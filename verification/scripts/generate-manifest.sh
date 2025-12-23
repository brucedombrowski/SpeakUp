#!/bin/bash
#
# SpeakUp File Integrity Manifest Generator
#
# Purpose: Generate cryptographic hashes for all repository files
# Method: SHA-256 checksums for integrity verification
# Standards:
#   - NIST SP 800-53: SI-7 (Software, Firmware, and Information Integrity)
#   - FIPS 180-4 (Secure Hash Standard - SHA-256)
#
# Output: verification/File-Manifest.md
#
# Exit codes:
#   0 = Manifest generated successfully
#   1 = Error generating manifest
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_FILE="$REPO_ROOT/verification/File-Manifest.md"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

echo "SpeakUp File Integrity Manifest Generator"
echo "=========================================="
echo "Timestamp: $TIMESTAMP"
echo ""

# Initialize output
cat > "$OUTPUT_FILE" << EOF
# SpeakUp File Integrity Manifest

---

## Manifest Information

| Field | Value |
|-------|-------|
| Generated | $TIMESTAMP |
| Algorithm | SHA-256 |
| Standard | FIPS 180-4 (Secure Hash Standard) |

---

## Purpose

This manifest provides cryptographic hashes for all repository files, enabling:

1. **Integrity Verification** - Detect unauthorized modifications
2. **Authenticity Confirmation** - Verify file contents match expected values
3. **Chain of Custody** - Document file state at a point in time

---

## File Hashes

| File | SHA-256 Hash |
|------|--------------|
EOF

# Generate hashes for all tracked files
echo "Generating SHA-256 hashes..."

cd "$REPO_ROOT"

# Get list of files (excluding .git, generated files, and this manifest)
find . -type f \
    -not -path "./.git/*" \
    -not -path "./.DS_Store" \
    -not -name ".DS_Store" \
    -not -name "File-Manifest.md" \
    -not -name "*.aux" \
    -not -name "*.log" \
    -not -name "*.nav" \
    -not -name "*.out" \
    -not -name "*.snm" \
    -not -name "*.toc" \
    -not -name "*.vrb" \
    | sort | while read -r file; do

    # Skip binary files for PDF (hash them but note they're binary)
    filename=$(basename "$file")
    hash=$(shasum -a 256 "$file" 2>/dev/null | cut -d' ' -f1)

    if [ -n "$hash" ]; then
        echo "| \`$file\` | \`$hash\` |" >> "$OUTPUT_FILE"
        echo "  $file"
    fi
done

# Add summary
cat >> "$OUTPUT_FILE" << EOF

---

## Verification Instructions

To verify file integrity, run:

\`\`\`bash
shasum -a 256 <filename>
\`\`\`

Compare the output hash with the value in this manifest.

---

## NIST Control Reference

| Control | Description |
|---------|-------------|
| SI-7 | Software, Firmware, and Information Integrity |
| SI-7(1) | Integrity Checks |
| SI-7(6) | Cryptographic Protection |

---

## Notes

- This manifest is regenerated with each verification run
- Binary files (PDF) are included in the hash
- The manifest itself is excluded from hashing (circular reference)
- Git commit hashes provide additional integrity verification

---

*This manifest was automatically generated for integrity verification purposes.*
EOF

echo ""
echo "=========================================="
echo "Manifest generated: $OUTPUT_FILE"
echo ""

exit 0
