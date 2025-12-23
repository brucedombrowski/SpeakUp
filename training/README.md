# SpeakUp Training Materials

Training and marketing video production assets.

## Contents

- `Video-Storyboard.md` - Script and storyboard for three video versions (short/medium/long)
- `narration-scripts/` - Plain text narration for TTS
- `slides-export/` - Briefing slides exported as images for video production
- `visual-assets/` - B-roll graphics and supplementary visuals
- `build.sh` - Build script for training materials
- `generate-video.sh` - CLI video generator (no GUI needed)
- `generate-visuals.sh` - Generate B-roll and supplementary visuals

## Video Versions

| Version | Duration | Audience | Platform |
|---------|----------|----------|----------|
| Short | 1-2 min | General, social | LinkedIn, Twitter/X, TikTok |
| Medium | 5-8 min | Managers | YouTube, internal comms |
| Long | 15-20 min | Practitioners | YouTube, training portals |
| Conference | 45-60 min | Technical audience | Conferences, meetups |

### Presentation Formats by Venue

| Format | Duration | Structure | Venue |
|--------|----------|-----------|-------|
| **Lightning Talk** | 5-10 min | Hook + core concept + CTA | Meetups, unconferences |
| **Lunch & Learn** | 30 min | Problem + Solution + Demo + Q&A | Internal teams, brown bags |
| **Conference Talk** | 45 min | Full deck + live demo + Q&A (15 min) | Tech conferences |
| **Workshop** | 2-4 hours | Hands-on setup + exercises | Training sessions |
| **Keynote** | 60 min | Story arc + vision + demo + Q&A | Major conferences |

### Lunch & Learn Format (30 min)

Perfect for internal teams and brown bag sessions:

| Time | Content |
|------|---------|
| 0:00-0:05 | Hook + Problem statement |
| 0:05-0:15 | Solution overview (workflow diagram) |
| 0:15-0:22 | Live demo or video walkthrough |
| 0:22-0:25 | Results / proof points |
| 0:25-0:30 | Q&A + next steps |

**Key**: Keep it conversational. Pause for questions. This is about dialogue, not presentation.

### Conference Talk Format (45 min + 15 min Q&A)

For formal conference presentations in a 1-hour block:

| Time | Content |
|------|---------|
| 0:00-0:05 | Hook + personal story |
| 0:05-0:15 | Problem deep-dive (the 8 constraints) |
| 0:15-0:25 | Solution architecture (workflow, tools) |
| 0:25-0:35 | Live demo (ideation → execution → commit) |
| 0:35-0:42 | Results + verification evidence |
| 0:42-0:45 | Call to action + resources |
| 0:45-1:00 | Q&A |

**Includes**:
- Live demo: Real-time workflow demonstration
- Code walkthrough: DTN implementation deep-dive
- Audience interaction: Polls, questions throughout

### Target Venues

| Category | Examples |
|----------|----------|
| **Developer** | Strange Loop, GOTO, local meetups, PyCon, JSConf |
| **Systems Engineering** | INCOSE, IEEE conferences, SAE events |
| **Government/Defense** | AFCEA, DISA symposiums, GovTech |
| **Open Source** | FOSDEM, All Things Open, Linux Foundation events |
| **Enterprise** | Internal tech talks, vendor briefings, customer demos |

*Note: Conference materials are in planning. Current priority is short/medium videos for social distribution.*

---

## Visual Assets

Pre-generated visuals for B-roll and supplementary content:

```bash
./generate-visuals.sh
```

### Available Assets (in `visual-assets/`)

| Asset | Purpose | File |
|-------|---------|------|
| Hook opener | "Your ideas are dying" | `hook-ideas-die.png` |
| Inbox overload | Pain point: 10,847 unread | `inbox-overload.png` |
| Access denied | Pain point: blocked tools | `access-denied.png` |
| Workflow diagram | Ideation → Execution → Record | `workflow-diagram.png` |
| Commit graph | Proof: 42 commits in 2 days | `commit-graph.png` |
| Scan results | Verification evidence | `scan-results.png` |
| Build success | Satisfaction payoff | `build-success.png` |
| Repo structure | GitHub proof shot | `repo-structure.png` |
| One person stat | "1 person, 30 commits" | `one-person.png` |
| QR code | Call to action | `qr-code.png` |

### The Vibe: Coffee Shop Chad, Not Basement Hacker

**Wrong vibe**: Hooded figure in dark room, 100 monitors, Matrix terminals scrolling

**Right vibe**: Relaxed person at coffee shop, dog at their feet, single laptop, getting things done

The point is **capability without drama**. SpeakUp isn't about grinding—it's about working smart in comfortable environments. The aesthetic should feel:

- Approachable, not intimidating
- Calm, not frantic
- Confident, not tryhard
- Real, not performative

When sourcing B-roll or filming custom footage:
- Natural light (coffee shop, home office, patio)
- Single screen (laptop, not multi-monitor battlestation)
- Casual dress (not suit, not hoodie-hacker)
- Optional: pet in frame (dogs are engagement gold)

### Scrolling Terminal Effect

For dynamic visuals showing real work happening:

```bash
# Record actual terminal session with asciinema
brew install asciinema
asciinema rec terminal-demo.cast

# Convert to GIF or video
brew install agg
agg terminal-demo.cast terminal-demo.gif
```

Show real commands, real output. Not fake "hacking" nonsense—actual git commits, actual test runs, actual builds.

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

### TTS Voice Selection (Design Decision)

**Current choice: edge-tts (Microsoft Azure Neural Voices)**

| Decision Factor | Analysis |
|-----------------|----------|
| **Why edge-tts** | Free, no API key, works offline after model download, 17 natural-sounding English voices |
| **Alternatives considered** | Piper TTS (dependency issues on Python 3.14), Coqui TTS (requires Python <3.13), macOS `say` (robotic) |
| **Trade-off** | Requires internet for first use; voices are "good enough" but not ElevenLabs quality |
| **Future option** | When Piper/Coqui support Python 3.14+, consider switching for fully offline operation |

**Recommended voices (in order of naturalness):**

| Voice | Style | Best For |
|-------|-------|----------|
| `en-US-AndrewNeural` | Warm, confident | Professional narration |
| `en-US-BrianNeural` | Casual, sincere | Conversational content |
| `en-US-AvaNeural` | Friendly, expressive | Engaging presentations |
| `en-US-ChristopherNeural` | Authoritative | Technical content |
| `en-US-GuyNeural` | Passionate | (current default, more robotic) |

To change voice, edit `generate-video.sh` line with `--voice` parameter.

**Test voices locally:**
```bash
edge-tts --voice "en-US-AndrewNeural" --text "Test message" --write-media test.mp3
afplay test.mp3
```

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

## Video Engagement: YouTube Creator Wisdom

**SpeakUp is for everyone**—systems engineers, dubstep DJs, content creators, and everyone in between. The principles below apply whether you're explaining DTN protocols or drop bass frequencies.

### The First 7 Seconds Rule

**You have 7 seconds before viewers decide to stay or leave.**

| Technique | What It Means | Example |
|-----------|---------------|---------|
| **Pattern interrupt** | Break expectations immediately | Start mid-action, not with "Hey guys..." |
| **Open with outcome** | Show the result, then explain how | "30 commits in 8 hours. Here's how." |
| **Promise value** | Tell them what they'll gain | "After this, you'll never lose an idea again." |
| **Create curiosity gap** | Hint at something surprising | "Most workflows are broken. Yours probably is too." |

**MrBeast's rule**: If nothing interesting happens in 5 seconds, 23% fewer viewers will watch the next 30 seconds.

### Retention Mechanics

| Principle | Implementation |
|-----------|----------------|
| **Visual change every 2-3 sec** | Cut, zoom, pan, graphic overlay—something must move |
| **"Crazy progression"** | Don't dwell; keep revealing new information |
| **Tension → Payoff** | Build anticipation, then deliver satisfaction |
| **Avoid "the dip"** | Middle of video = highest dropout; put a hook there |
| **End with curiosity** | "But there's one more thing..." keeps them for the next video |

### The "Too Many DJs" Problem

> *"There are too many DJs, but not enough people making music."*
> — Every producer, everywhere

Same applies to content: **lots of people talking about productivity, few actually demonstrating it**.

SpeakUp differentiates by showing receipts:
- 42 commits in 2 days (verifiable)
- Working code, not slides about code
- Open source—inspect the git history yourself

**Don't just claim expertise. Prove it.**

### Hook Templates That Work

| Type | Template | SpeakUp Example |
|------|----------|-----------------|
| **Contrarian** | "Everything you know about X is wrong" | "Your workflow is killing your best ideas." |
| **Specific number** | "X ways to..." or "I did X in Y time" | "30 commits in 8 hours." |
| **Us vs Them** | "Why most people fail at X" | "Why most ideas die before execution." |
| **Curiosity** | "The secret to X that nobody talks about" | "The one tool that changed how I work." |
| **Proof** | "I tested X so you don't have to" | "I built this entire system to prove a point." |

### Platform-Specific Strategies

| Platform | Optimal Length | Hook Window | Key Tactic |
|----------|---------------|-------------|------------|
| **YouTube** | 5-10 min (31.5% avg retention) | 7 seconds | Chapters, end screens |
| **LinkedIn** | 1-3 min | 3 seconds | Text overlay (many watch muted) |
| **TikTok** | 15-60 sec | 1 second | Vertical, face-to-camera |
| **Twitter/X** | 30-140 sec | 2 seconds | Subtitles mandatory |

### The Authenticity Paradox

Highly-produced content performs worse than authentic content for educational material.

| High Production | Authentic/Raw |
|-----------------|---------------|
| Feels like an ad | Feels like a conversation |
| Viewers skeptical | Viewers trust |
| High cost | Low/zero cost |
| Slow iteration | Fast iteration |

**The sweet spot**: Professional enough to be credible, raw enough to be trusted.

CLI-generated videos hit this balance: they're polished but clearly not million-dollar productions.

### Thumbnail Psychology

| Element | Why It Works |
|---------|--------------|
| **Face with emotion** | Humans are wired to notice faces |
| **Contrasting colors** | Stands out in crowded feed |
| **3 words max** | Readable at thumbnail size |
| **Curiosity gap** | Image + title don't fully explain = click to find out |

### Keep It Fun (Self-Governance Clause)

This documentation exists to help, not to create bureaucracy. If something here makes video creation feel like a chore:

1. Ignore that part
2. Ship something
3. Iterate based on actual feedback

**The best video is the one that exists.** Perfect is the enemy of shipped.

### Sponsors: Our Sugar Daddies

> *"This video is sponsored by..."*

Even open-source projects need resources. Sponsorship tiers for SpeakUp-style content:

| Tier | Integration | Rate (typical) | Example |
|------|-------------|----------------|---------|
| **Pre-roll** | 60-90 sec at start | $50-500/1k views | "This video is brought to you by..." |
| **Mid-roll** | 30-60 sec at natural break | $30-300/1k views | "Speaking of workflows, NordVPN..." |
| **Post-roll** | 15-30 sec at end | $20-100/1k views | "Thanks to [sponsor] for supporting" |
| **Integrated** | Woven into content | $100-1k/1k views | Tool demo as part of tutorial |

**Open Source Sponsor Alignment**:

| Good Fit | Why |
|----------|-----|
| Developer tools | Audience overlap |
| Cloud providers | Hosting for OSS |
| Learning platforms | Educational content |
| Git hosting | Version control focus |

| Poor Fit | Why |
|----------|-----|
| VPN (generic) | Not relevant to workflow content |
| Mobile games | Audience mismatch |
| Anything deceptive | Destroys trust (the only real asset) |

**The Authenticity Rule**: Only sponsor things you'd actually use. Your credibility is worth more than any single deal.

**Disclosure**: Always disclose sponsorships clearly. FTC requires it. Audiences respect it.

### GitHub Sponsors / Patreon

For ongoing support without per-video deals:

| Platform | Cut | Best For |
|----------|-----|----------|
| **GitHub Sponsors** | 0% (GitHub pays fees) | Developer projects |
| **Patreon** | 5-12% | General creators |
| **Ko-fi** | 0-5% | One-time tips |
| **Open Collective** | 10% | Transparent OSS funding |

### Resources

- [MrBeast's leaked training doc](https://www.scribd.com/document/696162330/MrBeast-Guides) - Actual internal guidelines
- [VidIQ YouTube Analytics](https://vidiq.com) - Free tier for optimization
- [YouTube Creator Academy](https://creatoracademy.youtube.com) - Official best practices

---

## Quality Standards

**Benchmark**: Netflix, Disney, top YouTubers.

We aim for professional, industry-standard quality in all outputs. The bar is high—but we're realistic about resource constraints and document the trade-offs transparently.

### Quality Hierarchy

| Category | Benchmark | Our Target | Gap Analysis |
|----------|-----------|------------|--------------|
| **Video quality** | Netflix 4K HDR | 1080p H.264 | Acceptable—most social platforms compress anyway |
| **TTS narration** | Professional VO artist | Microsoft Neural Voices | 80% quality at 0% cost—documented trade-off |
| **Subtitles** | Netflix word-by-word sync | Chunked 10-word blocks | See "Subtitle Constraints" below |
| **Transitions** | Disney-level motion graphics | Simple cuts, Ken Burns | Acceptable for educational content |
| **Music** | Licensed orchestral scores | Royalty-free or silence | Acceptable—music optional for tech content |

### Subtitle Constraints (Known Limitation)

**What Netflix does**: Word-by-word highlighting synchronized to speech, karaoke-style reveal as words are spoken.

**What we can do with free tools**:
- **With Whisper** (`pip install openai-whisper`): Near-Netflix quality word-level timing
- **Without Whisper**: Chunked 10-word blocks with estimated timing

| Approach | Quality | Cost | Automation |
|----------|---------|------|------------|
| **Whisper** | Excellent word-level sync | Free (local GPU helps) | Fully automated |
| **Chunked timing** | Good, readable | Free | Fully automated |
| **Manual SRT edit** | Perfect | Time-expensive | Manual |
| **Rev.com / Descript** | Professional | $1-2/min | Semi-automated |

**Current implementation**: Whisper if available, otherwise 10-word chunks with proportional timing.

**To upgrade**: Install Whisper for word-level timing:
```bash
pip install openai-whisper
# Requires ~1GB model download on first run
```

### Resource Constraints → Automation

Every constraint we identify gets automated away:

| Constraint | Manual Approach | Automated Solution |
|------------|-----------------|-------------------|
| No VO artist | Record yourself | `edge-tts` with neural voices |
| No video editor | Learn Premiere | `ffmpeg` slideshow + concat |
| No subtitle editor | Manual .srt editing | `whisper` or chunked generation |
| No graphic designer | Hire someone | `imagemagick` for visuals |
| No hosting | Pay for CDN | GitHub + YouTube (free) |

**Philosophy**: If it's a recurring task, automate it. If it's a one-time task, document it.

### Quality Gap Reporting

When we can't meet Netflix/Disney standards, we:
1. **Document the gap** - What's the delta between our output and the benchmark?
2. **Explain the constraint** - Why can't we close the gap? (Cost, time, tooling)
3. **Propose the solution** - What would it take to close the gap?
4. **Track for automation** - Can this be automated away later?

| Gap | Current State | To Close Gap | Priority |
|-----|---------------|--------------|----------|
| Word-by-word subtitles | 10-word chunks | Install Whisper | High |
| 4K video | 1080p | Just change ffmpeg params | Low |
| Pro VO artist | Neural TTS | Pay for ElevenLabs | Medium |
| Motion graphics | Static cuts | After Effects / Remotion | Low |
| Background music | Silent | License from Epidemic Sound | Low |

This table becomes our roadmap. High-priority gaps get addressed first.

### When to Bring in SME Help

**Current state**: The video is functional and communicates the message, but lacks professional polish that's difficult to articulate without domain expertise.

**The feedback wall**: At some point, you hit a limit where you can see something isn't quite right, but can't describe *what* to fix. This is where subject matter experts provide outsized value.

| Domain | SME Role | What They'd Evaluate |
|--------|----------|---------------------|
| **Video editing** | Editor / Motion designer | Pacing, transitions, visual rhythm |
| **Audio** | Sound engineer | Levels, EQ, compression, room tone |
| **Voice** | VO director | Pacing, emphasis, emotional delivery |
| **Graphics** | Motion graphics artist | Title cards, lower thirds, animations |
| **Captions** | Accessibility specialist | Timing, formatting, reading speed |

**How to engage SMEs effectively**:
1. Show them the current output (not just describe it)
2. Ask "what feels off?" rather than "is this good?"
3. Request specific, actionable feedback
4. Ask them to demonstrate, not just explain

**Cost-effective SME options**:
- Fiverr/Upwork for one-time reviews ($50-200)
- YouTube creator communities (free peer feedback)
- Local film school students (portfolio building)
- r/VideoEditing, r/audioengineering (free community feedback)

**The SpeakUp principle**: Document what you don't know. The gap between "good enough" and "professional" is learnable, but requires feedback from people who've crossed that gap themselves.

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
