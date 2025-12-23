"""
TCP Convergence Layer Adapter for Bundle Protocol Version 7

Implements TCPCL v4 per RFC 9174 for bundle transmission over TCP.

The TCP Convergence Layer provides reliable, in-order delivery of
bundles between adjacent DTN nodes. It handles:
- Session establishment with contact header exchange
- Bundle segmentation and reassembly
- Acknowledgment and flow control
- Session termination

Standards:
- RFC 9174: TCP Convergence Layer Protocol Version 4
- RFC 9171: Bundle Protocol Version 7

Wire Format (RFC 9174 compliant for Wireshark compatibility):
- Contact Header: 6 bytes (magic + version + flags)
- SESS_INIT: variable (msg_type + keepalive + MRUs + node_id + ext_len)
- XFER_SEGMENT: variable (msg_type + flags + transfer_id + [ext_len] + data_len + data)
- XFER_ACK: 18 bytes (msg_type + flags + transfer_id + ack_len)
"""

import logging
import socket
import struct
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum

from ..core.bundle import Bundle
from ..core.eid import EndpointID

# TCPCL v4 Magic Number: "dtn!"
TCPCL_MAGIC = b'dtn!'

# Protocol version
TCPCL_VERSION = 4


class TCPCLMessageType(IntEnum):
    """TCPCL v4 Message Types per RFC 9174 Section 4.2."""
    XFER_SEGMENT = 0x01     # Bundle data segment
    XFER_ACK = 0x02         # Transfer acknowledgment
    XFER_REFUSE = 0x03      # Transfer refusal
    KEEPALIVE = 0x04        # Session keepalive
    SESS_TERM = 0x05        # Session termination
    MSG_REJECT = 0x06       # Message rejection
    SESS_INIT = 0x07        # Session initialization


class XferSegmentFlags(IntEnum):
    """Transfer segment flags per RFC 9174 Section 5.2.2."""
    END = 0x01      # End of bundle
    START = 0x02    # Start of bundle


class SessionTermReason(IntEnum):
    """Session termination reasons per RFC 9174."""
    UNKNOWN = 0x00
    IDLE_TIMEOUT = 0x01
    VERSION_MISMATCH = 0x02
    BUSY = 0x03
    CONTACT_FAILURE = 0x04
    RESOURCE_EXHAUSTION = 0x05


@dataclass
class ContactHeader:
    """
    TCPCL v4 Contact Header per RFC 9174 Section 4.1.

    Wire format (6 bytes):
        magic: 4 bytes ('dtn!')
        version: 1 byte (0x04)
        flags: 1 byte (bit 0 = CAN_TLS)
    """
    flags: int = 0

    def encode(self) -> bytes:
        """Encode contact header for transmission."""
        return (
            TCPCL_MAGIC +
            struct.pack('!B', TCPCL_VERSION) +
            struct.pack('!B', self.flags)
        )

    @classmethod
    def decode(cls, data: bytes) -> 'ContactHeader':
        """Decode contact header from received data."""
        if len(data) < 6:
            raise ValueError("Contact header too short")

        magic = data[0:4]
        if magic != TCPCL_MAGIC:
            raise ValueError(f"Invalid magic: {magic}")

        version = data[4]
        if version != TCPCL_VERSION:
            raise ValueError(f"Unsupported version: {version}")

        flags = data[5]
        return cls(flags=flags)


@dataclass
class SessionInit:
    """
    TCPCL v4 Session Initialization Message per RFC 9174 Section 4.3.

    Wire format:
        msg_type: 1 byte (0x07)
        keepalive_interval: 2 bytes (uint16)
        segment_mru: 8 bytes (uint64)
        transfer_mru: 8 bytes (uint64)
        node_id_len: 2 bytes (uint16)
        node_id: variable (UTF-8 string)
        ext_items_len: 4 bytes (uint32)
        ext_items: variable (none for now)
    """
    keepalive_interval: int = 30
    segment_mru: int = 0xFFFFFFFFFFFFFFFF  # Max receive unit for segments
    transfer_mru: int = 0xFFFFFFFFFFFFFFFF  # Max bundle size
    node_id: str = ""  # Node EID as string

    def encode(self) -> bytes:
        """Encode session init message."""
        node_bytes = self.node_id.encode('utf-8')
        return (
            struct.pack('!B', TCPCLMessageType.SESS_INIT) +
            struct.pack('!H', self.keepalive_interval) +
            struct.pack('!Q', self.segment_mru) +
            struct.pack('!Q', self.transfer_mru) +
            struct.pack('!H', len(node_bytes)) +
            node_bytes +
            struct.pack('!I', 0)  # Extension items length = 0
        )

    @classmethod
    def decode(cls, data: bytes) -> 'SessionInit':
        """Decode session init message."""
        if data[0] != TCPCLMessageType.SESS_INIT:
            raise ValueError("Not a SESS_INIT message")

        keepalive = struct.unpack('!H', data[1:3])[0]
        segment_mru = struct.unpack('!Q', data[3:11])[0]
        transfer_mru = struct.unpack('!Q', data[11:19])[0]
        node_len = struct.unpack('!H', data[19:21])[0]
        node_id = data[21:21+node_len].decode('utf-8')
        # Extension items length at 21+node_len, we skip it

        return cls(
            keepalive_interval=keepalive,
            segment_mru=segment_mru,
            transfer_mru=transfer_mru,
            node_id=node_id,
        )


class TCPCLConnection:
    """
    TCPCL v4 Connection Handler.

    Manages a single TCP connection for bundle transfer.
    """

    def __init__(
        self,
        sock: socket.socket,
        local_eid: EndpointID,
        on_bundle_received: Callable[[Bundle], None] | None = None,
    ):
        self.sock = sock
        self.local_eid = local_eid
        self.remote_eid: EndpointID | None = None
        self.on_bundle_received = on_bundle_received

        self._running = False
        self._recv_thread: threading.Thread | None = None
        self._transfer_id = 0
        self._pending_transfers: dict[int, bytearray] = {}

        self.logger = logging.getLogger(f"tcpcl.{id(self)}")

    def start(self) -> None:
        """Start the connection handler."""
        self._running = True
        self._exchange_contact_headers()
        self._exchange_session_init()

        # Start receive thread
        self._recv_thread = threading.Thread(target=self._receive_loop)
        self._recv_thread.daemon = True
        self._recv_thread.start()

    def stop(self) -> None:
        """Stop the connection handler."""
        self._running = False
        self._send_session_term(SessionTermReason.UNKNOWN)
        try:
            self.sock.close()
        except Exception:
            pass

    def _exchange_contact_headers(self) -> None:
        """Exchange contact headers with peer."""
        # Send our contact header (6 bytes per RFC 9174)
        header = ContactHeader()
        self.sock.sendall(header.encode())

        # Receive peer's contact header (6 bytes)
        data = self._recv_exact(6)
        peer_header = ContactHeader.decode(data)
        self.logger.info(f"Peer contact flags: 0x{peer_header.flags:02x}")

    def _exchange_session_init(self) -> None:
        """Exchange session initialization messages."""
        # Send our session init
        init = SessionInit(node_id=str(self.local_eid))
        self.sock.sendall(init.encode())

        # Receive peer's session init
        data = self._recv_message()
        peer_init = SessionInit.decode(data)
        self.remote_eid = EndpointID.parse(peer_init.node_id)
        self.logger.info(f"Connected to peer: {self.remote_eid}")

    def _recv_exact(self, n: int) -> bytes:
        """Receive exactly n bytes from socket."""
        chunks = []
        remaining = n
        while remaining > 0:
            chunk = self.sock.recv(min(remaining, 65536))
            if not chunk:
                raise ConnectionError("Connection closed during receive")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b''.join(chunks)

    def _recv_message(self) -> bytes:
        """Receive a complete TCPCL message."""
        # First byte is message type
        msg_type_byte = self._recv_exact(1)
        if not msg_type_byte:
            raise ConnectionError("Connection closed")

        msg_type = msg_type_byte[0]

        if msg_type == TCPCLMessageType.SESS_INIT:
            # SESS_INIT: keepalive(2) + segment_mru(8) + transfer_mru(8) + node_len(2)
            header = self._recv_exact(20)
            node_len = struct.unpack('!H', header[18:20])[0]
            node_data = self._recv_exact(node_len)
            # Extension items length (4 bytes)
            ext_len_data = self._recv_exact(4)
            ext_len = struct.unpack('!I', ext_len_data)[0]
            ext_data = self._recv_exact(ext_len) if ext_len > 0 else b''
            return msg_type_byte + header + node_data + ext_len_data + ext_data

        elif msg_type == TCPCLMessageType.XFER_SEGMENT:
            # XFER_SEGMENT: flags(1) + transfer_id(8)
            header = self._recv_exact(9)
            flags = header[0]

            # If START flag, read extension items
            ext_data = b''
            if flags & XferSegmentFlags.START:
                ext_len_data = self._recv_exact(4)
                ext_len = struct.unpack('!I', ext_len_data)[0]
                ext_data = ext_len_data + (self._recv_exact(ext_len) if ext_len > 0 else b'')

            # Data length (8 bytes, uint64)
            data_len_bytes = self._recv_exact(8)
            data_len = struct.unpack('!Q', data_len_bytes)[0]

            # Bundle data
            data = self._recv_exact(data_len)

            return msg_type_byte + header + ext_data + data_len_bytes + data

        elif msg_type == TCPCLMessageType.XFER_ACK:
            # XFER_ACK: flags(1) + transfer_id(8) + ack_len(8)
            return msg_type_byte + self._recv_exact(17)

        elif msg_type == TCPCLMessageType.KEEPALIVE:
            return msg_type_byte

        elif msg_type == TCPCLMessageType.SESS_TERM:
            # SESS_TERM: flags(1) + reason(1)
            return msg_type_byte + self._recv_exact(2)

        else:
            raise ValueError(f"Unknown message type: {msg_type}")

    def _receive_loop(self) -> None:
        """Main receive loop."""
        while self._running:
            try:
                data = self._recv_message()
                self._handle_message(data)
            except ConnectionError:
                self.logger.info("Connection closed by peer")
                break
            except Exception as e:
                self.logger.error(f"Receive error: {e}")
                break

        self._running = False

    def _handle_message(self, data: bytes) -> None:
        """Handle a received TCPCL message."""
        msg_type = data[0]

        if msg_type == TCPCLMessageType.XFER_SEGMENT:
            self._handle_xfer_segment(data)
        elif msg_type == TCPCLMessageType.XFER_ACK:
            self.logger.debug("Received transfer ACK")
        elif msg_type == TCPCLMessageType.KEEPALIVE:
            self.logger.debug("Received keepalive")
        elif msg_type == TCPCLMessageType.SESS_TERM:
            self.logger.info("Received session termination")
            self._running = False

    def _handle_xfer_segment(self, data: bytes) -> None:
        """Handle a transfer segment message."""
        flags = data[1]
        transfer_id = struct.unpack('!Q', data[2:10])[0]

        # Calculate offset to bundle data
        offset = 10
        if flags & XferSegmentFlags.START:
            # Skip extension items length (4 bytes) + any extensions
            ext_len = struct.unpack('!I', data[10:14])[0]
            offset = 14 + ext_len

        # Skip data length field (8 bytes) - we already read the data
        offset += 8

        segment_data = data[offset:]

        # Initialize buffer for new transfer
        if flags & XferSegmentFlags.START:
            self._pending_transfers[transfer_id] = bytearray()

        # Append data
        if transfer_id in self._pending_transfers:
            self._pending_transfers[transfer_id].extend(segment_data)

        # Complete transfer
        if flags & XferSegmentFlags.END:
            bundle_data = bytes(self._pending_transfers.pop(transfer_id))
            self._send_xfer_ack(transfer_id, len(bundle_data))

            # Decode and deliver bundle
            try:
                bundle = Bundle.decode(bundle_data)
                self.logger.info(f"Received bundle: {bundle.bundle_id}")
                if self.on_bundle_received:
                    self.on_bundle_received(bundle)
            except Exception as e:
                self.logger.error(f"Failed to decode bundle: {e}")

    def send_bundle(self, bundle: Bundle) -> None:
        """
        Send a bundle over this connection.

        Wire format per RFC 9174 Section 5.2.2:
            msg_type: 1 byte (0x01)
            flags: 1 byte (START=0x02, END=0x01)
            transfer_id: 8 bytes (uint64)
            ext_items_len: 4 bytes (uint32) - only if START flag
            data_len: 8 bytes (uint64)
            data: variable
        """
        self._transfer_id += 1
        transfer_id = self._transfer_id

        # Encode bundle
        bundle_data = bundle.encode()

        # Send as single segment (START + END flags)
        flags = XferSegmentFlags.START | XferSegmentFlags.END
        msg = (
            struct.pack('!B', TCPCLMessageType.XFER_SEGMENT) +
            struct.pack('!B', flags) +
            struct.pack('!Q', transfer_id) +
            struct.pack('!I', 0) +  # Extension items length = 0 (required when START)
            struct.pack('!Q', len(bundle_data)) +  # 8-byte length per RFC 9174
            bundle_data
        )

        self.sock.sendall(msg)
        self.logger.info(f"Sent bundle: {bundle.bundle_id}")

    def _send_xfer_ack(self, transfer_id: int, length: int) -> None:
        """
        Send transfer acknowledgment.

        Wire format per RFC 9174:
            msg_type: 1 byte (0x02)
            flags: 1 byte
            transfer_id: 8 bytes (uint64)
            ack_len: 8 bytes (uint64)
        """
        msg = (
            struct.pack('!B', TCPCLMessageType.XFER_ACK) +
            struct.pack('!B', 0) +  # flags
            struct.pack('!Q', transfer_id) +
            struct.pack('!Q', length)
        )
        self.sock.sendall(msg)

    def _send_session_term(self, reason: SessionTermReason) -> None:
        """Send session termination message."""
        msg = (
            struct.pack('!B', TCPCLMessageType.SESS_TERM) +
            struct.pack('!B', 0) +  # flags
            struct.pack('!B', reason)
        )
        try:
            self.sock.sendall(msg)
        except Exception:
            pass


class TCPConvergenceLayer:
    """
    TCP Convergence Layer Adapter.

    Manages TCPCL connections and bundle routing.
    """

    def __init__(
        self,
        local_eid: EndpointID,
        listen_port: int = 4556,  # IANA assigned TCPCL port
    ):
        self.local_eid = local_eid
        self.listen_port = listen_port

        self._connections: dict[str, TCPCLConnection] = {}
        self._server_sock: socket.socket | None = None
        self._running = False
        self._accept_thread: threading.Thread | None = None

        self._bundle_handlers: list[Callable[[Bundle], None]] = []

        self.logger = logging.getLogger("tcpcl")

    def add_bundle_handler(self, handler: Callable[[Bundle], None]) -> None:
        """Register a handler for received bundles."""
        self._bundle_handlers.append(handler)

    def start(self) -> None:
        """Start the convergence layer."""
        self._running = True

        # Start listening server
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind(('0.0.0.0', self.listen_port))
        self._server_sock.listen(5)

        self._accept_thread = threading.Thread(target=self._accept_loop)
        self._accept_thread.daemon = True
        self._accept_thread.start()

        self.logger.info(f"TCPCL listening on port {self.listen_port}")

    def stop(self) -> None:
        """Stop the convergence layer."""
        self._running = False

        # Close all connections
        for conn in self._connections.values():
            conn.stop()

        # Close server socket
        if self._server_sock:
            self._server_sock.close()

    def _accept_loop(self) -> None:
        """Accept incoming connections."""
        while self._running:
            try:
                self._server_sock.settimeout(1.0)
                client_sock, addr = self._server_sock.accept()
                self.logger.info(f"Accepted connection from {addr}")

                conn = TCPCLConnection(
                    sock=client_sock,
                    local_eid=self.local_eid,
                    on_bundle_received=self._on_bundle_received,
                )
                conn.start()

            except TimeoutError:
                continue
            except Exception as e:
                if self._running:
                    self.logger.error(f"Accept error: {e}")

    def connect(self, host: str, port: int = 4556) -> TCPCLConnection:
        """Establish outgoing connection to a peer."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        conn = TCPCLConnection(
            sock=sock,
            local_eid=self.local_eid,
            on_bundle_received=self._on_bundle_received,
        )
        conn.start()

        # Store connection by peer EID
        if conn.remote_eid:
            self._connections[str(conn.remote_eid)] = conn

        return conn

    def send_bundle(self, bundle: Bundle) -> bool:
        """
        Send a bundle to its destination.

        Returns True if sent, False if no route.
        """
        dest = str(bundle.destination)

        # Find connection to destination (or next hop)
        conn = self._connections.get(dest)
        if conn:
            conn.send_bundle(bundle)
            return True

        self.logger.warning(f"No route to {dest}")
        return False

    def _on_bundle_received(self, bundle: Bundle) -> None:
        """Handle received bundle."""
        for handler in self._bundle_handlers:
            try:
                handler(bundle)
            except Exception as e:
                self.logger.error(f"Bundle handler error: {e}")
