# SpeakUp Decision Log

This document captures key decisions made during project execution,
including constraints encountered, options evaluated, and rationale.

---

## Decision: DTN Implementation Selection

**Date:** 2025-12-22
**Status:** Decided
**Category:** Technical / Export Control

### Context

The BPv7 implementation requires a test environment to validate bundle
protocol operations. During research, we identified NASA TReK as the
official mission operations toolkit with comprehensive DTN support.

### Constraint Encountered

**NASA TReK is export-controlled:**

| Field | Value |
|-------|-------|
| ECCN | 9D515.B.5 |
| Jurisdiction | EAR (Export Administration Regulations) |
| Category | Aerospace and Propulsion |

Registration requires:
- NASA sponsorship
- US citizenship or green card, OR International Agreement
- Contract/grant/project association

### Options Evaluated

| Option | Pros | Cons |
|--------|------|------|
| **A: Register for TReK** | Official NASA tooling, mission-ready, full CFDP/ION integration | Export control compliance burden, requires sponsor, delays project |
| **B: Use ION-DTN Open Source** | No restrictions, full BPv7, proven in missions | Less integrated than TReK |
| **C: Clean-Room Only** | Complete control, no dependencies | Must build everything, no interop validation |
| **D: Hybrid (B + C)** | Best of both - ION for reference, Python for learning | Two implementations to maintain |

### Decision

**Selected: Option D - Hybrid Approach**

Implement both:
1. NASA JPL ION-DTN (open source) for reference interoperability
2. SpeakUp Python implementation for clean-room demonstration

Provide configurable selection at runtime:
- `./run-demo.sh ion` - NASA JPL ION-DTN
- `./run-demo.sh python` - SpeakUp Python
- `./run-demo.sh interop` - Mixed (validates compliance)

### Rationale

1. **No export control barriers** - ION is open source (NASA Open Source Agreement)
2. **Interoperability proof** - Can validate Python against reference implementation
3. **Educational value** - Clean-room implementation demonstrates RFC understanding
4. **Future path** - TReK registration can proceed independently if needed
5. **Demonstrates constraint handling** - Shows how to work around blockers

### Implications

- TReK integration documented as future enhancement, not current requirement
- Export control notice added to repository (`EXPORT_CONTROL.md`)
- Simulation environment works without NASA registration
- Project remains executable for demonstration purposes

### References

- [NASA ION-DTN](https://github.com/nasa-jpl/ION-DTN) - Selected open source implementation
- [NASA TReK](https://trek.msfc.nasa.gov) - Future integration path
- [TReK Registration](https://trek.msfc.nasa.gov/assets/documents/trek_registration.pdf) - Export control requirements

---

## Decision Template

```markdown
## Decision: [Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Decided | Superseded
**Category:** [Technical | Process | Resource | External]

### Context
[Why is this decision needed?]

### Constraint Encountered
[What blocker or limitation was identified?]

### Options Evaluated
| Option | Pros | Cons |
|--------|------|------|

### Decision
[What was decided?]

### Rationale
[Why was this option selected?]

### Implications
[What are the consequences?]

### References
[Links to supporting documentation]
```

---

*This decision log demonstrates the SpeakUp principle: when you hit a
constraint, document it explicitly, evaluate options transparently, and
make the decision traceable.*
