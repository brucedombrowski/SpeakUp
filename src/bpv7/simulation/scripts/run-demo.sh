#!/bin/bash
#
# BPv7 Mars Relay Network Demonstration
#
# Demonstrates end-to-end bundle transfer:
#   Earth (Node 1) -> Relay Satellite (Node 2) -> Mars Lander (Node 3)
#
# Supports two BPv7 implementations:
#   1. NASA JPL ION-DTN (open source reference implementation)
#   2. SpeakUp Clean-Room Python implementation
#
# Standards: CCSDS 734.20-O-1 / RFC 9171
#
# Usage:
#   ./run-demo.sh ion        # Use NASA JPL ION-DTN
#   ./run-demo.sh python     # Use SpeakUp Python implementation
#   ./run-demo.sh interop    # Test interoperability (Python <-> ION)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIM_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
IMPLEMENTATION="${1:-ion}"

echo "============================================================"
echo "BPv7 Mars Relay Network Demonstration"
echo "============================================================"
echo ""
echo "Network Topology:"
echo "  Earth (ipn:1.x) <--600s--> Relay (ipn:2.x) <--local--> Mars (ipn:3.x)"
echo ""
echo "Standards: CCSDS 734.20-O-1 / RFC 9171"
echo ""

case "$IMPLEMENTATION" in
    ion)
        echo "Implementation: NASA JPL ION-DTN (Open Source)"
        echo "Source: https://github.com/nasa-jpl/ION-DTN"
        ;;
    python)
        echo "Implementation: SpeakUp Clean-Room Python"
        echo "Source: Local (src/bpv7)"
        ;;
    interop)
        echo "Implementation: Interoperability Test"
        echo "  Earth: SpeakUp Python"
        echo "  Relay: NASA JPL ION-DTN"
        echo "  Mars:  NASA JPL ION-DTN"
        ;;
    *)
        echo "Unknown implementation: $IMPLEMENTATION"
        echo "Usage: $0 [ion|python|interop]"
        exit 1
        ;;
esac

echo ""
echo "============================================================"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found. Please install Docker."
    exit 1
fi

# Select compose file based on implementation
case "$IMPLEMENTATION" in
    ion)
        COMPOSE_FILE="docker-compose.yml"
        ;;
    python)
        COMPOSE_FILE="docker-compose-python.yml"
        ;;
    interop)
        COMPOSE_FILE="docker-compose-interop.yml"
        ;;
esac

# Start the network
echo "Starting DTN network with $IMPLEMENTATION implementation..."
cd "$SIM_DIR"

if [ -f "$COMPOSE_FILE" ]; then
    docker-compose -f "$COMPOSE_FILE" up -d --build
else
    echo "Using default docker-compose.yml"
    docker-compose up -d --build
fi

echo ""
echo "Waiting for nodes to initialize..."
sleep 10

# Start BPv7 agents based on implementation
case "$IMPLEMENTATION" in
    ion)
        echo ""
        echo "Starting ION on all nodes..."
        docker exec dtn-earth bash -c "cd /dtn && ionstart -I config/ion.rc" 2>/dev/null || true
        docker exec dtn-relay bash -c "cd /dtn && ionstart -I config/ion.rc" 2>/dev/null || true
        docker exec dtn-mars bash -c "cd /dtn && ionstart -I config/ion.rc" 2>/dev/null || true
        ;;
    python)
        echo ""
        echo "Starting Python BPA on all nodes..."
        docker exec dtn-earth bash -c "python3 -m bpv7.agent.bpa --node 1 --config /dtn/config &" 2>/dev/null || true
        docker exec dtn-relay bash -c "python3 -m bpv7.agent.bpa --node 2 --config /dtn/config &" 2>/dev/null || true
        docker exec dtn-mars bash -c "python3 -m bpv7.agent.bpa --node 3 --config /dtn/config &" 2>/dev/null || true
        ;;
    interop)
        echo ""
        echo "Starting mixed implementation nodes..."
        echo "  Earth: Python BPA"
        docker exec dtn-earth bash -c "python3 -m bpv7.agent.bpa --node 1 --config /dtn/config &" 2>/dev/null || true
        echo "  Relay: ION"
        docker exec dtn-relay bash -c "cd /dtn && ionstart -I config/ion.rc" 2>/dev/null || true
        echo "  Mars: ION"
        docker exec dtn-mars bash -c "cd /dtn && ionstart -I config/ion.rc" 2>/dev/null || true
        ;;
esac

sleep 5

echo ""
echo "============================================================"
echo "Sending test bundle: Earth -> Mars"
echo "============================================================"
echo ""

# Create test payload
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TEST_MSG="Hello Mars! Implementation: $IMPLEMENTATION. Timestamp: $TIMESTAMP"
echo "Payload: $TEST_MSG"
echo ""

# Send bundle based on implementation
case "$IMPLEMENTATION" in
    ion)
        echo "Sending bundle via ION bpsource..."
        docker exec dtn-earth bash -c "echo '$TEST_MSG' | bpsource ipn:3.1" 2>/dev/null || echo "  (bpsource not available)"
        ;;
    python|interop)
        echo "Sending bundle via Python BPA..."
        docker exec dtn-earth bash -c "python3 -c \"
from bpv7 import Bundle, EndpointID
from bpv7.agent import TCPConvergenceLayer

# Create bundle
bundle = Bundle.create(
    destination=EndpointID.ipn(3, 1),
    source=EndpointID.ipn(1, 1),
    payload=b'$TEST_MSG',
)

# Send via TCPCL
cla = TCPConvergenceLayer(EndpointID.ipn(1, 1))
conn = cla.connect('10.1.1.20', 4556)
conn.send_bundle(bundle)
print(f'Sent bundle: {bundle.bundle_id}')
\"" 2>/dev/null || echo "  (Python send failed - check logs)"
        ;;
esac

echo ""
echo "Bundle injected into DTN."
echo "With 600-second simulated light time, real delivery would be delayed."
echo ""

echo "============================================================"
echo "Network Status"
echo "============================================================"
echo ""

case "$IMPLEMENTATION" in
    ion)
        echo "Earth node (ION):"
        docker exec dtn-earth bash -c "bpstats" 2>/dev/null || echo "  (stats unavailable)"
        echo ""
        echo "Relay node (ION):"
        docker exec dtn-relay bash -c "bpstats" 2>/dev/null || echo "  (stats unavailable)"
        echo ""
        echo "Mars node (ION):"
        docker exec dtn-mars bash -c "bpstats" 2>/dev/null || echo "  (stats unavailable)"
        ;;
    python)
        echo "Earth node (Python):"
        docker exec dtn-earth bash -c "python3 -c 'from bpv7.agent import status; status()'" 2>/dev/null || echo "  (stats unavailable)"
        echo ""
        echo "Relay node (Python):"
        docker exec dtn-relay bash -c "python3 -c 'from bpv7.agent import status; status()'" 2>/dev/null || echo "  (stats unavailable)"
        echo ""
        echo "Mars node (Python):"
        docker exec dtn-mars bash -c "python3 -c 'from bpv7.agent import status; status()'" 2>/dev/null || echo "  (stats unavailable)"
        ;;
    interop)
        echo "Earth node (Python):"
        docker exec dtn-earth bash -c "python3 -c 'from bpv7.agent import status; status()'" 2>/dev/null || echo "  (stats unavailable)"
        echo ""
        echo "Relay node (ION):"
        docker exec dtn-relay bash -c "bpstats" 2>/dev/null || echo "  (stats unavailable)"
        echo ""
        echo "Mars node (ION):"
        docker exec dtn-mars bash -c "bpstats" 2>/dev/null || echo "  (stats unavailable)"
        ;;
esac

echo ""
echo "============================================================"
echo "Demonstration Complete"
echo "============================================================"
echo ""
echo "To interact with nodes:"
echo "  docker exec -it dtn-earth bash"
echo "  docker exec -it dtn-relay bash"
echo "  docker exec -it dtn-mars bash"
echo ""
echo "To stop the network:"
echo "  docker-compose down"
echo ""
echo "To apply space link delay simulation:"
echo "  ./scripts/simulate-space-link.sh mars-min"
echo ""
echo "To switch implementations:"
echo "  ./scripts/run-demo.sh ion       # NASA JPL ION-DTN"
echo "  ./scripts/run-demo.sh python    # SpeakUp Python"
echo "  ./scripts/run-demo.sh interop   # Interoperability test"
echo ""
