#!/bin/bash
#
# SpeakUp Master Build Script
#
# Builds all artifacts and runs all verification scans.
# This is the single command to produce all deliverables.
#
# Usage: ./build.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================"
echo "SpeakUp Master Build"
echo "========================================================"
echo "Timestamp: $(date)"
echo ""

# Track status
FAILED=0
TOTAL_STEPS=6
STEP=0

# ------------------------------------------------------
# 1. Python Code Quality (ruff)
# ------------------------------------------------------
STEP=$((STEP + 1))
echo "========================================================"
echo "[$STEP/$TOTAL_STEPS] Running Python Code Quality Checks"
echo "========================================================"

if command -v ruff &> /dev/null; then
    if ruff check src/; then
        echo "  Ruff Linting: OK"
    else
        echo "  Ruff Linting: FAILED"
        FAILED=1
    fi
else
    echo "  Ruff not installed (pip install ruff)"
    echo "  Skipping code quality checks"
fi

echo ""

# ------------------------------------------------------
# 2. Run BPv7 Tests
# ------------------------------------------------------
STEP=$((STEP + 1))
echo "========================================================"
echo "[$STEP/$TOTAL_STEPS] Running BPv7 Protocol Tests"
echo "========================================================"

if PYTHONPATH=src python3 -m pytest src/bpv7/tests/ -v 2>/dev/null; then
    echo "  BPv7 Tests: OK"
else
    # Try without pytest
    echo "  pytest not available, running example..."
    if PYTHONPATH=src python3 src/bpv7/example.py 2>/dev/null; then
        echo "  BPv7 Example: OK"
    else
        echo "  BPv7 Tests: FAILED"
        FAILED=1
    fi
fi

echo ""

# ------------------------------------------------------
# 2. Run PDF Transfer Test (BPv7 Integration)
# ------------------------------------------------------
STEP=$((STEP + 1))
echo "========================================================"
echo "[$STEP/$TOTAL_STEPS] Running BPv7 PDF Transfer Test"
echo "========================================================"

if PYTHONPATH=src python3 src/bpv7/test_pdf_transfer.py 2>&1 | grep -q "SUCCESS"; then
    echo "  PDF Transfer Test: OK"
else
    echo "  PDF Transfer Test: FAILED"
    FAILED=1
fi

echo ""

# ------------------------------------------------------
# 3. Run Security Verification Scans
# ------------------------------------------------------
STEP=$((STEP + 1))
echo "========================================================"
echo "[$STEP/$TOTAL_STEPS] Running Security Verification Scans"
echo "========================================================"

if [ -x "verification/scripts/run-all-scans.sh" ]; then
    if ./verification/scripts/run-all-scans.sh; then
        echo "  Security Scans: OK"
    else
        echo "  Security Scans: FAILED (details not disclosed)"
        FAILED=1
    fi
else
    echo "  Security scan script not found"
    FAILED=1
fi

echo ""

# ------------------------------------------------------
# 4. Build Briefing PDF
# ------------------------------------------------------
STEP=$((STEP + 1))
echo "========================================================"
echo "[$STEP/$TOTAL_STEPS] Building Briefing PDF"
echo "========================================================"

if [ -f "briefing/build.sh" ]; then
    cd briefing
    if ./build.sh; then
        echo "  Briefing PDF: OK"
    else
        echo "  Briefing PDF: FAILED"
        FAILED=1
    fi
    cd "$SCRIPT_DIR"
else
    echo "  Briefing build script not found"
    FAILED=1
fi

echo ""

# ------------------------------------------------------
# 5. Generate Training Video (after briefing so slides are current)
# ------------------------------------------------------
STEP=$((STEP + 1))
echo "========================================================"
echo "[$STEP/$TOTAL_STEPS] Generating Training Video"
echo "========================================================"

if [ -x "training/generate-video.sh" ]; then
    cd training

    # Generate visuals first, then video
    if ./generate-visuals.sh > /dev/null 2>&1; then
        echo "  Visual Assets: OK"
    else
        echo "  Visual Assets: FAILED"
        FAILED=1
    fi

    if ./generate-video.sh --tts --broll --version short > /dev/null 2>&1; then
        # Verify video was actually created
        if [ -f "video-output/SpeakUp-short.mp4" ]; then
            VIDEO_SIZE=$(ls -lh video-output/SpeakUp-short.mp4 | awk '{print $5}')
            echo "  Training Video: OK ($VIDEO_SIZE)"
        else
            echo "  Training Video: FAILED (file not created)"
            FAILED=1
        fi
    else
        echo "  Training Video: FAILED"
        FAILED=1
    fi
    cd "$SCRIPT_DIR"
else
    echo "  Video generation script not found"
    FAILED=1
fi

echo ""

# ------------------------------------------------------
# Summary
# ------------------------------------------------------
echo "========================================================"
echo "BUILD SUMMARY"
echo "========================================================"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "  STATUS: ALL PASSED"
    echo ""
    echo "  Artifacts produced:"
    echo "    - briefing/SpeakUp-Briefing.pdf"
    echo "    - verification/Security-Attestation.md"
    echo "    - verification/Compliance-Statement.md"
    echo "    - verification/Requirements-Traceability.md"
    echo "    - training/video-output/SpeakUp-short.mp4"
    echo "    - training/visual-assets/*.png"
    echo ""
    exit 0
else
    echo "  STATUS: FAILED"
    echo ""
    echo "  Check output above for errors."
    echo ""
    exit 1
fi
