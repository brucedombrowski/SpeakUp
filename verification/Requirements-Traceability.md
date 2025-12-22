# SpeakUp Requirements Traceability Matrix

---

## Purpose

This matrix provides bidirectional traceability between requirements defined
in the SpeakUp README and evidence of their satisfaction.

---

## Requirements to Evidence (Forward Traceability)

| Req ID | Requirement Statement | Evidence Location | Verification Method |
|--------|----------------------|-------------------|---------------------|
| FR-1.1 | Smartphone-based ideation | README:137-150 | Inspection |
| FR-1.2 | Text input primary | README:143 | Inspection |
| FR-1.3 | Voice input supported | README:145 | Inspection |
| FR-2.1 | Modern IDE environment | Execution context | Demonstration |
| FR-2.2 | AI assistance integrated | Execution context | Demonstration |
| FR-2.3 | AI component replaceable | README:159 | Inspection |
| FR-2.4 | Enterprise trust boundary | Execution context | Demonstration |
| FR-3.1 | Git-based VCS | .git directory | Demonstration |
| FR-3.2 | Work artifacts captured | artifacts/, briefing/, verification/ | Demonstration |
| FR-3.3 | History captured | Git log | Demonstration |
| FR-3.4 | Rationale captured | Commit messages | Demonstration |
| FR-3.5 | Authoritative SoR | README:175 | Inspection |
| FR-4.1 | Security at identity | Execution context | Demonstration |
| FR-4.2 | Security at device | Execution context | Demonstration |
| FR-4.3 | AI in-boundary | Execution context | Demonstration |
| FR-4.4 | Handling rules maintained | Compliance-Statement.md | Analysis |
| FR-5.1 | Email not work | README:195 | Inspection |
| FR-5.2 | Minimize non-actionable | Repository content | Inspection |
| FR-5.3 | Email for notification | README:203-205 | Inspection |

---

## Evidence to Requirements (Backward Traceability)

| Evidence | Location | Satisfies Requirements |
|----------|----------|------------------------|
| README.md | Root | All FR definitions |
| SpeakUp-Briefing.md | briefing/ | Expected Output: Briefing Deck |
| Compliance-Statement.md | verification/ | Verification Intent, Expected Outputs |
| Requirements-Traceability.md | verification/ | Verification Intent |
| Directory structure | artifacts/, briefing/, verification/ | FR-3.2, Expected Outputs |
| Git repository | .git/ | FR-3.1, FR-3.3, FR-3.4 |

---

## Information Handling Traceability

| Statement | README Reference | Evidence |
|-----------|------------------|----------|
| No sensitive PII | Line 218 | Compliance-Statement.md |
| No CUI | Line 220 | Compliance-Statement.md |
| No proprietary info | Line 222 | Compliance-Statement.md |
| No classified info | Line 224 | Compliance-Statement.md |
| Author attribution | Lines 226-228 | README Author section |

---

## Change Control Traceability

| Change Control Requirement | README Reference | Status |
|---------------------------|------------------|--------|
| Controlled changes only | Lines 305-319 | ACTIVE |
| Change Log updates | Line 311 | ACTIVE |
| Minimal edits | Line 313 | ACTIVE |
| No unauthorized new requirements | Lines 315-316 | ACTIVE |
| Security not weakened | Line 318 | ACTIVE |

---

## Verification Status Legend

| Status | Meaning |
|--------|---------|
| DEMONSTRATED | Requirement satisfied through execution evidence |
| INSPECTED | Requirement verified by document review |
| ANALYZED | Requirement verified by analysis of multiple sources |
| PENDING | Requirement not yet verified |

---

*This traceability matrix supports the Verification Intent requirement for
traceability between requirements and evidence.*
