#!/usr/bin/env python3
"""
BPv7 PDF Transfer Test

Sends the SpeakUp briefing PDF via Bundle Protocol to prove
real file transfer over DTN links.

This is a meaningful test: the actual project deliverable
is transmitted using the protocol we implemented.
"""

import sys
import os
import time
import threading
import hashlib

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bpv7 import Bundle, EndpointID
from bpv7.agent.tcpcl import TCPConvergenceLayer

PORT = 4556
PDF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'briefing', 'SpeakUp-Briefing.pdf'
)


def print_header(text):
    print()
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)


def run_server(ready_event, received_bundles, stop_event):
    """Run TCPCL server that receives the PDF."""
    print("[SERVER] Starting on localhost:4556...")

    server_eid = EndpointID.ipn(2, 1)  # Mars relay
    cla = TCPConvergenceLayer(server_eid, listen_port=PORT)

    def on_bundle(bundle):
        print()
        print_header("BUNDLE RECEIVED")
        print(f"  Source:      {bundle.source}")
        print(f"  Destination: {bundle.destination}")
        print(f"  Payload:     {len(bundle.payload.data)} bytes")

        # Verify it's PDF data
        if bundle.payload.data[:4] == b'%PDF':
            print(f"  Content:     PDF document detected")

            # Calculate hash for verification
            md5 = hashlib.md5(bundle.payload.data).hexdigest()
            print(f"  MD5:         {md5}")

            # Save received PDF
            received_path = '/tmp/received_briefing.pdf'
            with open(received_path, 'wb') as f:
                f.write(bundle.payload.data)
            print(f"  Saved to:    {received_path}")
        else:
            print(f"  Content:     (first 50 bytes) {bundle.payload.data[:50]}")

        received_bundles.append(bundle)

    cla.add_bundle_handler(on_bundle)
    cla.start()
    print("[SERVER] Listening...")

    ready_event.set()

    while not stop_event.is_set():
        time.sleep(0.1)

    cla.stop()
    print("[SERVER] Stopped")


def run_client(ready_event, pdf_data, pdf_hash):
    """Send the PDF via bundle protocol."""
    ready_event.wait()
    time.sleep(0.5)

    print()
    print_header("CLIENT SENDING PDF")

    client_eid = EndpointID.ipn(1, 1)  # Earth ground station

    # Create bundle with PDF as payload
    bundle = Bundle.create(
        destination=EndpointID.ipn(2, 1),  # Mars relay
        source=client_eid,
        payload=pdf_data,
        lifetime_ms=86400000,  # 24 hours (realistic for Mars)
    )

    print(f"  Source:      {bundle.source} (Earth)")
    print(f"  Destination: {bundle.destination} (Mars Relay)")
    print(f"  Payload:     {len(pdf_data)} bytes")
    print(f"  Original MD5: {pdf_hash}")
    print(f"  Lifetime:    {bundle.primary.lifetime_ms} ms (24 hours)")
    print(f"  Bundle ID:   {bundle.bundle_id}")

    # Show encoding stats
    encoded = bundle.encode()
    print()
    print(f"  CBOR Encoded: {len(encoded)} bytes")
    print(f"  Overhead:     {len(encoded) - len(pdf_data)} bytes ({100*(len(encoded)-len(pdf_data))/len(pdf_data):.1f}%)")

    print()
    print("  Connecting to server...")

    try:
        cla = TCPConvergenceLayer(client_eid)
        conn = cla.connect('127.0.0.1', PORT)
        print(f"  Connected! Remote EID: {conn.remote_eid}")

        print("  Sending bundle (this is the PDF)...")
        conn.send_bundle(bundle)
        print("  Bundle sent!")

        time.sleep(2)
        conn.stop()
        return True

    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print_header("BPv7 PDF TRANSFER TEST")
    print()
    print("This test sends the SpeakUp briefing PDF via Bundle Protocol.")
    print("The actual project deliverable is transmitted using BPv7/TCPCL.")
    print()

    # Check if PDF exists
    if not os.path.exists(PDF_PATH):
        print(f"Error: PDF not found at {PDF_PATH}")
        print("Run 'cd briefing && ./build.sh' to generate it first.")
        sys.exit(1)

    # Load PDF
    with open(PDF_PATH, 'rb') as f:
        pdf_data = f.read()

    pdf_hash = hashlib.md5(pdf_data).hexdigest()

    print(f"PDF File:   {PDF_PATH}")
    print(f"Size:       {len(pdf_data):,} bytes")
    print(f"MD5:        {pdf_hash}")
    print()
    print("Protocol Stack:")
    print("  - Bundle Protocol v7 (RFC 9171 / CCSDS 734.20-O-1)")
    print("  - TCP Convergence Layer v4 (RFC 9174)")
    print("  - CBOR Encoding (RFC 8949)")

    # Events for coordination
    ready_event = threading.Event()
    stop_event = threading.Event()
    received_bundles = []

    # Start server
    print_header("STARTING RECEIVER (Mars Relay - ipn:2.1)")
    server_thread = threading.Thread(
        target=run_server,
        args=(ready_event, received_bundles, stop_event)
    )
    server_thread.daemon = True
    server_thread.start()

    # Run client
    success = run_client(ready_event, pdf_data, pdf_hash)

    # Wait for transfer
    time.sleep(3)

    # Stop
    stop_event.set()
    time.sleep(0.5)

    # Results
    print()
    print_header("TEST RESULTS")

    if received_bundles:
        received = received_bundles[0]
        received_hash = hashlib.md5(received.payload.data).hexdigest()

        print()
        if received_hash == pdf_hash:
            print("  SUCCESS: PDF transferred correctly via Bundle Protocol!")
            print()
            print("  Verification:")
            print(f"    Original size:  {len(pdf_data):,} bytes")
            print(f"    Received size:  {len(received.payload.data):,} bytes")
            print(f"    Original MD5:   {pdf_hash}")
            print(f"    Received MD5:   {received_hash}")
            print(f"    Match:          YES")
            print()
            print("  This proves:")
            print("    - Complete BPv7 bundle encoding/decoding works")
            print("    - TCPCL transmission is reliable")
            print("    - Real binary data (PDF) survives the protocol stack")
            print("    - The briefing document can traverse DTN links")
            print()
            print("  Received PDF saved to: /tmp/received_briefing.pdf")
            print("  Open it to verify: open /tmp/received_briefing.pdf")
        else:
            print("  FAILURE: MD5 mismatch - PDF corrupted in transfer")
            print(f"    Original: {pdf_hash}")
            print(f"    Received: {received_hash}")
    else:
        print()
        print("  FAILURE: No bundle received")
        print("  Check the output above for errors.")

    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
