#!/bin/bash
#
# SpeakUp Video Generator
#
# Purpose: Generate training video from script and slides using CLI tools only
#
# Dependencies:
#   - ffmpeg (brew install ffmpeg)
#   - ImageMagick (brew install imagemagick)
#   - Optional: edge-tts (pip install edge-tts) for free TTS
#   - Optional: openai-whisper for captions
#
# Usage: ./generate-video.sh [--tts] [--version short|medium|long]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
SLIDES_DIR="slides-export"
NARRATION_DIR="narration-scripts"
OUTPUT_DIR="video-output"
VERSION="short"
USE_TTS=false
SLIDE_DURATION=5  # seconds per slide

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tts)
            USE_TTS=true
            shift
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --duration)
            SLIDE_DURATION="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

echo "========================================================"
echo "SpeakUp Video Generator"
echo "========================================================"
echo "Version: $VERSION"
echo "TTS enabled: $USE_TTS"
echo ""

# Check dependencies
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo "  [MISSING] $1 - install with: $2"
        return 1
    else
        echo "  [OK] $1"
        return 0
    fi
}

echo "Checking dependencies..."
DEPS_OK=true
check_dependency ffmpeg "brew install ffmpeg" || DEPS_OK=false
check_dependency convert "brew install imagemagick" || DEPS_OK=false

if [ "$USE_TTS" = true ]; then
    check_dependency edge-tts "pip install edge-tts" || DEPS_OK=false
fi

if [ "$DEPS_OK" = false ]; then
    echo ""
    echo "Install missing dependencies and try again."
    exit 1
fi

echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Step 1: Build assets if needed
if [ ! -d "$SLIDES_DIR" ] || [ -z "$(ls -A $SLIDES_DIR 2>/dev/null)" ]; then
    echo "Building slides..."
    ./build.sh
fi

# Step 2: Generate TTS narration if requested
AUDIO_FILE=""
if [ "$USE_TTS" = true ]; then
    echo "Generating TTS narration..."
    NARRATION_FILE="$NARRATION_DIR/${VERSION}-narration.txt"

    if [ ! -f "$NARRATION_FILE" ]; then
        NARRATION_FILE="$NARRATION_DIR/full-narration.txt"
    fi

    if [ -f "$NARRATION_FILE" ]; then
        AUDIO_FILE="$OUTPUT_DIR/narration.mp3"

        # Use edge-tts (free Microsoft TTS)
        edge-tts --voice "en-US-GuyNeural" --file "$NARRATION_FILE" --write-media "$AUDIO_FILE"

        echo "  Generated: $AUDIO_FILE"
    else
        echo "  [WARN] Narration file not found: $NARRATION_FILE"
    fi
fi

# Step 3: Create slideshow video
echo "Creating slideshow from slides..."

# Get list of slides
SLIDES=($(ls -1 "$SLIDES_DIR"/*.png 2>/dev/null | sort -V))
SLIDE_COUNT=${#SLIDES[@]}

if [ $SLIDE_COUNT -eq 0 ]; then
    echo "  [ERROR] No slides found in $SLIDES_DIR"
    exit 1
fi

echo "  Found $SLIDE_COUNT slides"

# Calculate duration
if [ -n "$AUDIO_FILE" ] && [ -f "$AUDIO_FILE" ]; then
    # Match video length to audio
    AUDIO_DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$AUDIO_FILE" | cut -d. -f1)
    SLIDE_DURATION=$(echo "scale=2; $AUDIO_DURATION / $SLIDE_COUNT" | bc)
    echo "  Audio duration: ${AUDIO_DURATION}s"
    echo "  Slide duration: ${SLIDE_DURATION}s each"
fi

# Create concat file for ffmpeg
CONCAT_FILE="$OUTPUT_DIR/concat.txt"
> "$CONCAT_FILE"

for slide in "${SLIDES[@]}"; do
    # ffmpeg concat demuxer format
    echo "file '$(cd "$SCRIPT_DIR" && pwd)/$slide'" >> "$CONCAT_FILE"
    echo "duration $SLIDE_DURATION" >> "$CONCAT_FILE"
done

# Add last slide again (ffmpeg concat quirk)
LAST_SLIDE="${SLIDES[${#SLIDES[@]}-1]}"
echo "file '$(cd "$SCRIPT_DIR" && pwd)/$LAST_SLIDE'" >> "$CONCAT_FILE"

# Create video from slides
SLIDESHOW_FILE="$OUTPUT_DIR/slideshow.mp4"
echo "  Creating slideshow video..."

ffmpeg -y -f concat -safe 0 -i "$CONCAT_FILE" \
    -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1" \
    -c:v libx264 -pix_fmt yuv420p -r 30 \
    "$SLIDESHOW_FILE" 2>/dev/null

echo "  Created: $SLIDESHOW_FILE"

# Step 4: Combine with audio if available
OUTPUT_FILE="$OUTPUT_DIR/SpeakUp-${VERSION}.mp4"

if [ -n "$AUDIO_FILE" ] && [ -f "$AUDIO_FILE" ]; then
    echo "Combining video with narration..."

    ffmpeg -y -i "$SLIDESHOW_FILE" -i "$AUDIO_FILE" \
        -c:v copy -c:a aac -shortest \
        "$OUTPUT_FILE" 2>/dev/null

    # Clean up intermediate files
    rm -f "$SLIDESHOW_FILE"
else
    mv "$SLIDESHOW_FILE" "$OUTPUT_FILE"
fi

# Clean up
rm -f "$CONCAT_FILE"

# Step 5: Generate subtitles/captions (ADA compliance)
echo "Generating subtitles for accessibility..."
SUBTITLE_FILE="$OUTPUT_DIR/SpeakUp-${VERSION}.srt"
NARRATION_FILE="$NARRATION_DIR/${VERSION}-narration.txt"

if [ ! -f "$NARRATION_FILE" ]; then
    NARRATION_FILE="$NARRATION_DIR/full-narration.txt"
fi

if [ -f "$NARRATION_FILE" ]; then
    # Generate SRT from narration text
    # Simple approach: split into timed segments based on audio duration
    AUDIO_DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$AUDIO_FILE" 2>/dev/null | cut -d. -f1)
    LINE_COUNT=$(wc -l < "$NARRATION_FILE" | tr -d ' ')

    if [ "$LINE_COUNT" -gt 0 ] && [ -n "$AUDIO_DURATION" ]; then
        SECONDS_PER_LINE=$(echo "scale=2; $AUDIO_DURATION / $LINE_COUNT" | bc)

        > "$SUBTITLE_FILE"
        INDEX=1
        CURRENT_TIME=0

        while IFS= read -r line; do
            if [ -n "$line" ]; then
                START_TIME=$(printf "%02d:%02d:%02d,000" $((CURRENT_TIME/3600)) $(((CURRENT_TIME%3600)/60)) $((CURRENT_TIME%60)))
                END_SECONDS=$(echo "$CURRENT_TIME + $SECONDS_PER_LINE" | bc | cut -d. -f1)
                END_TIME=$(printf "%02d:%02d:%02d,000" $((END_SECONDS/3600)) $(((END_SECONDS%3600)/60)) $((END_SECONDS%60)))

                echo "$INDEX" >> "$SUBTITLE_FILE"
                echo "$START_TIME --> $END_TIME" >> "$SUBTITLE_FILE"
                echo "$line" >> "$SUBTITLE_FILE"
                echo "" >> "$SUBTITLE_FILE"

                INDEX=$((INDEX + 1))
                CURRENT_TIME=$END_SECONDS
            fi
        done < "$NARRATION_FILE"

        echo "  Generated: $SUBTITLE_FILE"
    fi
fi

# Get video info
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUTPUT_FILE" | cut -d. -f1)
SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

echo ""
echo "========================================================"
echo "Video Generation Complete"
echo "========================================================"
echo ""
echo "Output: $OUTPUT_FILE"
echo "Duration: ${DURATION}s"
echo "Size: $SIZE"
echo ""
echo "Next steps:"
echo "  1. Review the video: open $OUTPUT_FILE"
echo "  2. Upload to YouTube/LinkedIn"
echo ""
echo "To add TTS narration:"
echo "  ./generate-video.sh --tts --version $VERSION"
echo ""
