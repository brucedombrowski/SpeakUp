#!/bin/bash
#
# SpeakUp IEEE 802.3 MAC Address Verification Script
#
# Purpose: Automated scanning for MAC addresses per IEEE 802.3
# Method: Pattern matching for MAC address formats with optional vendor lookup
# Output: Test results logged to verification/MAC-Address-Scan-Results.md
#
# IEEE 802.3 defines MAC addresses as 48-bit identifiers
# Format: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
# First 3 octets = OUI (Organizationally Unique Identifier) assigned by IEEE
#
# Exit codes:
#   0 = All checks passed (no MAC addresses found)
#   1 = MAC addresses detected (requires review)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_FILE="$REPO_ROOT/verification/MAC-Address-Scan-Results.md"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# MAC address patterns (IEEE 802.3)
# Colon-separated: XX:XX:XX:XX:XX:XX
# Dash-separated: XX-XX-XX-XX-XX-XX
# Cisco format: XXXX.XXXX.XXXX
MAC_PATTERN_COLON="([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}"
MAC_PATTERN_DASH="([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}"
MAC_PATTERN_CISCO="([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}"

# Files to scan
SCAN_DIR="$REPO_ROOT"

# Initialize output
cat > "$OUTPUT_FILE" << EOF
# IEEE 802.3 MAC Address Scan Results

---

## Scan Information

| Field | Value |
|-------|-------|
| Scan Date | $TIMESTAMP |
| Script | verification/scripts/check-mac-addresses.sh |
| Repository | SpeakUp |
| Standard | IEEE 802.3 (Ethernet MAC addresses) |

---

## IEEE 802.3 Background

IEEE 802.3 defines the MAC (Media Access Control) address format for Ethernet:

- **Length:** 48 bits (6 octets)
- **Format:** XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
- **OUI:** First 3 octets identify the vendor (Organizationally Unique Identifier)
- **Device ID:** Last 3 octets are device-specific

MAC addresses can be sensitive because they:
- Uniquely identify network hardware
- Can be used for device tracking
- May reveal organizational network infrastructure

---

## Scan Results

EOF

FOUND_ISSUES=0
TOTAL_FOUND=0

echo "SpeakUp IEEE 802.3 MAC Address Verification Scan"
echo "================================================="
echo "Timestamp: $TIMESTAMP"
echo ""

# Function to lookup vendor from OUI
lookup_vendor() {
    local oui="$1"
    # Normalize OUI format (remove separators, uppercase)
    oui=$(echo "$oui" | tr -d ':-.' | tr 'a-f' 'A-F' | cut -c1-6)

    # Use IEEE OUI lookup API (macvendors.com provides free lookups)
    local vendor=""
    vendor=$(curl -s "https://api.macvendors.com/$oui" 2>/dev/null || echo "Unknown")

    if [ "$vendor" = "Vendor not found" ] || [ -z "$vendor" ]; then
        vendor="Unknown/Private"
    fi

    echo "$vendor"
}

# Function to run a MAC address check
run_mac_check() {
    local format_name="$1"
    local pattern="$2"

    echo "Checking: $format_name"

    # Run grep, capture output
    local results=""
    results=$(grep -r -n -o -E "$pattern" "$SCAN_DIR" \
        --include="*.sh" \
        --include="*.py" \
        --include="*.js" \
        --include="*.ts" \
        --include="*.yaml" \
        --include="*.yml" \
        --include="*.json" \
        --include="*.md" \
        --include="*.tex" \
        --include="*.conf" \
        --include="*.config" \
        --include="*.log" \
        --exclude-dir=".git" \
        --exclude="*Scan-Results.md" \
        --exclude="check-*.sh" \
        2>/dev/null || true)

    local count=0
    if [ -n "$results" ]; then
        count=$(echo "$results" | wc -l | tr -d ' ')
        TOTAL_FOUND=$((TOTAL_FOUND + count))
    fi

    # Log to output file
    echo "### $format_name" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "**Pattern:** \`$pattern\`" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    if [ "$count" -eq 0 ]; then
        echo "**Result:** PASS - No matches found" >> "$OUTPUT_FILE"
        echo "  Result: PASS (0 matches)"
    else
        echo "**Result:** REVIEW REQUIRED - $count MAC address(es) found" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "| File:Line | MAC Address | OUI | Vendor Lookup |" >> "$OUTPUT_FILE"
        echo "|-----------|-------------|-----|---------------|" >> "$OUTPUT_FILE"

        while IFS= read -r line; do
            local file_line=$(echo "$line" | cut -d':' -f1-2)
            local mac=$(echo "$line" | cut -d':' -f3-)
            # Extract OUI (first 3 octets)
            local oui=$(echo "$mac" | sed 's/[:-]//g' | cut -c1-6)
            local vendor=$(lookup_vendor "$oui")
            echo "| \`$file_line\` | \`$mac\` | $oui | $vendor |" >> "$OUTPUT_FILE"
        done <<< "$results"

        echo "  Result: REVIEW - $count MAC address(es) found"
        FOUND_ISSUES=1
    fi
    echo "" >> "$OUTPUT_FILE"
    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
}

# Run MAC address checks for each format
run_mac_check "Colon-Separated (XX:XX:XX:XX:XX:XX)" "$MAC_PATTERN_COLON"
run_mac_check "Dash-Separated (XX-XX-XX-XX-XX-XX)" "$MAC_PATTERN_DASH"
run_mac_check "Cisco Format (XXXX.XXXX.XXXX)" "$MAC_PATTERN_CISCO"

# Summary
echo "" >> "$OUTPUT_FILE"
echo "## Summary" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ $FOUND_ISSUES -eq 0 ]; then
    echo "**Overall Result: PASS**" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "No IEEE 802.3 MAC addresses detected in scanned files." >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "This indicates the repository does not contain hardware identifiers that could:" >> "$OUTPUT_FILE"
    echo "- Identify specific network devices" >> "$OUTPUT_FILE"
    echo "- Reveal organizational infrastructure" >> "$OUTPUT_FILE"
    echo "- Enable device tracking" >> "$OUTPUT_FILE"
    echo ""
    echo "================================================="
    echo "OVERALL RESULT: PASS"
    echo "No MAC addresses detected."
else
    echo "**Overall Result: REVIEW REQUIRED**" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "**Total MAC addresses found: $TOTAL_FOUND**" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "MAC addresses detected require manual review to determine if they:" >> "$OUTPUT_FILE"
    echo "- Represent actual hardware identifiers (security concern)" >> "$OUTPUT_FILE"
    echo "- Are example/placeholder addresses (acceptable)" >> "$OUTPUT_FILE"
    echo "- Are documentation references (context-dependent)" >> "$OUTPUT_FILE"
    echo ""
    echo "================================================="
    echo "OVERALL RESULT: REVIEW REQUIRED"
    echo "$TOTAL_FOUND MAC address(es) found."
    echo "See $OUTPUT_FILE for details."
fi

echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "### IEEE 802.3 Reference" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "- **Standard:** IEEE 802.3 Ethernet" >> "$OUTPUT_FILE"
echo "- **OUI Registry:** [IEEE OUI Database](https://standards.ieee.org/products-programs/regauth/)" >> "$OUTPUT_FILE"
echo "- **Address Types:**" >> "$OUTPUT_FILE"
echo "  - Unicast: LSB of first octet = 0" >> "$OUTPUT_FILE"
echo "  - Multicast: LSB of first octet = 1" >> "$OUTPUT_FILE"
echo "  - Universal: Second LSB of first octet = 0" >> "$OUTPUT_FILE"
echo "  - Local: Second LSB of first octet = 1" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "*This report was automatically generated by the SpeakUp IEEE 802.3 verification script.*" >> "$OUTPUT_FILE"

echo ""
echo "Results written to: $OUTPUT_FILE"

exit $FOUND_ISSUES
