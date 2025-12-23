#!/bin/bash
#
# SpeakUp Briefing Deck Builder
#
# Purpose: Compile LaTeX briefing deck to PDF
#
# Usage: ./build.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Building SpeakUp Briefing Deck..."
echo ""

# Run pdflatex twice for cross-references
/Library/TeX/texbin/pdflatex -interaction=nonstopmode SpeakUp-Briefing.tex > /dev/null 2>&1
/Library/TeX/texbin/pdflatex -interaction=nonstopmode SpeakUp-Briefing.tex > /dev/null 2>&1

# Clean up auxiliary files
rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb 2>/dev/null || true

echo "Done: SpeakUp-Briefing.pdf"
