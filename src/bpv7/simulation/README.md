# BPv7 Space Network Simulation

A configurable DTN (Delay-Tolerant Networking) test environment demonstrating
Bundle Protocol Version 7 with three implementation options.

**Standards:** CCSDS 734.20-O-1 / RFC 9171 / RFC 9174

---

## Implementation Options

This simulation supports three approaches, selectable at runtime:

| Option | Implementation | Use Case | Restrictions |
|--------|---------------|----------|--------------|
| `ion` | NASA JPL ION-DTN | Reference interoperability | None (Open Source) |
| `python` | SpeakUp Clean-Room | Learning, customization | None |
| `interop` | Mixed (Python + ION) | Compliance verification | None |

### Option 1: NASA TReK (Not Included)

**NASA Telescience Resource Kit** is the official mission operations toolkit.

| Attribute | Value |
|-----------|-------|
| Source | https://trek.msfc.nasa.gov |
| ECCN | **9D515.B.5** (Export Controlled) |
| Access | Requires NASA registration |
| Features | Full mission ops, CFDP, ION management, Python/C++ APIs |

**Why not included:** TReK is export-controlled under EAR. Registration requires
NASA sponsorship and citizenship/green card verification. See `EXPORT_CONTROL.md`.

**When to use TReK:** Actual NASA mission operations, ISS payloads, Artemis.

---

### Option 2: NASA JPL ION-DTN (Default)

**Interplanetary Overlay Network** - NASA's open-source BPv7 reference implementation.

| Attribute | Value |
|-----------|-------|
| Source | https://github.com/nasa-jpl/ION-DTN |
| License | NASA Open Source Agreement |
| Access | Public, no registration |
| Features | Full BPv7, TCPCL, LTP, CGR, BPSec |

**Why included:** Open source, no export restrictions, full RFC 9171 compliance,
proven in actual space missions (DINET, DTN on ISS, LCRD).

```bash
# Run with ION
./scripts/run-demo.sh ion
```

---

### Option 3: SpeakUp Clean-Room Python

**Pure Python implementation** built from RFC specifications.

| Attribute | Value |
|-----------|-------|
| Source | `src/bpv7/` in this repository |
| License | Project license |
| Access | Included |
| Features | BPv7 core, CBOR, CRC, TCPCL |

**Why included:** No external dependencies, full control, educational value,
demonstrates clean-room implementation from standards.

```bash
# Run with Python implementation
./scripts/run-demo.sh python
```

---

### Option 4: Interoperability Testing

**Mixed environment** testing Python implementation against ION reference.

```bash
# Earth uses Python, Relay and Mars use ION
./scripts/run-demo.sh interop
```

This validates that our clean-room implementation produces standards-compliant
bundles that ION can correctly process.

---

## Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                    Mars Relay Network                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────┐     600 sec      ┌───────────┐     local       ┌───────────┐
│  │   Earth   │ ◄──────────────► │   Relay   │ ◄─────────────► │   Mars    │
│  │  (ipn:1)  │    10.1.1.0/24   │  (ipn:2)  │   10.2.1.0/24   │  (ipn:3)  │
│  │           │                  │           │                  │           │
│  │  Ground   │                  │  Orbiter  │                  │  Lander   │
│  │  Station  │                  │  (MRO)    │                  │           │
│  └───────────┘                  └───────────┘                  └───────────┘
│                                                                 │
│  One-way light time: 600 seconds (10 minutes)                   │
│  Orbiter-Lander contacts: 15 min every 2 hours                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Start the simulation (uses ION by default)
cd src/bpv7/simulation
./scripts/run-demo.sh

# 2. Connect to a node
docker exec -it dtn-earth bash

# 3. Send a bundle (ION)
echo "Hello Mars" | bpsource ipn:3.1

# 4. Apply realistic space link delays
./scripts/simulate-space-link.sh mars-min
```

---

## Space Link Simulation

Realistic network conditions using Linux `tc` with `netem`:

| Link Type | One-Way Delay | Loss | Use Case |
|-----------|---------------|------|----------|
| `leo` | 50ms | 0.1% | ISS, Starlink |
| `geo` | 600ms | 0.5% | TDRS, Geosat |
| `lunar` | 1.3s | 1% | Artemis, LunaNet |
| `mars-min` | 3 min | 2% | Mars closest approach |
| `mars-max` | 22 min | 5% | Mars opposition |

```bash
./scripts/simulate-space-link.sh lunar
```

---

## Contact Plans

Pre-configured scenarios in `contact_plans/`:

| Scenario | Description |
|----------|-------------|
| `scenario_mars.txt` | Earth-Mars relay with solar conjunction blackout |
| More coming... | |

Contact plans define when links are available (AOS/LOS) based on:
- DSN antenna visibility (~8-14 hours per complex)
- Orbital geometry (orbiter passes over lander)
- Solar conjunction blackouts (1-14 days)

---

## File Structure

```
simulation/
├── Dockerfile              # Container with ION + Python BPv7
├── docker-compose.yml      # 3-node network (ION)
├── docker-compose-python.yml   # 3-node network (Python)
├── docker-compose-interop.yml  # Mixed implementation
├── EXPORT_CONTROL.md       # TReK export control notice
├── config/
│   ├── earth/ion.rc        # ION config for Earth station
│   ├── relay/ion.rc        # ION config for relay satellite
│   └── mars/ion.rc         # ION config for Mars lander
├── contact_plans/
│   ├── README.md           # Reference AOS/LOS periods
│   └── scenario_mars.txt   # Mars relay contact plan
└── scripts/
    ├── run-demo.sh         # Main demo script (ion|python|interop)
    └── simulate-space-link.sh  # Apply tc/netem delays
```

---

## Why Three Options?

This demonstrates a key systems engineering principle from SpeakUp:

**When you hit a constraint, document it and provide alternatives.**

1. **TReK** is ideal but export-controlled → Document the constraint
2. **ION** is open source and mission-proven → Use as default
3. **Python** gives full control and learning → Include for flexibility

All three implement the same standards (RFC 9171). The interoperability test
proves our clean-room implementation is compliant.

---

## References

- [NASA ION-DTN](https://github.com/nasa-jpl/ION-DTN) - Open source BPv7
- [NASA TReK](https://trek.msfc.nasa.gov) - Mission operations toolkit (export-controlled)
- [RFC 9171](https://www.rfc-editor.org/rfc/rfc9171) - Bundle Protocol Version 7
- [RFC 9174](https://www.rfc-editor.org/rfc/rfc9174) - TCP Convergence Layer v4
- [CCSDS 734.20-O-1](https://public.ccsds.org) - CCSDS Bundle Protocol Specification
- [DSN Now](https://eyes.nasa.gov/apps/dsn-now/) - Real-time DSN activity
