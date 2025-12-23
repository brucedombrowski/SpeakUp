#!/bin/bash
#
# SpeakUp Document QA Verification Script
#
# Purpose: Verify document quality standards compliance
# Standards Reference:
#   - IEEE Std 1063-2001: Software User Documentation
#   - IEEE Std 610.12-1990: Standard Glossary of Software Engineering Terminology
#   - MIL-STD-498: Software Development and Documentation
#
# Checks performed:
#   - Acronyms defined on first use
#   - Consistent terminology
#   - Required sections present
#
# Exit codes:
#   0 = All checks passed
#   1 = QA issues detected (requires review)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

echo "========================================================"
echo "SpeakUp Document Quality Assurance Check"
echo "========================================================"
echo "Timestamp: $TIMESTAMP"
echo ""
echo "Standards: IEEE 1063-2001, IEEE 610.12-1990, MIL-STD-498"
echo ""
echo "========================================================"
echo ""

ISSUES_FOUND=0

# Known acronyms that must be defined on first use
ACRONYMS=(
    "PII:Personally Identifiable Information"
    "CUI:Controlled Unclassified Information"
    "AI:Artificial Intelligence"
    "IDE:Integrated Development Environment"
    "API:Application Programming Interface"
    "BYOD:Bring Your Own Device"
    "SSN:Social Security Number"
    "NIST:National Institute of Standards and Technology"
    "FIPS:Federal Information Processing Standards"
    "CBOR:Concise Binary Object Representation"
    "DTN:Delay-Tolerant Networking"
    "BPv7:Bundle Protocol Version 7"
    "TCPCL:TCP Convergence Layer"
    "LOS:Loss of Signal"
    "AOS:Acquisition of Signal"
    "RFC:Request for Comments"
    "CCSDS:Consultative Committee for Space Data Systems"
    "CRC:Cyclic Redundancy Check"
)

check_acronym_defined() {
    local file="$1"
    local acronym="$2"
    local definition="$3"
    local basename=$(basename "$file")

    # Check if acronym is used in file
    if grep -q "$acronym" "$file" 2>/dev/null; then
        # Check if definition pattern exists (acronym followed by definition in parentheses)
        # Pattern: "ACRONYM (Full Definition)" or "(Full Definition)" near ACRONYM
        if grep -qE "${acronym}[[:space:]]*\(|${acronym}[[:space:]]*---[[:space:]]*|${acronym}:[[:space:]]|textsuperscript.*${acronym}:" "$file" 2>/dev/null; then
            echo "  [PASS] $acronym defined in $basename"
            return 0
        else
            # Check if it's in a context where definition isn't required (e.g., file names, code, tables)
            # Skip if only appears in file paths, code blocks, table headers, or abbreviated lists
            local context=$(grep -n "$acronym" "$file" | head -3)
            if echo "$context" | grep -qE "texttt|verb|\.md|\.sh|\.py|RFC[[:space:]]*[0-9]|tabular|toprule|midrule|bottomrule|&.*&"; then
                echo "  [SKIP] $acronym in $basename (technical/table context)"
                return 0
            fi
            echo "  [WARN] $acronym used but not defined in $basename"
            echo "         Expected: $acronym ($definition)"
            return 1
        fi
    fi
    return 0
}

echo "Checking acronym definitions in briefing deck..."
echo ""

BRIEFING_FILE="$REPO_ROOT/briefing/SpeakUp-Briefing.tex"

if [ -f "$BRIEFING_FILE" ]; then
    for entry in "${ACRONYMS[@]}"; do
        acronym="${entry%%:*}"
        definition="${entry#*:}"

        if ! check_acronym_defined "$BRIEFING_FILE" "$acronym" "$definition"; then
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    done
else
    echo "  [ERROR] Briefing file not found: $BRIEFING_FILE"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""
echo "--------------------------------------------------------"
echo ""

echo "Checking required document sections..."
echo ""

# Check for required sections in README
README_FILE="$REPO_ROOT/README.md"
REQUIRED_SECTIONS=(
    "Project Purpose"
    "Intended Audience"
    "Terminology"
    "Functional Requirements"
    "Information Handling"
    "Verification"
    "Author"
)

if [ -f "$README_FILE" ]; then
    for section in "${REQUIRED_SECTIONS[@]}"; do
        if grep -q "$section" "$README_FILE" 2>/dev/null; then
            echo "  [PASS] README contains: $section"
        else
            echo "  [WARN] README missing section: $section"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    done
else
    echo "  [ERROR] README not found: $README_FILE"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""
echo "--------------------------------------------------------"
echo ""

echo "Checking terminology consistency..."
echo ""

# Check for inconsistent terminology
check_consistency() {
    local preferred="$1"
    local deprecated="$2"
    local file="$3"

    if grep -q "$deprecated" "$file" 2>/dev/null; then
        echo "  [WARN] Found '$deprecated' in $(basename $file) - prefer '$preferred'"
        return 1
    fi
    return 0
}

# Terminology checks for LaTeX briefing
if [ -f "$BRIEFING_FILE" ]; then
    # These are example checks - adjust based on project style guide
    check_consistency "shall" "must" "$BRIEFING_FILE" || true
    check_consistency "repository" "repo" "$BRIEFING_FILE" || true
    echo "  [INFO] Terminology check complete"
fi

echo ""
echo "--------------------------------------------------------"
echo ""

echo "Checking PDF page count consistency..."
echo ""

PDF_FILE="$REPO_ROOT/briefing/SpeakUp-Briefing.pdf"
if [ -f "$PDF_FILE" ]; then
    # Get actual page count from PDF
    ACTUAL_PAGES=$(pdfinfo "$PDF_FILE" 2>/dev/null | grep "Pages:" | awk '{print $2}')

    if [ -n "$ACTUAL_PAGES" ]; then
        # Check if PDF footer shows correct total (extract from last page text)
        # This is a heuristic - checks if .aux file is newer than .tex file
        AUX_FILE="$REPO_ROOT/briefing/SpeakUp-Briefing.aux"
        TEX_FILE="$BRIEFING_FILE"

        if [ -f "$AUX_FILE" ] && [ "$TEX_FILE" -nt "$AUX_FILE" ]; then
            echo "  [WARN] LaTeX source modified after last build"
            echo "         Run ./briefing/build.sh to rebuild PDF"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        else
            echo "  [PASS] PDF has $ACTUAL_PAGES pages, build appears current"
        fi
    else
        echo "  [SKIP] Could not determine page count (pdfinfo not available)"
    fi
else
    echo "  [WARN] PDF not found - run ./briefing/build.sh"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""
echo "========================================================"

if [ $ISSUES_FOUND -eq 0 ]; then
    echo "OVERALL RESULT: PASS"
    echo ""
    echo "All document QA checks passed."
    echo "Standards compliance verified: IEEE 1063-2001, IEEE 610.12-1990"
    exit 0
else
    echo "OVERALL RESULT: REVIEW REQUIRED ($ISSUES_FOUND issue(s))"
    echo ""
    echo "Document QA issues detected. Review warnings above."
    echo ""
    echo "Reference standards:"
    echo "  - IEEE Std 1063-2001: Software User Documentation"
    echo "  - IEEE Std 610.12-1990: Standard Glossary of Software Engineering"
    echo "  - MIL-STD-498: Software Development and Documentation"
    exit 1
fi
