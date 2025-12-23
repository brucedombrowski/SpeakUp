#!/bin/bash
#
# Space Link Simulator
#
# Applies network conditions to simulate space communication links
# using Linux tc (traffic control) with netem (network emulator).
#
# Standards Reference:
#   - CCSDS 131.1-O-2: TM Synchronization and Channel Coding
#   - Typical Mars link: 3-22 minute one-way delay, variable loss
#
# Usage:
#   ./simulate-space-link.sh <link-type>
#
# Link types:
#   leo       - Low Earth Orbit (~50ms delay, 0.1% loss)
#   geo       - Geostationary (~600ms delay, 0.5% loss)
#   lunar     - Earth-Moon (~1.3s delay, 1% loss)
#   mars-min  - Mars at closest approach (~3min delay, 2% loss)
#   mars-max  - Mars at opposition (~22min delay, 5% loss)
#   custom    - Custom parameters via environment variables
#

set -e

LINK_TYPE="${1:-leo}"

# Default custom parameters
CUSTOM_DELAY="${CUSTOM_DELAY:-100ms}"
CUSTOM_LOSS="${CUSTOM_LOSS:-0%}"
CUSTOM_JITTER="${CUSTOM_JITTER:-10ms}"

echo "Space Link Simulator"
echo "===================="
echo ""

case "$LINK_TYPE" in
    leo)
        DELAY="50ms"
        JITTER="5ms"
        LOSS="0.1%"
        DESC="Low Earth Orbit (ISS, ~400km)"
        ;;
    geo)
        DELAY="600ms"
        JITTER="10ms"
        LOSS="0.5%"
        DESC="Geostationary Orbit (~36,000km)"
        ;;
    lunar)
        DELAY="1300ms"
        JITTER="50ms"
        LOSS="1%"
        DESC="Earth-Moon (~384,000km)"
        ;;
    mars-min)
        DELAY="180000ms"  # 3 minutes
        JITTER="1000ms"
        LOSS="2%"
        DESC="Mars Closest Approach (~55M km)"
        ;;
    mars-max)
        DELAY="1320000ms"  # 22 minutes
        JITTER="5000ms"
        LOSS="5%"
        DESC="Mars Opposition (~400M km)"
        ;;
    custom)
        DELAY="$CUSTOM_DELAY"
        JITTER="$CUSTOM_JITTER"
        LOSS="$CUSTOM_LOSS"
        DESC="Custom link parameters"
        ;;
    *)
        echo "Unknown link type: $LINK_TYPE"
        echo "Available: leo, geo, lunar, mars-min, mars-max, custom"
        exit 1
        ;;
esac

echo "Link Type: $LINK_TYPE"
echo "Description: $DESC"
echo ""
echo "Parameters:"
echo "  Delay:  $DELAY (one-way)"
echo "  Jitter: $JITTER"
echo "  Loss:   $LOSS"
echo ""

# Apply to Earth-Relay link
echo "Applying to Earth <-> Relay link..."
docker exec dtn-earth tc qdisc replace dev eth0 root netem \
    delay $DELAY $JITTER distribution normal \
    loss $LOSS 2>/dev/null || \
docker exec dtn-earth tc qdisc add dev eth0 root netem \
    delay $DELAY $JITTER distribution normal \
    loss $LOSS

# Apply to Relay-Mars link (deeper space = more delay)
if [ "$LINK_TYPE" = "mars-min" ] || [ "$LINK_TYPE" = "mars-max" ]; then
    echo "Applying to Relay <-> Mars link..."
    docker exec dtn-relay tc qdisc replace dev eth1 root netem \
        delay $DELAY $JITTER distribution normal \
        loss $LOSS 2>/dev/null || \
    docker exec dtn-relay tc qdisc add dev eth1 root netem \
        delay $DELAY $JITTER distribution normal \
        loss $LOSS
fi

echo ""
echo "Link simulation active."
echo "To remove: tc qdisc del dev eth0 root"
