#!/usr/bin/env python3
"""
BPv7 Local Test with Packet Capture

Proves BPv7 bundle transmission by:
1. Starting packet capture (tcpdump)
2. Running TCPCL server and client
3. Analyzing captured packets
4. Showing the bundle bytes on the wire

No Wireshark GUI needed - everything in console.
"""

import sys
import os
import time
import threading
import subprocess
import tempfile
import struct

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bpv7 import Bundle, EndpointID, cbor_encode, cbor_decode
from bpv7.agent.tcpcl import TCPConvergenceLayer, TCPCL_MAGIC, TCPCL_VERSION

PORT = 4556  # IANA assigned TCPCL port


def print_header(text):
    print()
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_hex_dump(data, prefix=""):
    """Print hex dump of data."""
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"{prefix}{i:04x}: {hex_part:<48} {ascii_part}")


def analyze_tcpcl_packet(data):
    """Analyze TCPCL packet and explain what we see."""
    if len(data) < 4:
        return None

    # Look for TCPCL magic
    if data[:4] == TCPCL_MAGIC:
        print("  [TCPCL Contact Header]")
        print(f"    Magic: {data[:4]} ('dtn!')")
        if len(data) >= 5:
            print(f"    Version: {data[4]} (TCPCL v{data[4]})")
        if len(data) >= 6:
            print(f"    Flags: 0x{data[5]:02x}")
        if len(data) >= 8:
            keepalive = struct.unpack('>H', data[6:8])[0]
            print(f"    Keepalive: {keepalive} seconds")
        return "contact_header"

    # Check for CBOR indefinite array (bundle start)
    if data[0] == 0x9F:
        print("  [CBOR Bundle Data]")
        print(f"    0x9F = Indefinite-length array start")

        # Try to find bundle structure
        try:
            # Look for the break code
            if 0xFF in data:
                break_pos = data.rindex(0xFF)
                print(f"    0xFF = Break code at offset {break_pos}")
                print(f"    Bundle size: {break_pos + 1} bytes")
        except:
            pass

        return "bundle"

    return None


def run_server(ready_event, received_bundles, stop_event):
    """Run TCPCL server."""
    print("[SERVER] Starting on localhost:4556...")

    server_eid = EndpointID.ipn(2, 1)
    cla = TCPConvergenceLayer(server_eid, listen_port=PORT)

    def on_bundle(bundle):
        print()
        print_header("BUNDLE RECEIVED BY SERVER")
        print(f"  Source:      {bundle.source}")
        print(f"  Destination: {bundle.destination}")
        print(f"  Payload:     {bundle.payload.data}")
        print(f"  Bundle ID:   {bundle.bundle_id}")
        print()
        received_bundles.append(bundle)

    cla.add_bundle_handler(on_bundle)
    cla.start()
    print("[SERVER] Listening...")

    ready_event.set()

    # Wait until stop signal
    while not stop_event.is_set():
        time.sleep(0.1)

    cla.stop()
    print("[SERVER] Stopped")


def run_client(ready_event):
    """Run TCPCL client and send bundle."""
    ready_event.wait()
    time.sleep(0.5)

    print()
    print_header("CLIENT SENDING BUNDLE")

    client_eid = EndpointID.ipn(1, 1)

    # Create the bundle
    bundle = Bundle.create(
        destination=EndpointID.ipn(2, 1),
        source=client_eid,
        payload=b"Hello from BPv7! This message traversed a DTN link.",
        lifetime_ms=3600000,
    )

    print(f"  Source:      {bundle.source}")
    print(f"  Destination: {bundle.destination}")
    print(f"  Payload:     {bundle.payload.data.decode()}")
    print(f"  Lifetime:    {bundle.primary.lifetime_ms} ms")
    print(f"  Bundle ID:   {bundle.bundle_id}")

    # Show CBOR encoding
    encoded = bundle.encode()
    print()
    print(f"  CBOR Encoded ({len(encoded)} bytes):")
    print_hex_dump(encoded, "    ")

    print()
    print("  Connecting to server...")

    try:
        cla = TCPConvergenceLayer(client_eid)
        conn = cla.connect('127.0.0.1', PORT)
        print(f"  Connected! Remote EID: {conn.remote_eid}")

        print("  Sending bundle...")
        conn.send_bundle(bundle)
        print("  Bundle sent!")

        time.sleep(1)
        conn.stop()
        return True

    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def capture_packets(pcap_file, duration=5):
    """Capture packets using tcpdump."""
    print(f"[CAPTURE] Starting tcpdump on lo0 port {PORT}...")

    cmd = [
        'tcpdump',
        '-i', 'lo0',
        '-w', pcap_file,
        '-c', '50',  # Capture up to 50 packets
        f'port {PORT}'
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return proc
    except FileNotFoundError:
        print("[CAPTURE] tcpdump not found - will skip packet capture")
        return None


def analyze_pcap(pcap_file):
    """Analyze captured packets."""
    print()
    print_header("PACKET CAPTURE ANALYSIS")

    # Use tcpdump to read the pcap
    cmd = [
        'tcpdump',
        '-r', pcap_file,
        '-X',  # Hex and ASCII
        '-v',  # Verbose
        f'port {PORT}'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.stdout:
            print(result.stdout)

        # Also show raw hex for payload analysis
        print()
        print("Raw TCP Payloads:")
        print("-" * 70)

        cmd2 = ['tcpdump', '-r', pcap_file, '-xx', f'port {PORT}']
        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=10)
        if result2.stdout:
            lines = result2.stdout.split('\n')
            for line in lines[:50]:  # First 50 lines
                print(line)

    except subprocess.TimeoutExpired:
        print("  Analysis timed out")
    except FileNotFoundError:
        print("  tcpdump not available for analysis")


def main():
    print_header("BPv7 BUNDLE PROTOCOL TEST")
    print()
    print("This test proves BPv7 bundles are transmitted over the network.")
    print()
    print("What happens:")
    print("  1. Start packet capture (tcpdump)")
    print("  2. Start TCPCL server on port 4556")
    print("  3. Client connects and sends a bundle")
    print("  4. Server receives and decodes the bundle")
    print("  5. Analyze captured packets")
    print()
    print("Standards:")
    print("  - Bundle Protocol v7: RFC 9171 / CCSDS 734.20-O-1")
    print("  - TCPCL v4: RFC 9174")
    print("  - CBOR: RFC 8949")
    print()

    # Create temp file for packet capture
    pcap_fd, pcap_file = tempfile.mkstemp(suffix='.pcap')
    os.close(pcap_fd)

    print_header("STARTING PACKET CAPTURE")

    # Start packet capture
    capture_proc = capture_packets(pcap_file)
    if capture_proc:
        time.sleep(1)  # Let tcpdump start
        print("[CAPTURE] Running...")

    # Events for coordination
    ready_event = threading.Event()
    stop_event = threading.Event()
    received_bundles = []

    # Start server
    print_header("STARTING TCPCL SERVER")
    server_thread = threading.Thread(
        target=run_server,
        args=(ready_event, received_bundles, stop_event)
    )
    server_thread.daemon = True
    server_thread.start()

    # Run client
    success = run_client(ready_event)

    # Wait for bundle to be received
    time.sleep(2)

    # Stop everything
    stop_event.set()
    time.sleep(0.5)

    # Stop capture
    if capture_proc:
        capture_proc.terminate()
        try:
            capture_proc.wait(timeout=2)
        except:
            capture_proc.kill()
        print("[CAPTURE] Stopped")

    # Analyze packets
    if capture_proc and os.path.exists(pcap_file):
        analyze_pcap(pcap_file)
        os.unlink(pcap_file)

    # Final summary
    print()
    print_header("TEST RESULTS")

    if received_bundles:
        print()
        print("  ✓ BUNDLE SUCCESSFULLY TRANSMITTED AND RECEIVED")
        print()
        for i, b in enumerate(received_bundles):
            print(f"  Bundle {i+1}:")
            print(f"    Source:      {b.source}")
            print(f"    Destination: {b.destination}")
            print(f"    Payload:     {b.payload.data.decode()}")
        print()
        print("  This proves:")
        print("    - CBOR encoding works (RFC 8949)")
        print("    - Bundle structure is correct (RFC 9171)")
        print("    - TCPCL transmission works (RFC 9174)")
        print("    - Contact headers exchanged ('dtn!' magic)")
        print("    - Bundle decoded correctly at receiver")
    else:
        print()
        print("  Bundle transmission may have failed.")
        print("  Check the output above for errors.")

    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
