# Contact Plans for DTN Simulation

Reference contact schedules based on real space mission operations.

## Sources

- [NASA DSN Now](https://eyes.nasa.gov/apps/dsn-now/) - Real-time DSN activity
- [Deep Space Network](https://www.jpl.nasa.gov/missions/dsn/) - JPL DSN overview
- CCSDS 734.20-O-1 Section 3.2 - Contact Graph Routing

## Typical Contact Windows

### Deep Space Network (DSN)

Each of the three DSN complexes provides 8-14 hour visibility windows:

| Complex | Location | Longitude |
|---------|----------|-----------|
| DSS-14/43/63 | Goldstone, CA | -116.9° |
| DSS-54/55/56 | Madrid, Spain | -4.2° |
| DSS-34/35/36 | Canberra, Australia | 148.9° |

Spacecraft >120° apart in longitude from a complex are out of view.

### Mars Orbiters

- **MRO (Mars Reconnaissance Orbiter)**: ~2 hr orbit, multiple DSN contacts/day
- **MAVEN**: ~4.5 hr orbit
- **Mars Odyssey**: ~2 hr orbit

**Solar Conjunction Blackout**: Every 26 months, lasting 1-14 days when
Sun-Earth-Mars angle < 5°.

### Lunar Operations (Artemis/LunaNet)

- **Earth-Moon delay**: 1.3 seconds one-way
- **Lunar far side**: No direct Earth contact (requires relay)
- **Lunar orbit**: ~2 hr orbital period

### Voyager 1 & 2

- **Current distance**: ~160 AU (Voyager 1), ~135 AU (Voyager 2)
- **Light time**: ~22 hours (Voyager 1), ~19 hours (Voyager 2)
- **Contact**: ~12 hours/day via 70m antennas only
- **Voyager 2**: Only visible from Canberra (DSS-43)

## Contact Plan Format (ION)

ION uses contact plan files defining when links are available:

```
# Contact: start_time duration from_node to_node rate
a contact +0 +3600 1 2 100000
a contact +3600 +7200 2 3 50000

# Range: start_time duration from_node to_node owlt_seconds
a range +0 +86400 1 2 1.3
```

## Simulated Scenarios

### scenario_leo.txt
Low Earth Orbit satellite operations:
- 92-minute orbital period (ISS-like)
- 5-15 minute ground contacts per pass
- 4-6 passes per day from single station
- Optional TDRSS relay for near-continuous coverage
- ~1ms one-way delay

### scenario_lunar.txt
Artemis/LunaNet lunar operations:
- Earth <-> Lunar Gateway (NRHO) with 7-day period
- Gateway <-> Surface relay for far-side coverage
- 1.28 second one-way light time
- Lunar occultation blackouts (~6 hours)
- Based on NASA LunaNet Interoperability Spec v5 (2025)

### scenario_mars.txt
Mars relay network operations:
- Earth <-> Mars Orbiter <-> Mars Lander topology
- 10-minute one-way light time (moderate distance)
- 15-minute orbiter passes every 2 hours
- Solar conjunction blackout (14 days, every 26 months)
- Based on MRO/Mars Odyssey operations

### scenario_voyager.txt
Voyager deep space operations:
- Voyager 1: 165 AU, 22-hour one-way light time
- Voyager 2: 138 AU, 19-hour one-way light time
- Only 70m DSN antennas (DSS-14, DSS-43, DSS-63)
- **Voyager 2: Only visible from Canberra (DSS-43)**
- 12-hour daily contact windows
- 160 bps data rate (20 bytes/second)
- Historical: DSS-43 maintenance blackout (2020)
