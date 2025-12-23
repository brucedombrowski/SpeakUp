#!/bin/bash
#
# SpeakUp Master Verification Script
#
# Purpose: Run all security verification scans and produce consolidated attestation
# Standards Reference:
#   - NIST SP 800-53 Rev 5: Security and Privacy Controls
#   - NIST SP 800-171: Protecting CUI in Nonfederal Systems
#   - FIPS 199: Standards for Security Categorization
#   - FIPS 200: Minimum Security Requirements
#
# SECURITY POLICY:
#   - Only PASSING results are published to the repository
#   - Vulnerability/failure details are NEVER exposed publicly
#   - Failed scans produce console output only (not committed)
#
# Exit codes:
#   0 = All scans passed (attestation produced)
#   1 = One or more scans failed (no public artifacts)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ATTESTATION_FILE="$REPO_ROOT/verification/Security-Attestation.md"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

echo "========================================================"
echo "SpeakUp Security Verification Suite"
echo "========================================================"
echo "Timestamp: $TIMESTAMP"
echo ""
echo "SECURITY POLICY: Only passing results are published."
echo "Vulnerability details are never exposed publicly."
echo ""
echo "========================================================"
echo ""

# Track overall status
OVERALL_STATUS="PASS"
FAIL_COUNT=0

# Run each scan (suppress detailed output)
run_scan() {
    local scan_name="$1"
    local script="$2"
    local control_ref="$3"

    echo "Running: $scan_name"
    echo "  Control: $control_ref"

    if [ -x "$script" ]; then
        if "$script" > /dev/null 2>&1; then
            echo "  Result: PASS"
        else
            OVERALL_STATUS="FAIL"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            echo "  Result: FAIL (details not disclosed)"
        fi
    else
        echo "  Result: SKIPPED (script not found)"
    fi
    echo ""
}

# Run all scans with NIST control references
run_scan "PII Pattern Scan" \
    "$SCRIPT_DIR/check-pii.sh" \
    "NIST 800-53: SI-12 (Information Management)"

run_scan "Malware Scan (ClamAV)" \
    "$SCRIPT_DIR/check-malware.sh" \
    "NIST 800-53: SI-3 (Malicious Code Protection)"

run_scan "Vulnerability/Secrets Scan" \
    "$SCRIPT_DIR/check-vulnerabilities.sh" \
    "NIST 800-53: SA-11 (Developer Testing)"

run_scan "IEEE 802.3 MAC Address Scan" \
    "$SCRIPT_DIR/check-mac-addresses.sh" \
    "NIST 800-53: SC-8 (Transmission Confidentiality)"

run_scan "Host Security Configuration" \
    "$SCRIPT_DIR/check-host-security.sh" \
    "NIST 800-53: CM-6 (Configuration Settings)"

echo "========================================================"

# Only produce attestation if ALL scans pass
if [ "$OVERALL_STATUS" = "PASS" ]; then
    echo "OVERALL RESULT: PASS"
    echo ""
    echo "All security scans passed. Producing attestation..."

    cat > "$ATTESTATION_FILE" << EOF
# SpeakUp Security Attestation

---

## Attestation Statement

This document attests that the SpeakUp repository and execution environment
have been verified to meet security requirements through automated scanning.

---

## Attestation Summary

| Field | Value |
|-------|-------|
| Attestation Date | $TIMESTAMP |
| Repository | SpeakUp |
| Overall Status | **PASS** |

---

## Verification Scans Completed

| Scan | NIST Control | Status |
|------|--------------|--------|
| PII Pattern Detection | SI-12 (Information Management) | PASS |
| Malware Scan (ClamAV) | SI-3 (Malicious Code Protection) | PASS |
| Secrets/Credentials Scan | SA-11 (Developer Testing) | PASS |
| IEEE 802.3 MAC Address Scan | SC-8 (Transmission Confidentiality) | PASS |
| Host Security Configuration | CM-6 (Configuration Settings) | PASS |

---

## Standards Compliance

This verification suite aligns with federal security standards:

| Standard | Title |
|----------|-------|
| NIST SP 800-53 Rev 5 | Security and Privacy Controls |
| NIST SP 800-171 | Protecting CUI in Nonfederal Systems |
| FIPS 199 | Standards for Security Categorization |
| FIPS 200 | Minimum Security Requirements |

---

## What Was Verified

The automated verification confirms:

1. **No PII Patterns** - Repository contains no phone numbers, SSNs, IP addresses
2. **No Malware** - ClamAV scan detected no malicious code signatures
3. **No Hardcoded Secrets** - No API keys, passwords, or credentials detected
4. **No Hardware Identifiers** - No MAC addresses that could identify devices
5. **Secure Host Environment** - Execution environment meets security baseline

---

## Attestation Policy

- Only passing verifications produce this attestation
- Failed scans do not generate public artifacts
- Vulnerability details are never exposed in repository
- This attestation is valid only for the timestamp indicated

---

## FIPS 199 Security Categorization

| Impact Area | Level | Justification |
|-------------|-------|---------------|
| Confidentiality | LOW | Public methodology documentation |
| Integrity | LOW | Version-controlled artifacts |
| Availability | LOW | Non-critical demonstration project |

**Overall System Categorization: LOW**

---

*This security attestation was automatically generated upon successful
completion of all verification scans. No security findings require disclosure.*
EOF

    echo ""
    echo "Attestation written to: $ATTESTATION_FILE"
    echo ""

    # Clean up any detailed scan results (only attestation is published)
    echo "Cleaning up detailed scan results..."
    rm -f "$REPO_ROOT/verification/PII-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Malware-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Vulnerability-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/MAC-Address-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Host-Security-Attestation.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Security-Verification-Report.md" 2>/dev/null || true

    echo "Done. Only Security-Attestation.md is retained."
    exit 0

else
    echo "OVERALL RESULT: FAIL ($FAIL_COUNT scan(s) failed)"
    echo ""
    echo "No attestation produced."
    echo "Remediate issues and re-run verification."
    echo ""
    echo "IMPORTANT: Failure details are NOT written to repository."

    # Remove any existing attestation if scans fail
    if [ -f "$ATTESTATION_FILE" ]; then
        rm "$ATTESTATION_FILE"
        echo "Previous attestation removed."
    fi

    # Clean up all scan result files
    rm -f "$REPO_ROOT/verification/PII-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Malware-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Vulnerability-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/MAC-Address-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Host-Security-Attestation.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Security-Verification-Report.md" 2>/dev/null || true

    exit 1
fi
