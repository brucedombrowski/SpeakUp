# Development Environment Setup

This guide documents the complete development environment for SpeakUp, including all dependencies. Designed for reproducibility and air-gapped deployment.

## Quick Start (Connected System)

```bash
# Clone repository
git clone https://github.com/brucedombrowski/SpeakUp.git
cd SpeakUp

# Install dependencies (macOS)
brew install texlive-basic poppler imagemagick ffmpeg
pip3 install edge-tts

# Build everything
./build.sh
```

## Complete Dependency List

### Core Tools

| Tool | Purpose | Install (macOS) | Version Used |
|------|---------|-----------------|--------------|
| Git | Version control | `brew install git` | 2.x |
| Python 3 | Scripting, TTS | System or `brew install python` | 3.11+ |
| Bash | Shell scripts | System | 5.x |

### Document Generation

| Tool | Purpose | Install (macOS) | Version Used |
|------|---------|-----------------|--------------|
| pdflatex | LaTeX to PDF | `brew install texlive-basic` | TeX Live 2025 |
| pdfinfo | PDF metadata | `brew install poppler` | 24.x |
| pdftoppm | PDF to images | `brew install poppler` | 24.x |

### Video Generation

| Tool | Purpose | Install (macOS) | Version Used |
|------|---------|-----------------|--------------|
| ffmpeg | Video processing | `brew install ffmpeg` | 8.0 |
| imagemagick | Image processing | `brew install imagemagick` | 7.x |
| edge-tts | Text-to-speech | `pip3 install edge-tts` | 7.2.7 |

### Verification Tools

| Tool | Purpose | Install (macOS) | Version Used |
|------|---------|-----------------|--------------|
| ClamAV | Malware scanning | `brew install clamav` | 1.x |
| shasum | File hashing | System | - |
| grep/sed/awk | Text processing | System | - |

## Air-Gapped Installation

For systems without internet access, pre-download all packages on a connected system and transfer via approved media.

### Step 1: Collect Packages (Connected System)

```bash
# Create offline package directory
mkdir -p ~/speakup-offline/{brew,pip,repo}

# Download Homebrew packages
brew fetch --deps texlive-basic poppler imagemagick ffmpeg clamav
cp -r $(brew --cache)/*.tar.gz ~/speakup-offline/brew/

# Download Python packages
pip3 download -d ~/speakup-offline/pip edge-tts

# Clone repository
git clone --mirror https://github.com/brucedombrowski/SpeakUp.git ~/speakup-offline/repo/SpeakUp.git

# Create manifest with checksums
cd ~/speakup-offline
find . -type f -exec shasum -a 256 {} \; > MANIFEST.sha256
```

### Step 2: Transfer

Transfer `~/speakup-offline/` directory via:
- Approved removable media
- Cross-domain solution (if available)
- Manual review and approval process

**Document the transfer** - who, when, what, approval reference.

### Step 3: Install (Air-Gapped System)

```bash
# Verify checksums
cd /path/to/speakup-offline
shasum -a 256 -c MANIFEST.sha256

# Install Homebrew packages from cache
for pkg in brew/*.tar.gz; do
    brew install --force-bottle "$pkg"
done

# Install Python packages
pip3 install --no-index --find-links=pip/ edge-tts

# Clone repository from local mirror
git clone repo/SpeakUp.git ~/SpeakUp
```

### Step 4: Verify Installation

```bash
cd ~/SpeakUp
./verification/scripts/run-all-scans.sh
./briefing/build.sh
```

## Version Pinning

For reproducible builds, pin exact versions:

```bash
# Record current versions
brew list --versions > brew-versions.txt
pip3 freeze > pip-requirements.txt
```

To restore:
```bash
# Homebrew (approximate - may need manual matching)
cat brew-versions.txt | xargs brew install

# Python
pip3 install -r pip-requirements.txt
```

## IDE Setup (Optional)

### VS Code

Recommended extensions:
- LaTeX Workshop (James-Yu.latex-workshop)
- Claude Code (anthropic.claude-code)
- GitLens (eamodio.gitlens)

```bash
code --install-extension James-Yu.latex-workshop
code --install-extension eamodio.gitlens
```

### JetBrains (PyCharm/IntelliJ)

- TeXiFy IDEA plugin for LaTeX
- Python plugin (bundled)

## Directory Structure

```
SpeakUp/
├── briefing/           # LaTeX briefing deck
│   ├── build.sh        # Build PDF
│   └── SpeakUp-Briefing.tex
├── training/           # Video generation
│   ├── generate-video.sh  # Create videos
│   ├── generate-visuals.sh # B-roll generator
│   ├── narration-scripts/  # TTS input text
│   ├── slides-export/      # Briefing as PNGs
│   └── visual-assets/      # Generated B-roll
├── verification/       # Security scans
│   └── scripts/        # Verification scripts
├── accounting/         # Cost tracking
│   └── calculate-costs.sh
├── src/               # Source code (DTN implementation)
├── docs/              # Additional documentation
└── build.sh           # Master build (runs all steps)
```

## Troubleshooting

### LaTeX: Missing fonts
```bash
# Install additional fonts if needed
brew install texlive-fonts-recommended
```

### edge-tts: Network required
Edge-tts requires internet for TTS. For air-gapped:
- Pre-generate audio on connected system
- Transfer MP3 files
- Use `generate-video.sh` without `--tts` flag, provide audio manually

### ffmpeg: Codec issues
```bash
# Ensure libx264 is available
ffmpeg -codecs | grep libx264
```

## Cost of Boundary Crossings

For regulated environments, every data transfer across a security boundary has costs:

| Activity | Typical Cost | Notes |
|----------|--------------|-------|
| Package approval | 1-5 days | Security review |
| Media scan | $50-200 | Per transfer event |
| Cross-domain transfer | $100-500 | If CDS available |
| Manual review | 2-8 hours | Per package |

**Minimize crossings by:**
1. Bundling all dependencies in one transfer
2. Using the MANIFEST.sha256 for verification
3. Documenting approvals for reuse
4. Maintaining an approved software baseline

## Maintenance

### Update Dependencies
```bash
# Check for updates (connected system)
brew outdated
pip3 list --outdated

# Update and re-export for air-gapped transfer
brew upgrade
pip3 install --upgrade edge-tts
```

### Verify Integrity
```bash
# Run all verification scripts
./verification/scripts/run-all-scans.sh

# Check document QA
./verification/scripts/check-document-qa.sh
```
