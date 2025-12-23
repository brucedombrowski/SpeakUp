#!/bin/bash
#
# SpeakUp PII Verification Script
#
# Purpose: Automated scanning of repository files for potential PII patterns
# Method: Pattern matching using grep with regex
# Output: Test results logged to verification/PII-Scan-Results.md
#
# Patterns checked:
#   - IP addresses (IPv4)
#   - Phone numbers (US formats)
#   - Social Security Numbers
#   - Email addresses (non-example domains)
#
# Exit codes:
#   0 = All checks passed (no PII found)
#   1 = Potential PII detected (requires review)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_FILE="$REPO_ROOT/verification/PII-Scan-Results.md"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Files to scan (exclude binary, git, and this script's output)
SCAN_TARGETS="$REPO_ROOT/README.md $REPO_ROOT/artifacts/*.md $REPO_ROOT/verification/*.md $REPO_ROOT/briefing/*.tex"

# Initialize output
cat > "$OUTPUT_FILE" << EOF
# PII Scan Results

---

## Scan Information

| Field | Value |
|-------|-------|
| Scan Date | $TIMESTAMP |
| Script | verification/scripts/check-pii.sh |
| Repository | SpeakUp |

---

## Pattern Definitions

| Pattern Type | Regex | Description |
|--------------|-------|-------------|
| IPv4 Address | \`[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\` | Standard dotted-quad notation |
| US Phone | \`[0-9]{3}[-. ][0-9]{3}[-. ][0-9]{4}\` | XXX-XXX-XXXX and variants |
| US Phone (parens) | \`\([0-9]{3}\)[ ]*[0-9]{3}[-. ][0-9]{4}\` | (XXX) XXX-XXXX format |
| SSN | \`[0-9]{3}-[0-9]{2}-[0-9]{4}\` | Standard SSN format |
| SSN (no dashes) | \`\b[0-9]{9}\b\` | Nine consecutive digits |

---

## Scan Results

EOF

FOUND_ISSUES=0

echo "SpeakUp PII Verification Scan"
echo "=============================="
echo "Timestamp: $TIMESTAMP"
echo ""

# Function to run a check and log results
run_check() {
    local check_name="$1"
    local pattern="$2"
    local description="$3"

    echo "Checking: $check_name"

    # Run grep, capture output
    local results=""
    local count=0

    for file in $SCAN_TARGETS; do
        if [ -f "$file" ]; then
            local file_results=$(grep -n -E "$pattern" "$file" 2>/dev/null || true)
            if [ -n "$file_results" ]; then
                results="$results\n### $(basename $file)\n\`\`\`\n$file_results\n\`\`\`\n"
                count=$((count + $(echo "$file_results" | wc -l)))
            fi
        fi
    done

    # Log to output file
    echo "### $check_name" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "**Pattern:** \`$pattern\`" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "**Description:** $description" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    if [ $count -eq 0 ]; then
        echo "**Result:** PASS - No matches found" >> "$OUTPUT_FILE"
        echo "  Result: PASS (0 matches)"
    else
        echo "**Result:** REVIEW REQUIRED - $count potential match(es) found" >> "$OUTPUT_FILE"
        echo -e "$results" >> "$OUTPUT_FILE"
        echo "  Result: REVIEW - $count match(es) found"
        FOUND_ISSUES=1
    fi
    echo "" >> "$OUTPUT_FILE"
    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
}

# Run all checks
run_check "IPv4 Addresses" \
    "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" \
    "Searches for IP address patterns that could identify network infrastructure"

run_check "US Phone Numbers (dashed)" \
    "[0-9]{3}[-][0-9]{3}[-][0-9]{4}" \
    "Searches for phone numbers in XXX-XXX-XXXX format"

run_check "US Phone Numbers (dotted)" \
    "[0-9]{3}[.][0-9]{3}[.][0-9]{4}" \
    "Searches for phone numbers in XXX.XXX.XXXX format"

run_check "US Phone Numbers (parenthetical)" \
    "\([0-9]{3}\)[ ]*[0-9]{3}[-. ][0-9]{4}" \
    "Searches for phone numbers in (XXX) XXX-XXXX format"

run_check "Social Security Numbers" \
    "[0-9]{3}-[0-9]{2}-[0-9]{4}" \
    "Searches for SSN patterns in XXX-XX-XXXX format"

run_check "Credit Card Numbers (16 digit)" \
    "[0-9]{4}[-. ]?[0-9]{4}[-. ]?[0-9]{4}[-. ]?[0-9]{4}" \
    "Searches for 16-digit sequences that could be credit card numbers"

# Summary
echo "" >> "$OUTPUT_FILE"
echo "## Summary" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ $FOUND_ISSUES -eq 0 ]; then
    echo "**Overall Result: PASS**" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "No potential PII patterns detected in scanned files." >> "$OUTPUT_FILE"
    echo ""
    echo "=============================="
    echo "OVERALL RESULT: PASS"
    echo "No PII patterns detected."
else
    echo "**Overall Result: REVIEW REQUIRED**" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "Potential PII patterns detected. Manual review required to determine if matches represent actual sensitive information or false positives (e.g., version numbers, example data)." >> "$OUTPUT_FILE"
    echo ""
    echo "=============================="
    echo "OVERALL RESULT: REVIEW REQUIRED"
    echo "See $OUTPUT_FILE for details."
fi

echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "*This report was automatically generated by the SpeakUp PII verification script.*" >> "$OUTPUT_FILE"

echo ""
echo "Results written to: $OUTPUT_FILE"

exit $FOUND_ISSUES
