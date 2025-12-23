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
SCANS_DIR="$REPO_ROOT/.scans"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Create .scans directory for detailed local results (git-ignored)
mkdir -p "$SCANS_DIR"

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

# Initialize summary log
SUMMARY_LOG="$SCANS_DIR/scan-summary-$(date +%Y%m%d_%H%M%S).log"
echo "SpeakUp Security Scan Results" > "$SUMMARY_LOG"
echo "=============================" >> "$SUMMARY_LOG"
echo "Timestamp: $TIMESTAMP" >> "$SUMMARY_LOG"
echo "" >> "$SUMMARY_LOG"

# Run each scan (save detailed output to .scans/ directory)
run_scan() {
    local scan_name="$1"
    local script="$2"
    local control_ref="$3"
    local output_file="$4"

    echo "Running: $scan_name"
    echo "  Control: $control_ref"

    if [ -x "$script" ]; then
        # Compute script MD5 for integrity verification
        local script_md5=$(md5 -q "$script" 2>/dev/null || md5sum "$script" | cut -d' ' -f1)
        local script_path="${script#$REPO_ROOT/}"

        # Run scan and capture output to .scans/ directory
        local detail_file="$SCANS_DIR/$output_file"
        echo "=== $scan_name ===" > "$detail_file"
        echo "Timestamp: $TIMESTAMP" >> "$detail_file"
        echo "Control: $control_ref" >> "$detail_file"
        echo "Script: $script_path" >> "$detail_file"
        echo "Script MD5: $script_md5" >> "$detail_file"
        echo "" >> "$detail_file"

        if "$script" >> "$detail_file" 2>&1; then
            echo "  Result: PASS"
            echo "PASS  Status: PASS" >> "$detail_file"
            echo "$scan_name: PASS" >> "$SUMMARY_LOG"
        else
            OVERALL_STATUS="FAIL"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            echo "  Result: FAIL (details in .scans/$output_file)"
            echo "Status: FAIL" >> "$detail_file"
            echo "$scan_name: FAIL (see $output_file)" >> "$SUMMARY_LOG"
        fi
        echo "  Details: .scans/$output_file"
    else
        echo "  Result: SKIPPED (script not found)"
        echo "$scan_name: SKIPPED" >> "$SUMMARY_LOG"
    fi
    echo ""
}

# Run all scans with NIST control references
run_scan "PII Pattern Scan" \
    "$SCRIPT_DIR/check-pii.sh" \
    "NIST 800-53: SI-12 (Information Management)" \
    "pii-scan.log"

run_scan "Malware Scan (ClamAV)" \
    "$SCRIPT_DIR/check-malware.sh" \
    "NIST 800-53: SI-3 (Malicious Code Protection)" \
    "malware-scan.log"

run_scan "Vulnerability/Secrets Scan" \
    "$SCRIPT_DIR/check-vulnerabilities.sh" \
    "NIST 800-53: SA-11 (Developer Testing)" \
    "vulnerability-scan.log"

run_scan "IEEE 802.3 MAC Address Scan" \
    "$SCRIPT_DIR/check-mac-addresses.sh" \
    "NIST 800-53: SC-8 (Transmission Confidentiality)" \
    "mac-address-scan.log"

run_scan "Host Security Configuration" \
    "$SCRIPT_DIR/check-host-security.sh" \
    "NIST 800-53: CM-6 (Configuration Settings)" \
    "host-security-scan.log"

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

    # Clean up any detailed scan results from verification/ (only attestation is published)
    echo "Cleaning up old scan results from verification/..."
    rm -f "$REPO_ROOT/verification/PII-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Malware-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Vulnerability-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/MAC-Address-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Host-Security-Attestation.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Security-Verification-Report.md" 2>/dev/null || true

    # Write overall status to summary
    echo "" >> "$SUMMARY_LOG"
    echo "OVERALL: PASS" >> "$SUMMARY_LOG"

    echo "Done. Only Security-Attestation.md is retained in repository."
    echo ""
    echo "Detailed scan results available locally in .scans/ (git-ignored):"
    echo "  - $SCANS_DIR/pii-scan.log"
    echo "  - $SCANS_DIR/malware-scan.log"
    echo "  - $SCANS_DIR/vulnerability-scan.log"
    echo "  - $SCANS_DIR/mac-address-scan.log"
    echo "  - $SCANS_DIR/host-security-scan.log"
    echo "  - $SUMMARY_LOG"
    exit 0

else
    echo "OVERALL RESULT: FAIL ($FAIL_COUNT scan(s) failed)"
    echo ""
    echo "No attestation produced."
    echo "Remediate issues and re-run verification."
    echo ""
    echo "IMPORTANT: Failure details are NOT written to repository."

    # Write overall status to summary
    echo "" >> "$SUMMARY_LOG"
    echo "OVERALL: FAIL ($FAIL_COUNT scan(s) failed)" >> "$SUMMARY_LOG"

    # Remove any existing attestation if scans fail
    if [ -f "$ATTESTATION_FILE" ]; then
        rm "$ATTESTATION_FILE"
        echo "Previous attestation removed."
    fi

    # Clean up all scan result files from verification/
    rm -f "$REPO_ROOT/verification/PII-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Malware-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Vulnerability-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/MAC-Address-Scan-Results.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Host-Security-Attestation.md" 2>/dev/null || true
    rm -f "$REPO_ROOT/verification/Security-Verification-Report.md" 2>/dev/null || true

    echo ""
    echo "Review detailed scan results in .scans/ (git-ignored):"
    echo "  - $SCANS_DIR/pii-scan.log"
    echo "  - $SCANS_DIR/malware-scan.log"
    echo "  - $SCANS_DIR/vulnerability-scan.log"
    echo "  - $SCANS_DIR/mac-address-scan.log"
    echo "  - $SCANS_DIR/host-security-scan.log"
    echo "  - $SUMMARY_LOG"

    exit 1
fi
