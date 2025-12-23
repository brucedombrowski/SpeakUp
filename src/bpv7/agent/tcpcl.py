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
"""

import socket
import struct
import threading
import logging
from typing import Optional, Callable, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import IntEnum
from queue import Queue

from ..core.bundle import Bundle
from ..core.eid import EndpointID


# TCPCL v4 Magic Number: "dtn!"
TCPCL_MAGIC = b'dtn!'

# Protocol version
TCPCL_VERSION = 4


class TCPCLMessageType(IntEnum):
    """TCPCL v4 Message Types per RFC 9174."""
    XFER_SEGMENT = 0x01     # Bundle data segment
    XFER_ACK = 0x02         # Transfer acknowledgment
    XFER_REFUSE = 0x03      # Transfer refusal
    KEEPALIVE = 0x04        # Session keepalive
    SESS_TERM = 0x05        # Session termination
    MSG_REJECT = 0x06       # Message rejection
    SESS_INIT = 0x07        # Session initialization


class XferSegmentFlags(IntEnum):
    """Transfer segment flags."""
    END = 0x01      # End of bundle
    START = 0x02    # Start of bundle


class SessionTermReason(IntEnum):
    """Session termination reasons."""
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

    Exchanged at session establishment.
    """
    flags: int = 0
    keepalive_interval: int = 30  # seconds

    def encode(self) -> bytes:
        """Encode contact header for transmission."""
        return (
            TCPCL_MAGIC +
            struct.pack('!B', TCPCL_VERSION) +
            struct.pack('!B', self.flags) +
            struct.pack('!H', self.keepalive_interval)
        )

    @classmethod
    def decode(cls, data: bytes) -> 'ContactHeader':
        """Decode contact header from received data."""
        if len(data) < 8:
            raise ValueError("Contact header too short")

        magic = data[0:4]
        if magic != TCPCL_MAGIC:
            raise ValueError(f"Invalid magic: {magic}")

        version = data[4]
        if version != TCPCL_VERSION:
            raise ValueError(f"Unsupported version: {version}")

        flags = data[5]
        keepalive = struct.unpack('!H', data[6:8])[0]

        return cls(flags=flags, keepalive_interval=keepalive)


@dataclass
class SessionInit:
    """
    TCPCL v4 Session Initialization Message per RFC 9174 Section 4.2.

    Carries node EID and session parameters.
    """
    keepalive_interval: int = 30
    segment_mru: int = 65535  # Max receive unit for segments
    transfer_mru: int = 0xFFFFFFFF  # Max bundle size
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
            node_bytes
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
        on_bundle_received: Optional[Callable[[Bundle], None]] = None,
    ):
        self.sock = sock
        self.local_eid = local_eid
        self.remote_eid: Optional[EndpointID] = None
        self.on_bundle_received = on_bundle_received

        self._running = False
        self._recv_thread: Optional[threading.Thread] = None
        self._transfer_id = 0
        self._pending_transfers: Dict[int, bytearray] = {}

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
        except:
            pass

    def _exchange_contact_headers(self) -> None:
        """Exchange contact headers with peer."""
        # Send our contact header
        header = ContactHeader()
        self.sock.sendall(header.encode())

        # Receive peer's contact header
        data = self.sock.recv(8)
        peer_header = ContactHeader.decode(data)
        self.logger.info(f"Peer keepalive: {peer_header.keepalive_interval}s")

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

    def _recv_message(self) -> bytes:
        """Receive a complete TCPCL message."""
        # First byte is message type
        msg_type_byte = self.sock.recv(1)
        if not msg_type_byte:
            raise ConnectionError("Connection closed")

        msg_type = msg_type_byte[0]

        if msg_type == TCPCLMessageType.SESS_INIT:
            # Session init has variable length
            header = self.sock.recv(20)
            node_len = struct.unpack('!H', header[18:20])[0]
            node_data = self.sock.recv(node_len)
            return msg_type_byte + header + node_data

        elif msg_type == TCPCLMessageType.XFER_SEGMENT:
            # Transfer segment
            header = self.sock.recv(9)  # flags(1) + transfer_id(8)
            flags = header[0]
            # Read data length (varint)
            data_len = self._recv_varint()
            data = self.sock.recv(data_len)
            return msg_type_byte + header + data

        elif msg_type == TCPCLMessageType.XFER_ACK:
            return msg_type_byte + self.sock.recv(17)  # flags + tid + length

        elif msg_type == TCPCLMessageType.KEEPALIVE:
            return msg_type_byte

        elif msg_type == TCPCLMessageType.SESS_TERM:
            return msg_type_byte + self.sock.recv(2)

        else:
            raise ValueError(f"Unknown message type: {msg_type}")

    def _recv_varint(self) -> int:
        """Receive a variable-length integer."""
        # Simplified: assume 4-byte length
        data = self.sock.recv(4)
        return struct.unpack('!I', data)[0]

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
        segment_data = data[14:]  # Skip length prefix

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
        """Send a bundle over this connection."""
        self._transfer_id += 1
        transfer_id = self._transfer_id

        # Encode bundle
        bundle_data = bundle.encode()

        # Send as single segment (simplified - real impl would segment)
        flags = XferSegmentFlags.START | XferSegmentFlags.END
        msg = (
            struct.pack('!B', TCPCLMessageType.XFER_SEGMENT) +
            struct.pack('!B', flags) +
            struct.pack('!Q', transfer_id) +
            struct.pack('!I', len(bundle_data)) +
            bundle_data
        )

        self.sock.sendall(msg)
        self.logger.info(f"Sent bundle: {bundle.bundle_id}")

    def _send_xfer_ack(self, transfer_id: int, length: int) -> None:
        """Send transfer acknowledgment."""
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
        except:
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

        self._connections: Dict[str, TCPCLConnection] = {}
        self._server_sock: Optional[socket.socket] = None
        self._running = False
        self._accept_thread: Optional[threading.Thread] = None

        self._bundle_handlers: List[Callable[[Bundle], None]] = []

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

            except socket.timeout:
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
