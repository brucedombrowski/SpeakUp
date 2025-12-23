#!/bin/bash
#
# SpeakUp YouTube Upload Helper
#
# Purpose: Prepare and guide manual YouTube upload
# Note: Does NOT auto-upload (intentional - requires human review)
#
# Usage: ./upload-youtube.sh [video-file]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VIDEO_FILE="${1:-video-output/SpeakUp-short.mp4}"
SUBTITLE_FILE="${VIDEO_FILE%.mp4}.srt"

echo "========================================================"
echo "SpeakUp YouTube Upload Helper"
echo "========================================================"
echo ""

# Check if video exists
if [ ! -f "$VIDEO_FILE" ]; then
    echo "ERROR: Video file not found: $VIDEO_FILE"
    echo ""
    echo "Generate video first with:"
    echo "  ./generate-video.sh --tts --version short"
    exit 1
fi

# Get video info
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO_FILE" 2>/dev/null | cut -d. -f1)
SIZE=$(du -h "$VIDEO_FILE" | cut -f1)
RESOLUTION=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$VIDEO_FILE" 2>/dev/null)

echo "Video Details:"
echo "  File:       $VIDEO_FILE"
echo "  Duration:   ${DURATION}s"
echo "  Size:       $SIZE"
echo "  Resolution: $RESOLUTION"
echo ""

if [ -f "$SUBTITLE_FILE" ]; then
    echo "  Subtitles:  $SUBTITLE_FILE (ADA compliant)"
else
    echo "  Subtitles:  Not found (generate with --tts flag)"
fi

echo ""
echo "========================================================"
echo "PRE-UPLOAD CHECKLIST"
echo "========================================================"
echo ""
echo "Before uploading, verify:"
echo "  [ ] Video plays correctly and audio is clear"
echo "  [ ] All slides are readable"
echo "  [ ] Subtitles match narration (if applicable)"
echo "  [ ] No sensitive information visible"
echo "  [ ] You're ready for this to be public"
echo ""

read -p "Open video for review? [Y/n] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    open "$VIDEO_FILE"
    echo ""
    read -p "Press Enter after reviewing video..."
fi

echo ""
echo "========================================================"
echo "UPLOAD INFORMATION"
echo "========================================================"
echo ""
echo "Title:"
echo "  SpeakUp: A Systems-Engineering Workflow Demo"
echo ""
echo "Description:"
cat << 'DESCRIPTION'
SpeakUp is a workflow pattern for knowledge work that captures ideas, executes with AI assistance, and maintains a complete system of record.

This briefing demonstrates:
• The problem: 8 constraints limiting productivity
• The solution: Ideation → Execution → Automatic capture
• The proof: 30 commits in 8 hours by one person

📄 Full briefing (PDF): https://github.com/brucedombrowski/SpeakUp/blob/main/briefing/SpeakUp-Briefing.pdf
📦 Repository: https://github.com/brucedombrowski/SpeakUp
📋 MIT License - free to use, modify, distribute

#productivity #systemsengineering #workflow #ai #opensource
DESCRIPTION
echo ""
echo "Tags:"
echo "  systems engineering, workflow, productivity, ai assisted,"
echo "  knowledge work, git, version control, process improvement,"
echo "  open source, documentation"
echo ""
echo "Thumbnail suggestion:"
echo "  slides-export/slide-01.png"
echo ""

echo "========================================================"
echo "READY TO UPLOAD"
echo "========================================================"
echo ""
echo "Files to upload:"
echo "  1. Video:     $VIDEO_FILE"
if [ -f "$SUBTITLE_FILE" ]; then
    echo "  2. Subtitles: $SUBTITLE_FILE"
fi
echo ""

read -p "Open YouTube Studio? [Y/n] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    open "https://studio.youtube.com/channel/UC/videos/upload"
    echo ""
    echo "YouTube Studio opened. Follow the upload steps in README.md"
fi

echo ""
echo "========================================================"
echo "POST-UPLOAD"
echo "========================================================"
echo ""
echo "After uploading:"
echo "  1. Copy the YouTube URL"
echo "  2. Update briefing/SpeakUp-Briefing.tex with actual URL"
echo "  3. Rebuild: ./briefing/build.sh"
echo "  4. Commit and push changes"
echo ""
echo "Done."
