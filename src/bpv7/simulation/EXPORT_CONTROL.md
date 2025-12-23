# Export Control Notice

## NASA TReK Software

**NASA TReK (Telescience Resource Kit) is export-controlled.**

| Classification | Value |
|---------------|-------|
| ECCN | 9D515.B.5 |
| Jurisdiction | EAR (Export Administration Regulations) |
| Category | 9 - Aerospace and Propulsion |

### Registration Requirements

TReK requires registration through NASA before use:
- US Citizens: Standard registration
- Non-US Citizens: Requires International Agreement or green card
- NASA Sponsor required for non-NASA users

Registration form: https://trek.msfc.nasa.gov/assets/documents/trek_registration.pdf

### What This Means

- TReK cannot be freely distributed internationally
- Export license may be required for foreign nationals
- Re-export restrictions apply

## This Implementation (SpeakUp BPv7)

**The SpeakUp BPv7 implementation is NOT TReK software.**

This is an independent, clean-room implementation of:
- RFC 9171 (Bundle Protocol Version 7)
- RFC 8949 (CBOR)
- RFC 9174 (TCP Convergence Layer)

These are **open IETF standards** with no export restrictions.

### Open Source References Used

| Component | Source | License |
|-----------|--------|---------|
| RFC 9171 | IETF | Public Standard |
| RFC 8949 | IETF | Public Standard |
| ION-DTN | NASA JPL | NASA Open Source |
| CCSDS Standards | CCSDS.org | Public |

NASA ION-DTN is available as open source:
https://github.com/nasa-jpl/ION-DTN

### Docker Simulation Environment

The Docker simulation uses:
- Ubuntu base image (open source)
- ION-DTN from GitHub (NASA open source)
- Our Python BPv7 (clean-room implementation)

No TReK software is included in the simulation environment.

## Recommendations

1. If you need TReK functionality, register through NASA
2. For interoperability testing, use ION-DTN (open source)
3. For production space systems, consult export control counsel
