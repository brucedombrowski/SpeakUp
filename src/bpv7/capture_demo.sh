#!/bin/bash
#
# BPv7 Wireshark Capture Demo
#
# Captures BPv7/TCPCL traffic and opens in Wireshark for inspection.
#
# Usage: ./capture_demo.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CAPTURE_FILE="$HOME/Downloads/bpv7_demo_$(date +%Y%m%d_%H%M%S).pcap"

echo "========================================================"
echo "BPv7 Wireshark Capture Demo"
echo "========================================================"
echo ""
echo "This script will:"
echo "  1. Start packet capture on loopback (lo0)"
echo "  2. Run the BPv7 PDF transfer test"
echo "  3. Open the capture in Wireshark"
echo ""
echo "Capture file: $CAPTURE_FILE"
echo ""

# Check for tcpdump
if ! command -v tcpdump &> /dev/null; then
    echo "ERROR: tcpdump not found"
    exit 1
fi

# Start capture
echo "[1/3] Starting packet capture..."
tcpdump -i lo0 -w "$CAPTURE_FILE" port 4556 2>/dev/null &
TCPDUMP_PID=$!
sleep 1

# Run test
echo "[2/3] Running BPv7 PDF transfer test..."
echo ""
cd "$REPO_ROOT"
PYTHONPATH=src python3 src/bpv7/test_pdf_transfer.py 2>&1

# Stop capture
sleep 1
kill $TCPDUMP_PID 2>/dev/null || true
wait $TCPDUMP_PID 2>/dev/null || true

echo ""
echo "[3/3] Opening capture in Wireshark..."
echo ""

# Show packet summary
echo "Captured packets:"
tshark -r "$CAPTURE_FILE" 2>/dev/null | head -10
echo "..."
echo ""

# Open in Wireshark
if command -v open &> /dev/null; then
    open "$CAPTURE_FILE"
elif command -v wireshark &> /dev/null; then
    wireshark "$CAPTURE_FILE" &
else
    echo "Wireshark not found. Open manually: $CAPTURE_FILE"
fi

echo "========================================================"
echo "In Wireshark:"
echo "  1. Decode As... → TCP port 4556 → TCPCL"
echo "  2. Filter: tcpcl or bpv7"
echo "========================================================"
echo ""
echo "Capture saved: $CAPTURE_FILE"
