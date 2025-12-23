# SpeakUp Training Materials

Training and marketing video production assets.

## Contents

- `Video-Storyboard.md` - Script and storyboard for three video versions (short/medium/long)
- `narration-scripts/` - Plain text narration for TTS
- `slides-export/` - Briefing slides exported as images for video production
- `build.sh` - Build script for training materials
- `generate-video.sh` - CLI video generator (no GUI needed)

## Video Versions

| Version | Duration | Audience | Platform |
|---------|----------|----------|----------|
| Short | 1-2 min | General, social | LinkedIn, Twitter/X, TikTok |
| Medium | 5-8 min | Managers | YouTube, internal comms |
| Long | 15-20 min | Practitioners | YouTube, training portals |

## Building Assets

```bash
./build.sh
```

This will:
1. Extract narration scripts for TTS
2. Export briefing slides as high-resolution images

---

## CLI Video Generation (Recommended)

Generate videos entirely from the command line—no GUI video editors needed.

```bash
# Install dependencies (one-time)
brew install ffmpeg imagemagick
pip install edge-tts

# Generate video with TTS narration
./generate-video.sh --tts --version short

# Generate silent slideshow only
./generate-video.sh --version long
```

### What It Does

1. Exports slides from the briefing PDF
2. Generates TTS narration using Microsoft Edge voices (free)
3. Combines into a video with ffmpeg
4. Outputs to `video-output/SpeakUp-{version}.mp4`

### CLI Approach: Tradeoffs

| Advantage | Limitation |
|-----------|------------|
| Fully automated, reproducible | Less control over pacing |
| No GUI software needed | TTS voice less natural than pro services |
| Free (no subscriptions) | No B-roll insertion (slides only) |
| Fast (~1 min to generate) | No avatar/presenter |
| Version controlled | Fixed transitions |
| Runs in CI/CD pipeline | Single voice throughout |

### When to Use CLI vs Web Tools

**Use CLI (`generate-video.sh`) when:**
- You want reproducible, automated builds
- Budget is zero
- Content updates frequently
- "Good enough" quality is acceptable
- You value script over GUI

**Use Web Tools (Pictory, HeyGen) when:**
- First impression matters (stakeholder demo)
- You want AI avatars or B-roll
- Higher production value needed
- One-time video (not frequently updated)

### CLI Tool Options

| Tool | Purpose | Install |
|------|---------|---------|
| `ffmpeg` | Video/audio processing | `brew install ffmpeg` |
| `imagemagick` | Image manipulation | `brew install imagemagick` |
| `edge-tts` | Free Microsoft TTS | `pip install edge-tts` |
| `whisper` | Auto-captions | `pip install openai-whisper` |
| `yt-dlp` | YouTube download | `pip install yt-dlp` |

---

## Web-Based Video AI (Alternative)

If you need higher production value or don't want to install tools:

### Easiest Path (Script → Video in 1 Hour)

**Step 1: Generate Narration**

Upload `narration-scripts/full-narration.txt` to one of these TTS services:

| Service | Cost | Notes |
|---------|------|-------|
| [ElevenLabs](https://elevenlabs.io) | Free tier available | Best quality, natural voices |
| [Play.ht](https://play.ht) | Free tier available | Good quality, easy interface |
| [Murf.ai](https://murf.ai) | Free trial | Professional voices |

Download the generated audio file (MP3 or WAV).

**Step 2: Create Video from Script**

These tools convert your script + slides into a complete video:

| Tool | What It Does | Best For |
|------|--------------|----------|
| [Pictory](https://pictory.ai) | Script → video with stock footage | Fastest, least effort |
| [InVideo](https://invideo.io) | Template-based video creation | Professional look |
| [Lumen5](https://lumen5.com) | Blog/script to video | Simple, intuitive |

**Simple workflow:**
1. Sign up for free trial
2. Paste the script from `Video-Storyboard.md`
3. Upload your TTS audio (or use their built-in voices)
4. Upload slides from `slides-export/`
5. Let AI match visuals to script
6. Export

### AI Avatar Option

Want a virtual presenter instead of slides-only?

| Service | What It Does |
|---------|--------------|
| [HeyGen](https://heygen.com) | Realistic AI avatar reads your script |
| [Synthesia](https://synthesia.io) | Professional AI presenters |
| [D-ID](https://d-id.com) | Animate a photo to speak |

Upload your script, choose an avatar, export video.

---

## Workflow Comparison

### CLI Workflow (Automated)
```
./build.sh && ./generate-video.sh --tts
    ↓
video-output/SpeakUp-short.mp4
    ↓
Upload to YouTube/LinkedIn
```

### Web Workflow (Manual)
```
./build.sh
    ↓
narration-scripts/full-narration.txt → ElevenLabs → audio.mp3
    ↓
slides-export/*.png + audio.mp3 → Pictory/InVideo → final-video.mp4
    ↓
Upload to YouTube/LinkedIn
```

---

## Copyright Compliance

- **Slides**: Original work, MIT licensed
- **B-roll**: Generate with AI or use royalty-free sources
- **Music**: Use royalty-free (YouTube Audio Library is free)
- **Memes**: Fair use for commentary, or recreate as original

### Asset Sources (Royalty-Free)

- Pexels (pexels.com) - Free stock video
- Pixabay (pixabay.com) - Free stock video/images
- Unsplash (unsplash.com) - Free images
- YouTube Audio Library - Free music/SFX

---

## YouTube Upload (Manual)

Video upload is intentionally manual to allow review before publishing.

### Pre-Upload Checklist

- [ ] Review video for accuracy and quality
- [ ] Verify subtitles (.srt) are correct
- [ ] Prepare title, description, and tags
- [ ] Decide on visibility (public/unlisted/private)

### Upload Steps

1. Go to [YouTube Studio](https://studio.youtube.com)
2. Click **Create** → **Upload videos**
3. Select `video-output/SpeakUp-short.mp4`
4. While uploading, fill in:
   - **Title**: `SpeakUp: A Systems-Engineering Workflow Demo`
   - **Description**: (see template below)
   - **Thumbnail**: Use `slides-export/slide-01.png` or create custom
5. Under **Subtitles**, upload `video-output/SpeakUp-short.srt`
6. Set visibility and publish

### Description Template

```
SpeakUp is a workflow pattern for knowledge work that captures ideas, executes with AI assistance, and maintains a complete system of record.

This briefing demonstrates:
• The problem: 8 constraints limiting productivity
• The solution: Ideation → Execution → Automatic capture
• The proof: 30 commits in 8 hours by one person

📄 Full briefing (PDF): https://github.com/brucedombrowski/SpeakUp/blob/main/briefing/SpeakUp-Briefing.pdf
📦 Repository: https://github.com/brucedombrowski/SpeakUp
📋 MIT License - free to use, modify, distribute

#productivity #systemsengineering #workflow #ai #opensource
```

### Suggested Tags

```
systems engineering, workflow, productivity, ai assisted, knowledge work,
git, version control, process improvement, open source, documentation
```

---

## Output Specifications

### YouTube
- Resolution: 1920x1080 (16:9)
- Format: MP4, H.264
- Frame rate: 30fps
- Thumbnail: 1280x720

### LinkedIn/Twitter
- Resolution: 1920x1080 or 1080x1080 (square)
- Format: MP4
- Max length: 10 min (LinkedIn), 2:20 (Twitter)

### TikTok/Shorts
- Resolution: 1080x1920 (9:16 vertical)
- Format: MP4
- Max length: 3 min (TikTok), 60s (Shorts)
