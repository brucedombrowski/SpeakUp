# Training Materials - Known Issues

## Open Issues

### ISSUE-001: B-roll workflow diagram misaligned with slide deck (2024-12-23)

**Status**: Open

**Problem**:
- The B-roll `visual-assets/workflow-diagram.png` is a simplified ImageMagick-generated graphic
- It does NOT match the actual workflow diagram in the briefing slide deck
- The video shows the B-roll version, then immediately shows slide-03 (the real workflow slide)
- This creates visual inconsistency and a jarring duplicate

**Root Cause**:
- B-roll assets were generated independently of the slide deck
- No automated sync between slide deck updates and B-roll assets
- The BROLL_SEQUENCE in generate-video.sh hardcodes which visuals to show

**Impact**:
- Undermines the "everything stays in sync" message of SpeakUp
- Viewer sees two different versions of the same concept back-to-back
- Breaks the principle: "as we make updates we don't break supporting materials"

**Proposed Fix**:
1. Option A: Remove B-roll workflow diagram, only show the slide
2. Option B: Export slide-03 as the B-roll workflow asset (keep them identical)
3. Option C: Generate B-roll from slide deck automatically during build

**Recommended**: Option C - automate B-roll extraction from slides so they can never drift

**Files Affected**:
- `training/generate-video.sh` (BROLL_SEQUENCE)
- `training/visual-assets/workflow-diagram.png`
- `training/generate-visuals.sh`

---

## Design Principle Reminder

> "As we make updates we don't break all the supporting materials and they stay up to date."

This means:
1. Single source of truth for each visual/concept
2. Derived assets should be generated, not manually maintained
3. Build process should detect drift between sources and derivatives

---

## Issue Template

```markdown
### ISSUE-XXX: [Brief description] (YYYY-MM-DD)

**Status**: Open | In Progress | Resolved

**Problem**:
[What's wrong]

**Root Cause**:
[Why it happened]

**Impact**:
[Who/what is affected]

**Proposed Fix**:
[Options and recommendation]

**Files Affected**:
[List of files]
```
