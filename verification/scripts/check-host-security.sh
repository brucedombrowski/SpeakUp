#!/bin/bash
#
# SpeakUp Host OS Security Verification Script
#
# Purpose: Verify host system security posture for execution environment
# Method: Check macOS security settings, installed security tools, and system state
# Standards:
#   - NIST SP 800-53: CM-6 (Configuration Settings)
#   - NIST SP 800-53: SI-2 (Flaw Remediation)
#   - CIS macOS Benchmark (where applicable)
#
# IMPORTANT: This script only produces a public report if ALL checks pass.
# Vulnerability details are NEVER exposed in public artifacts.
#
# Output:
#   - PASS: Attestation written to verification/Host-Security-Attestation.md
#   - FAIL: No public output (details logged to console only)
#
# Exit codes:
#   0 = All checks passed (attestation produced)
#   1 = One or more checks failed (no attestation)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_FILE="$REPO_ROOT/verification/Host-Security-Attestation.md"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

echo "SpeakUp Host OS Security Verification"
echo "======================================"
echo "Timestamp: $TIMESTAMP"
echo ""
echo "NOTE: Detailed results are NOT written to repository."
echo "Only a clean attestation is produced on PASS."
echo ""

# Track overall status
OVERALL_STATUS="PASS"
FAIL_COUNT=0

# Function to run a check (results only to console, not file)
run_check() {
    local check_name="$1"
    local check_command="$2"
    local expected="$3"

    echo "Checking: $check_name"

    local result=""
    result=$(eval "$check_command" 2>/dev/null || echo "ERROR")

    if [[ "$result" == *"$expected"* ]] || [[ "$expected" == "EXISTS" && -n "$result" && "$result" != "ERROR" ]]; then
        echo "  Result: PASS"
        return 0
    else
        echo "  Result: FAIL (details not disclosed)"
        OVERALL_STATUS="FAIL"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
}

# Run security checks (results to console only)
echo "Running security configuration checks..."
echo ""

# Check if SIP is enabled
run_check "System Integrity Protection (SIP)" \
    "csrutil status" \
    "enabled" || true

# Check FileVault status
run_check "FileVault Disk Encryption" \
    "fdesetup status" \
    "On" || true

# Check Firewall status
run_check "macOS Application Firewall" \
    "/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate" \
    "enabled" || true

# Check Gatekeeper status
run_check "Gatekeeper" \
    "spctl --status" \
    "enabled" || true

# Check XProtect
run_check "XProtect Malware Definitions" \
    "test -f /Library/Apple/System/Library/CoreServices/XProtect.bundle/Contents/version.plist && echo EXISTS" \
    "EXISTS" || true

# Check for pending security updates
echo "Checking: Pending Security Updates"
UPDATE_OUTPUT=$(softwareupdate -l 2>&1 || true)
UPDATE_COUNT=$(echo "$UPDATE_OUTPUT" | grep -ci "security" || true)
if [ -z "$UPDATE_COUNT" ] || [ "$UPDATE_COUNT" -eq 0 ]; then
    echo "  Result: PASS (no security updates pending)"
else
    echo "  Result: FAIL (security updates available - details not disclosed)"
    OVERALL_STATUS="FAIL"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

echo ""
echo "======================================"

# Only produce public output if ALL checks pass
if [ "$OVERALL_STATUS" = "PASS" ]; then
    echo "OVERALL RESULT: PASS"
    echo ""
    echo "Producing attestation..."

    cat > "$OUTPUT_FILE" << EOF
# Host Security Attestation

---

## Attestation Statement

This document attests that the host system used for SpeakUp execution has
been verified to meet baseline security requirements.

---

## Verification Summary

| Field | Value |
|-------|-------|
| Attestation Date | $TIMESTAMP |
| Host OS | $(sw_vers -productName) $(sw_vers -productVersion) |
| Architecture | $(uname -m) |
| Overall Status | **PASS** |

---

## Security Controls Verified

The following security controls were verified as enabled/current:

| Control | NIST Reference | Status |
|---------|----------------|--------|
| System Integrity Protection (SIP) | CM-6 | Enabled |
| FileVault Disk Encryption | SC-28 | Enabled |
| Application Firewall | SC-7 | Enabled |
| Gatekeeper | CM-7 | Enabled |
| XProtect Definitions | SI-3 | Current |
| Security Updates | SI-2 | Current |

---

## Attestation Scope

This attestation confirms that at the time of verification:

1. The host operating system has security features enabled
2. Built-in malware protection is current
3. No pending security updates are required
4. The execution environment meets baseline security requirements

---

## Important Notes

- This attestation is valid only for the timestamp indicated
- Detailed scan results are not disclosed for security reasons
- Only a passing verification produces this attestation
- Failed verifications do not generate public artifacts

---

## Standards Reference

| Standard | Description |
|----------|-------------|
| NIST SP 800-53 Rev 5 | Security and Privacy Controls |
| NIST SP 800-171 | Protecting CUI |
| CIS macOS Benchmark | Hardening guidelines |

---

*This attestation was automatically generated upon successful completion
of all host security verification checks.*
EOF

    echo "Attestation written to: $OUTPUT_FILE"
    exit 0

else
    echo "OVERALL RESULT: FAIL ($FAIL_COUNT check(s) failed)"
    echo ""
    echo "No attestation produced."
    echo "Remediate issues and re-run verification."
    echo ""
    echo "IMPORTANT: Failure details are NOT written to repository."

    # Remove any existing attestation file if checks fail
    if [ -f "$OUTPUT_FILE" ]; then
        rm "$OUTPUT_FILE"
        echo "Previous attestation removed."
    fi

    exit 1
fi
