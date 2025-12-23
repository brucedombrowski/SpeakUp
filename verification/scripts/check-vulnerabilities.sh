#!/bin/bash
#
# SpeakUp Vulnerability Verification Script
#
# Purpose: Automated scanning for common security vulnerabilities
# Method: Pattern matching for secrets, credentials, and security anti-patterns
# Output: Test results logged to verification/Vulnerability-Scan-Results.md
#
# Checks performed:
#   - Hardcoded API keys and tokens
#   - AWS/cloud credentials
#   - Private keys
#   - Database connection strings with passwords
#   - Hardcoded passwords in code
#   - Shell injection vulnerabilities in scripts
#
# Exit codes:
#   0 = All checks passed (no vulnerabilities found)
#   1 = Potential vulnerabilities detected (requires review)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_FILE="$REPO_ROOT/verification/Vulnerability-Scan-Results.md"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Files to scan (exclude binary, git, and verification output files)
SCAN_DIR="$REPO_ROOT"

# Initialize output
cat > "$OUTPUT_FILE" << EOF
# Vulnerability Scan Results

---

## Scan Information

| Field | Value |
|-------|-------|
| Scan Date | $TIMESTAMP |
| Script | verification/scripts/check-vulnerabilities.sh |
| Repository | SpeakUp |

---

## Vulnerability Checks

EOF

FOUND_ISSUES=0

echo "SpeakUp Vulnerability Verification Scan"
echo "========================================"
echo "Timestamp: $TIMESTAMP"
echo ""

# Function to run a check and log results
run_check() {
    local check_name="$1"
    local pattern="$2"
    local description="$3"
    local severity="$4"

    echo "Checking: $check_name"

    # Run grep, capture output (exclude .git, binary files, scan results, and verification scripts)
    local results=""
    results=$(grep -r -n -E "$pattern" "$SCAN_DIR" \
        --include="*.sh" \
        --include="*.py" \
        --include="*.js" \
        --include="*.ts" \
        --include="*.rb" \
        --include="*.php" \
        --include="*.yaml" \
        --include="*.yml" \
        --include="*.json" \
        --include="*.env" \
        --include="*.conf" \
        --include="*.config" \
        --include="*.md" \
        --include="*.tex" \
        --exclude-dir=".git" \
        --exclude="*Scan-Results.md" \
        --exclude="check-*.sh" \
        2>/dev/null || true)

    local count=0
    if [ -n "$results" ]; then
        count=$(echo "$results" | wc -l | tr -d ' ')
    fi

    # Log to output file
    echo "### $check_name" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "**Severity:** $severity" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "**Pattern:** \`$pattern\`" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "**Description:** $description" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    if [ "$count" -eq 0 ]; then
        echo "**Result:** PASS - No matches found" >> "$OUTPUT_FILE"
        echo "  Result: PASS (0 matches)"
    else
        echo "**Result:** REVIEW REQUIRED - $count potential match(es) found" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "\`\`\`" >> "$OUTPUT_FILE"
        echo "$results" >> "$OUTPUT_FILE"
        echo "\`\`\`" >> "$OUTPUT_FILE"
        echo "  Result: REVIEW - $count match(es) found"
        FOUND_ISSUES=1
    fi
    echo "" >> "$OUTPUT_FILE"
    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
}

# Run all vulnerability checks

run_check "AWS Access Keys" \
    "AKIA[0-9A-Z]{16}" \
    "AWS access key IDs that could provide cloud access" \
    "CRITICAL"

run_check "AWS Secret Keys" \
    "['\"][A-Za-z0-9/+=]{40}['\"]" \
    "Potential AWS secret access keys (40-char base64)" \
    "CRITICAL"

run_check "Generic API Keys" \
    "(api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"][A-Za-z0-9]{16,}" \
    "Generic API key patterns in configuration" \
    "HIGH"

run_check "Private Keys" \
    "-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----" \
    "Private key files that should never be committed" \
    "CRITICAL"

run_check "Database Connection Strings" \
    "(mysql|postgres|mongodb|redis)://[^:]+:[^@]+@" \
    "Database URIs containing embedded credentials" \
    "CRITICAL"

run_check "Hardcoded Passwords" \
    "(password|passwd|pwd)['\"]?\s*[:=]\s*['\"][^'\"]{8,}" \
    "Hardcoded password assignments (excluding examples)" \
    "HIGH"

run_check "Bearer Tokens" \
    "Bearer\s+[A-Za-z0-9_-]{20,}" \
    "Hardcoded bearer authentication tokens" \
    "HIGH"

run_check "GitHub Tokens" \
    "gh[pousr]_[A-Za-z0-9_]{36,}" \
    "GitHub personal access tokens" \
    "CRITICAL"

run_check "Slack Tokens" \
    "xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}" \
    "Slack API tokens" \
    "HIGH"

run_check "Shell Command Injection" \
    "eval\s+\"\\\$" \
    "Potential shell command injection via eval" \
    "MEDIUM"

# Summary
echo "" >> "$OUTPUT_FILE"
echo "## Summary" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ $FOUND_ISSUES -eq 0 ]; then
    echo "**Overall Result: PASS**" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "No potential vulnerabilities detected in scanned files." >> "$OUTPUT_FILE"
    echo ""
    echo "========================================"
    echo "OVERALL RESULT: PASS"
    echo "No vulnerabilities detected."
else
    echo "**Overall Result: REVIEW REQUIRED**" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "Potential vulnerabilities detected. Manual review required to determine if matches represent actual security issues or false positives." >> "$OUTPUT_FILE"
    echo ""
    echo "========================================"
    echo "OVERALL RESULT: REVIEW REQUIRED"
    echo "See $OUTPUT_FILE for details."
fi

echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "### Vulnerability Categories" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "| Severity | Description |" >> "$OUTPUT_FILE"
echo "|----------|-------------|" >> "$OUTPUT_FILE"
echo "| CRITICAL | Immediate security risk, requires remediation |" >> "$OUTPUT_FILE"
echo "| HIGH | Significant security concern |" >> "$OUTPUT_FILE"
echo "| MEDIUM | Potential security issue depending on context |" >> "$OUTPUT_FILE"
echo "| LOW | Minor security consideration |" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "*This report was automatically generated by the SpeakUp vulnerability verification script.*" >> "$OUTPUT_FILE"

echo ""
echo "Results written to: $OUTPUT_FILE"

exit $FOUND_ISSUES
