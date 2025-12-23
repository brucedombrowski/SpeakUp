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
VISUALS_DIR="visual-assets"
NARRATION_DIR="narration-scripts"
OUTPUT_DIR="video-output"
VERSION="short"
USE_TTS=false
USE_BROLL=false
SLIDE_DURATION=5  # seconds per slide
TTS_VOICE="en-US-AndrewNeural"  # Default: warm, confident male voice
# Alternative voices:
#   en-US-AvaNeural      - friendly, expressive female
#   en-US-BrianNeural    - casual, sincere male
#   en-US-ChristopherNeural - authoritative male

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
        --voice)
            TTS_VOICE="$2"
            shift 2
            ;;
        --broll)
            USE_BROLL=true
            shift
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
echo "B-roll enabled: $USE_BROLL"
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
        echo "  Voice: $TTS_VOICE"
        edge-tts --voice "$TTS_VOICE" --file "$NARRATION_FILE" --write-media "$AUDIO_FILE"

        echo "  Generated: $AUDIO_FILE"
    else
        echo "  [WARN] Narration file not found: $NARRATION_FILE"
    fi
fi

# Step 3: Create slideshow video with optional B-roll
echo "Creating slideshow from slides..."

# Get list of slides
SLIDES=($(ls -1 "$SLIDES_DIR"/*.png 2>/dev/null | sort -V))
SLIDE_COUNT=${#SLIDES[@]}

if [ $SLIDE_COUNT -eq 0 ]; then
    echo "  [ERROR] No slides found in $SLIDES_DIR"
    exit 1
fi

echo "  Found $SLIDE_COUNT slides"

# B-roll sequence for short version (interleaved with slides)
# Maps narration sections to visual assets
# Format: "asset_name:duration_seconds" or "slide:N" for briefing slide N
if [ "$USE_BROLL" = true ] && [ -d "$VISUALS_DIR" ]; then
    echo "  B-roll mode: Interleaving visual assets with slides"

    # Short version B-roll sequence
    # This matches the Video-Storyboard.md sections:
    # [0:00-0:15] Hook - visual assets
    # [0:15-0:45] Problem + Solution - slides 3, 5 (workflow)
    # [0:45-1:15] Proof - slide 16, commit graph
    # [1:15-1:30] CTA - QR code, repo structure
    #
    # NOTE: Use actual slides, not B-roll graphics, for diagrams that appear in deck
    # This ensures B-roll stays in sync with slide updates (see ISSUES.md ISSUE-001)
    BROLL_SEQUENCE=(
        "hook-ideas-die.png:3"
        "inbox-overload.png:3"
        "access-denied.png:3"
        "slide-03.png:6"
        "slide-05.png:10"
        "one-person.png:5"
        "commit-graph.png:6"
        "slide-16.png:6"
        "scan-results.png:5"
        "repo-structure.png:4"
        "qr-code.png:4"
    )

    # Build image list from B-roll sequence
    IMAGES=()
    DURATIONS=()
    for item in "${BROLL_SEQUENCE[@]}"; do
        ASSET=$(echo "$item" | cut -d: -f1)
        DUR=$(echo "$item" | cut -d: -f2)

        if [[ "$ASSET" == slide-* ]]; then
            # It's a briefing slide
            IMAGES+=("$SLIDES_DIR/$ASSET")
        else
            # It's a visual asset
            if [ -f "$VISUALS_DIR/$ASSET" ]; then
                IMAGES+=("$VISUALS_DIR/$ASSET")
            else
                echo "  [WARN] Missing visual asset: $ASSET"
                continue
            fi
        fi
        DURATIONS+=("$DUR")
    done
else
    # Standard slides-only mode
    IMAGES=("${SLIDES[@]}")
fi

# Calculate duration
if [ -n "$AUDIO_FILE" ] && [ -f "$AUDIO_FILE" ]; then
    AUDIO_DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$AUDIO_FILE" | cut -d. -f1)
    echo "  Audio duration: ${AUDIO_DURATION}s"

    if [ "$USE_BROLL" = true ] && [ ${#DURATIONS[@]} -gt 0 ]; then
        # B-roll mode: use predefined durations, scale to match audio
        TOTAL_BROLL_DURATION=0
        for dur in "${DURATIONS[@]}"; do
            TOTAL_BROLL_DURATION=$((TOTAL_BROLL_DURATION + dur))
        done
        SCALE_FACTOR=$(echo "scale=4; $AUDIO_DURATION / $TOTAL_BROLL_DURATION" | bc)
        echo "  B-roll total: ${TOTAL_BROLL_DURATION}s (scaling by ${SCALE_FACTOR}x to match audio)"
    else
        # Standard mode: divide evenly
        SLIDE_DURATION=$(echo "scale=2; $AUDIO_DURATION / ${#IMAGES[@]}" | bc)
        echo "  Slide duration: ${SLIDE_DURATION}s each"
    fi
fi

# Create concat file for ffmpeg
CONCAT_FILE="$OUTPUT_DIR/concat.txt"
> "$CONCAT_FILE"

if [ "$USE_BROLL" = true ] && [ ${#DURATIONS[@]} -gt 0 ]; then
    # B-roll mode with custom durations
    for i in "${!IMAGES[@]}"; do
        IMAGE="${IMAGES[$i]}"
        DUR="${DURATIONS[$i]}"
        # Scale duration to match audio
        SCALED_DUR=$(echo "scale=2; $DUR * $SCALE_FACTOR" | bc)
        echo "file '$(cd "$SCRIPT_DIR" && pwd)/$IMAGE'" >> "$CONCAT_FILE"
        echo "duration $SCALED_DUR" >> "$CONCAT_FILE"
    done
    # Add last image again (ffmpeg concat quirk)
    LAST_IMAGE="${IMAGES[${#IMAGES[@]}-1]}"
    echo "file '$(cd "$SCRIPT_DIR" && pwd)/$LAST_IMAGE'" >> "$CONCAT_FILE"
else
    # Standard slides mode
    for slide in "${IMAGES[@]}"; do
        echo "file '$(cd "$SCRIPT_DIR" && pwd)/$slide'" >> "$CONCAT_FILE"
        echo "duration $SLIDE_DURATION" >> "$CONCAT_FILE"
    done
    # Add last slide again (ffmpeg concat quirk)
    LAST_SLIDE="${IMAGES[${#IMAGES[@]}-1]}"
    echo "file '$(cd "$SCRIPT_DIR" && pwd)/$LAST_SLIDE'" >> "$CONCAT_FILE"
fi

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
MUSIC_FILE="$OUTPUT_DIR/background-music.mp3"

if [ -n "$AUDIO_FILE" ] && [ -f "$AUDIO_FILE" ]; then
    echo "Combining video with narration..."

    # Check if background music exists
    if [ -f "$MUSIC_FILE" ]; then
        echo "  Mixing in background music..."
        # Mix narration (full volume) with background music (70% volume)
        # Music should be clearly audible but not compete with narration
        ffmpeg -y -i "$SLIDESHOW_FILE" -i "$AUDIO_FILE" -i "$MUSIC_FILE" \
            -filter_complex "[1:a]volume=1.0[narration];[2:a]volume=0.7[music];[narration][music]amix=inputs=2:duration=first[aout]" \
            -map 0:v -map "[aout]" \
            -c:v copy -c:a aac -shortest \
            "$OUTPUT_FILE" 2>/dev/null
    else
        # No background music, just narration
        ffmpeg -y -i "$SLIDESHOW_FILE" -i "$AUDIO_FILE" \
            -c:v copy -c:a aac -shortest \
            "$OUTPUT_FILE" 2>/dev/null
    fi

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

# Try Whisper for Netflix-quality word-level timing
# Falls back to simple line-based timing if Whisper unavailable
if command -v whisper &> /dev/null && [ -f "$AUDIO_FILE" ]; then
    echo "  Using Whisper for word-level subtitle timing..."

    # Whisper outputs to current directory, so we cd there
    pushd "$OUTPUT_DIR" > /dev/null
    whisper "../$AUDIO_FILE" --model tiny --language en --output_format srt --word_timestamps True 2>/dev/null

    # Whisper names output after input file
    WHISPER_OUTPUT="narration.srt"
    if [ -f "$WHISPER_OUTPUT" ]; then
        mv "$WHISPER_OUTPUT" "SpeakUp-${VERSION}.srt"
        echo "  Generated: $SUBTITLE_FILE (Whisper word-level timing)"
    fi
    popd > /dev/null
else
    echo "  Whisper not found, using simple timing (install: pip install openai-whisper)"

    NARRATION_FILE="$NARRATION_DIR/${VERSION}-narration.txt"
    if [ ! -f "$NARRATION_FILE" ]; then
        NARRATION_FILE="$NARRATION_DIR/full-narration.txt"
    fi

    if [ -f "$NARRATION_FILE" ]; then
        # Simple approach: split text into ~10-word chunks with estimated timing
        AUDIO_DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$AUDIO_FILE" 2>/dev/null)

        # Split into chunks of ~10 words each for better readability
        > "$SUBTITLE_FILE"
        INDEX=1

        # Read all text, split into words, group into chunks
        ALL_TEXT=$(cat "$NARRATION_FILE" | tr '\n' ' ')
        WORD_COUNT=$(echo "$ALL_TEXT" | wc -w | tr -d ' ')
        WORDS_PER_CHUNK=10
        CHUNK_COUNT=$(( (WORD_COUNT + WORDS_PER_CHUNK - 1) / WORDS_PER_CHUNK ))
        SECONDS_PER_CHUNK=$(echo "scale=3; $AUDIO_DURATION / $CHUNK_COUNT" | bc)

        CURRENT_TIME=0
        WORD_INDEX=0

        for word in $ALL_TEXT; do
            if [ $((WORD_INDEX % WORDS_PER_CHUNK)) -eq 0 ]; then
                # Start new chunk
                if [ $WORD_INDEX -gt 0 ]; then
                    # Close previous chunk
                    echo "" >> "$SUBTITLE_FILE"
                fi

                # Calculate times
                START_SEC=$(echo "scale=3; $CURRENT_TIME" | bc)
                END_SEC=$(echo "scale=3; $CURRENT_TIME + $SECONDS_PER_CHUNK" | bc)

                # Format as SRT timestamp (HH:MM:SS,mmm)
                START_H=$(echo "$START_SEC / 3600" | bc)
                START_M=$(echo "($START_SEC % 3600) / 60" | bc)
                START_S=$(echo "$START_SEC % 60" | bc)
                START_MS=$(echo "($START_SEC - ${START_S%.*}) * 1000" | bc | cut -d. -f1)

                END_H=$(echo "$END_SEC / 3600" | bc)
                END_M=$(echo "($END_SEC % 3600) / 60" | bc)
                END_S=$(echo "$END_SEC % 60" | bc)
                END_MS=$(echo "($END_SEC - ${END_S%.*}) * 1000" | bc | cut -d. -f1)

                START_TIME=$(printf "%02d:%02d:%02d,%03d" $START_H $START_M ${START_S%.*} ${START_MS:-0})
                END_TIME=$(printf "%02d:%02d:%02d,%03d" $END_H $END_M ${END_S%.*} ${END_MS:-0})

                echo "$INDEX" >> "$SUBTITLE_FILE"
                echo "$START_TIME --> $END_TIME" >> "$SUBTITLE_FILE"

                INDEX=$((INDEX + 1))
                CURRENT_TIME=$END_SEC
            fi

            # Append word to current line (with line break at ~42 chars for readability)
            if [ $((WORD_INDEX % WORDS_PER_CHUNK)) -lt 5 ]; then
                echo -n "$word " >> "$SUBTITLE_FILE"
            else
                # Second line of subtitle
                if [ $((WORD_INDEX % WORDS_PER_CHUNK)) -eq 5 ]; then
                    echo "" >> "$SUBTITLE_FILE"  # Line break
                fi
                echo -n "$word " >> "$SUBTITLE_FILE"
            fi

            WORD_INDEX=$((WORD_INDEX + 1))
        done

        # Close final chunk
        echo "" >> "$SUBTITLE_FILE"
        echo "" >> "$SUBTITLE_FILE"

        echo "  Generated: $SUBTITLE_FILE (chunked timing, ${WORDS_PER_CHUNK} words/subtitle)"
    fi
fi

# Step 6: Burn subtitles into video (cleaner than VLC overlay)
echo "Burning subtitles into video..."
FINAL_OUTPUT="$OUTPUT_DIR/SpeakUp-${VERSION}-subtitled.mp4"

if [ -f "$SUBTITLE_FILE" ]; then
    # Burn subtitles with dark background box for visibility on any slide
    # BorderStyle=4 = opaque box behind text
    # BackColour = semi-transparent black background
    ffmpeg -y -i "$OUTPUT_FILE" -vf "subtitles=$SUBTITLE_FILE:force_style='FontSize=20,FontName=Helvetica,PrimaryColour=&Hffffff,OutlineColour=&H000000,BackColour=&H80000000,Outline=1,Shadow=0,BorderStyle=4,MarginV=40'" \
        -c:a copy "$FINAL_OUTPUT" 2>/dev/null

    if [ -f "$FINAL_OUTPUT" ]; then
        echo "  Created: $FINAL_OUTPUT (with burned-in subtitles)"
        # Replace original with subtitled version
        mv "$FINAL_OUTPUT" "$OUTPUT_FILE"
        # Move .srt to prevent VLC auto-loading (keep for YouTube upload)
        mv "$SUBTITLE_FILE" "$OUTPUT_DIR/captions-for-upload.srt"
        echo "  Renamed SRT to captions-for-upload.srt (for YouTube, not VLC)"
    fi
fi

# Get video info
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUTPUT_FILE" | cut -d. -f1)
SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
BUILD_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Write metadata file for provenance
cat > "$OUTPUT_DIR/video-metadata.json" << METADATA
{
  "filename": "SpeakUp-${VERSION}.mp4",
  "version": "${VERSION}",
  "generated": "${BUILD_TIMESTAMP}",
  "duration_seconds": ${DURATION},
  "size": "${SIZE}",
  "tts_enabled": ${USE_TTS},
  "tts_voice": "${TTS_VOICE}",
  "broll_enabled": ${USE_BROLL},
  "generator": "SpeakUp/training/generate-video.sh"
}
METADATA

echo ""
echo "========================================================"
echo "Video Generation Complete"
echo "========================================================"
echo ""
echo "Output: $OUTPUT_FILE"
echo "Generated: $BUILD_TIMESTAMP"
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

# Auto-play in VLC if available (subtitles are burned in, no overlay needed)
if command -v vlc &> /dev/null; then
    echo "Opening video in VLC..."
    vlc --volume 128 "$OUTPUT_FILE" &
elif [ -d "/Applications/VLC.app" ]; then
    echo "Opening video in VLC..."
    open -a VLC "$OUTPUT_FILE"
    sleep 1
    osascript -e 'tell application "VLC" to set audio volume to 128' 2>/dev/null || true
else
    echo "Opening video in default player..."
    open "$OUTPUT_FILE"
fi
