# Test Results - System of Record

This directory contains objective quality evidence (OQE) from verification tests.

## Record Retention

Test results are part of the auditable system of record and must be preserved according to applicable retention requirements:

| Context | Retention Period | Authority |
|---------|------------------|-----------|
| Federal contracts | 6 years after final payment | FAR 4.703 |
| Defense contracts | 6 years after final payment | DFARS 204.7 |
| ITAR/EAR programs | 5 years after export | 22 CFR 122.5 |
| Quality records | Life of product + 3 years | ISO 9001 |
| Safety-critical | Life of system | NASA-STD-8739.8 |

**Default policy**: Retain indefinitely in version control.

## Directory Structure

Each test run creates a timestamped directory:

```
dtn-test-YYYYMMDD_HHMMSS/
├── test-manifest.json    # Test configuration (reproducibility)
├── test-log.txt          # Complete timestamped execution log
├── transfer-stats.json   # Quantitative metrics
├── payload-sent.bin      # Original test payload
├── payload-received.bin  # Received payload (for diff)
├── checksums.sha256      # SHA-256 of all artifacts
└── test-summary.txt      # Human-readable summary
```

## Verification

To verify artifact integrity:

```bash
cd verification/test-results/dtn-test-XXXXXX/
shasum -a 256 -c checksums.sha256
```

## What Constitutes OQE

Objective Quality Evidence must be:

1. **Objective** - Not opinion; measurable, verifiable facts
2. **Complete** - All relevant data, not cherry-picked
3. **Traceable** - Links to requirements, test procedures
4. **Immutable** - Cannot be altered after the fact (git history)
5. **Reproducible** - Same inputs produce same outputs

## Test Types

| Test | Purpose | Artifacts |
|------|---------|-----------|
| `run_auditable_test.py` | DTN transfer with LOS/AOS | Payload, logs, checksums |
| `test_pdf_transfer.py` | Real file transfer | MD5 verification |
| Unit tests | Code correctness | pytest output |

## Compliance Notes

- All tests use deterministic random seeds for reproducibility
- SHA-256 checksums provide tamper evidence
- Git commit history provides immutable timestamp
- Test manifest captures environment for forensic analysis

## Running Tests

```bash
# Quick verification test (6 minutes)
python3 src/bpv7/simulation/run_auditable_test.py --duration 0.1

# Full 5-hour realistic test
python3 src/bpv7/simulation/run_auditable_test.py --duration 5 --rate 160

# After test completes, commit results
git add verification/test-results/
git commit -m "Add DTN test results: [test-id]"
```
