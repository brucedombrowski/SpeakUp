# SpeakUp Accounting

Auditable cost tracking and project accounting.

## Purpose

Provide transparent, reproducible cost calculations for:
- Human labor time (derived from git commit history)
- Compute costs (AI API usage, build time)
- Total project investment

## Scripts

### calculate-costs.sh

Calculates total project costs using objective, auditable methods.

```bash
./calculate-costs.sh
./calculate-costs.sh --human-rate 200
./calculate-costs.sh --output cost-report.txt
```

**Methodology:**
- Human time estimated from git commit timestamps
- Gaps > 2 hours capped at 30 minutes (context switch assumption)
- API costs estimated from conversation length
- All calculations documented in script (auditable)

**Output includes:**
- Script hash (SHA-256) for verification
- Commit reference for reproducibility
- Breakdown by cost category

## Compliance

This accounting approach supports:
- **FAR 31.205** - Cost Accounting Standards
- **DCAA Audit Guidelines** - Defense Contract Audit Agency
- **Time & Materials contracts** - Objective evidence of effort

## Auditability Features

1. **Reproducible** - Same script produces same results
2. **Traceable** - Links to git history
3. **Hashable** - Script itself is checksummed
4. **Documented** - Methodology in comments and output

## Sample Output

```
========================================================
COST SUMMARY
========================================================

Human labor (6.84 hrs)           $1026.00
Claude API                        $22.50
Build/Infrastructure               $0.00
----------------------------------------
TOTAL PROJECT COST              $1048.50

Artifacts produced: 53
Cost per artifact: $19.78
```

## Rates

Default rates (configurable):
- Human labor: $150/hour
- Claude Opus input: $0.015/1K tokens
- Claude Opus output: $0.075/1K tokens

Override with `--human-rate` flag.
