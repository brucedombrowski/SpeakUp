#!/bin/bash
#
# SpeakUp Training Materials Builder
#
# Purpose: Compile training documents and prepare video production assets
#
# Usage: ./build.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================"
echo "SpeakUp Training Materials Builder"
echo "========================================================"
echo ""

# Extract narration scripts for TTS
echo "Extracting narration scripts for text-to-speech..."
SCRIPTS_DIR="narration-scripts"
mkdir -p "$SCRIPTS_DIR"

# Extract SHORT version narration
grep -A2 "NARRATION:" Video-Storyboard.md | grep "^>" | sed 's/^> //' | sed 's/^"//' | sed 's/"$//' > "$SCRIPTS_DIR/short-narration.txt"
echo "  Extracted: $SCRIPTS_DIR/short-narration.txt"

# Extract all narration (for full version)
grep -A10 "NARRATION:" Video-Storyboard.md | grep "^>" | sed 's/^> //' | sed 's/^"//' | sed 's/"$//' > "$SCRIPTS_DIR/full-narration.txt"
echo "  Extracted: $SCRIPTS_DIR/full-narration.txt"

echo ""

# Export briefing slides as images for video production
echo "Exporting briefing slides as images..."
BRIEFING_PDF="../briefing/SpeakUp-Briefing.pdf"
SLIDES_DIR="slides-export"

if [ -f "$BRIEFING_PDF" ]; then
    mkdir -p "$SLIDES_DIR"

    # Get page count
    PAGE_COUNT=$(pdfinfo "$BRIEFING_PDF" 2>/dev/null | grep "Pages:" | awk '{print $2}')

    if [ -n "$PAGE_COUNT" ]; then
        # Export each page as PNG (high quality for video)
        pdftoppm -png -r 300 "$BRIEFING_PDF" "$SLIDES_DIR/slide"

        EXPORTED=$(ls -1 "$SLIDES_DIR"/*.png 2>/dev/null | wc -l | tr -d ' ')
        echo "  Exported $EXPORTED slides to $SLIDES_DIR/"
    else
        echo "  [WARN] Could not determine page count"
    fi
else
    echo "  [WARN] Briefing PDF not found - run ../briefing/build.sh first"
fi

echo ""
echo "========================================================"
echo "Build complete."
echo ""
echo "Outputs:"
echo "  - Video-Storyboard.md (script document)"
echo "  - narration-scripts/ (plain text for TTS)"
echo "  - slides-export/ (slide images for video production)"
echo ""
echo "Next steps for video production:"
echo "  1. Review Video-Storyboard.md for script"
echo "  2. Upload narration-scripts/*.txt to TTS service"
echo "  3. See README.md for video AI tool recommendations"
echo "========================================================"
