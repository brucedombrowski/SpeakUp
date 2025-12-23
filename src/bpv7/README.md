# Bundle Protocol Version 7 Implementation

## Standards Reference

This implementation conforms to:

- **CCSDS 734.20-O-1** - CCSDS Bundle Protocol Version 7 Specification (Orange Book)
- **RFC 9171** - Bundle Protocol Version 7
- **RFC 9174** - TCP Convergence Layer Protocol Version 4
- **RFC 8949** - Concise Binary Object Representation (CBOR)
- **RFC 9172** - Bundle Protocol Security (BPSec) - Optional

## Architecture

```
src/bpv7/
├── __init__.py         # Package exports
├── example.py          # Usage demonstration
├── core/               # Core bundle structures and types
│   ├── bundle.py       # Bundle container and operations
│   ├── eid.py          # Endpoint Identifier handling (dtn:, ipn:)
│   └── time.py         # DTN time and timestamps
├── blocks/             # Block type implementations
│   ├── primary.py      # Primary block (block 0)
│   └── payload.py      # Payload block (block 1) + extensions
├── encoding/           # CBOR encoding/decoding
│   ├── cbor.py         # CBOR primitives (RFC 8949)
│   └── crc.py          # CRC-16 X.25 and CRC-32C
├── agent/              # Bundle Protocol Agent
│   └── tcpcl.py        # TCP Convergence Layer (RFC 9174)
├── simulation/         # Test environment
│   ├── Dockerfile      # Container with ION + Python
│   ├── docker-compose.yml
│   ├── EXPORT_CONTROL.md
│   ├── config/         # ION configuration files
│   │   ├── earth/
│   │   ├── relay/
│   │   └── mars/
│   ├── contact_plans/  # AOS/LOS schedules
│   │   ├── scenario_leo.txt
│   │   ├── scenario_lunar.txt
│   │   ├── scenario_mars.txt
│   │   └── scenario_voyager.txt
│   └── scripts/
│       ├── run-demo.sh
│       └── simulate-space-link.sh
└── tests/              # Protocol compliance tests
    ├── test_cbor.py
    ├── test_crc.py
    ├── test_eid.py
    └── test_bundle.py
```

## Implementation Status

| Component | Status | RFC Reference |
|-----------|--------|---------------|
| Bundle Structure | Complete | RFC 9171 §4.2 |
| Primary Block | Complete | RFC 9171 §4.3.1 |
| Payload Block | Complete | RFC 9171 §4.3.2 |
| Extension Blocks | Complete | RFC 9171 §4.4 |
| CBOR Encoding | Complete | RFC 8949 |
| CRC Calculation | Complete | RFC 9171 §4.2.1 |
| Endpoint IDs | Complete | RFC 9171 §4.2.5 |
| DTN Time | Complete | RFC 9171 §4.2.6 |
| TCP Convergence Layer | Complete | RFC 9174 |
| Contact Plans | Complete | CGR Reference |
| Space Link Simulation | Complete | --- |
| BPA Services | Partial | RFC 9171 §3.3 |

## Quick Start

```python
from bpv7 import Bundle, EndpointID

# Create a bundle
bundle = Bundle.create(
    destination=EndpointID.ipn(2, 1),
    source=EndpointID.ipn(1, 1),
    payload=b"Hello, DTN!",
    lifetime_ms=3600000,  # 1 hour
)

# Encode to CBOR
encoded = bundle.encode()

# Decode from CBOR
decoded = Bundle.decode(encoded)
```

## Simulation Environment

Three implementation options, selectable at runtime:

| Option | Command | Description |
|--------|---------|-------------|
| NASA JPL ION-DTN | `./run-demo.sh ion` | Open source reference (default) |
| SpeakUp Python | `./run-demo.sh python` | Clean-room implementation |
| Interoperability | `./run-demo.sh interop` | Mixed (validates compliance) |

### Contact Plan Scenarios

| Scenario | Distance | Delay | Key Constraint |
|----------|----------|-------|----------------|
| LEO | 400 km | 1 ms | 5-15 min passes |
| Lunar | 384,400 km | 1.28 s | Far side requires relay |
| Mars | 55M-400M km | 3-22 min | Solar conjunction blackout |
| Voyager | 138-165 AU | 19-22 hr | Voyager 2 = Canberra only |

### Running the Simulation

```bash
cd src/bpv7/simulation

# Start with ION (default)
./scripts/run-demo.sh ion

# Apply space link delays
./scripts/simulate-space-link.sh mars-min

# Connect to a node
docker exec -it dtn-earth bash
```

## Key Design Decisions

1. **Pure Python Implementation** - No external dependencies except standard library
2. **CBOR from scratch** - Implements deterministic CBOR per RFC 8949
3. **Dual Implementation** - Both clean-room Python and ION integration
4. **Realistic Simulation** - Contact plans based on actual mission operations
5. **Export Control Awareness** - Documents TReK restrictions, uses open source ION

## Verification

Protocol compliance is verified through:

- CBOR encoding conformance tests
- CRC-16 X.25 and CRC-32C test vectors
- Bundle structure integrity checks
- Interoperability testing with NASA JPL ION-DTN

Run tests:
```bash
PYTHONPATH=src python3 -m pytest src/bpv7/tests/ -v
```

Or without pytest:
```bash
PYTHONPATH=src python3 src/bpv7/example.py
```

## References

- [NASA ION-DTN](https://github.com/nasa-jpl/ION-DTN) - Open source BPv7
- [NASA TReK](https://trek.msfc.nasa.gov) - Mission ops toolkit (export-controlled)
- [DSN Now](https://eyes.nasa.gov/apps/dsn-now/) - Real-time DSN activity
- [LunaNet Spec v5](https://www.nasa.gov/lunanet) - Lunar DTN architecture
