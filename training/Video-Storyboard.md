# SpeakUp Video Storyboard

**Training Material Generation Script**

Bruce Dombrowski | December 2025

---

## Overview

This document provides the script and storyboard for SpeakUp training videos at three depth levels. Each version is a superset of the shorter versions, allowing consistent messaging across formats.

| Version | Duration | Audience | Platform |
|---------|----------|----------|----------|
| Short | 1-2 min | General, social media | LinkedIn, Twitter/X, TikTok |
| Medium | 5-8 min | Managers, decision-makers | YouTube, internal comms |
| Long | 15-20 min | Practitioners, evaluators | YouTube, training portals |

### Visual Language

Throughout all versions, supplement slide content with B-roll and memes to maintain engagement:

- **Pain points**: Office Space scenes, "this is fine" meme, email avalanche visuals
- **Solution**: Clean workspace, flow state imagery, satisfying compilation videos
- **Proof**: Terminal output, commit graphs, before/after comparisons
- **Call to action**: GitHub logo, QR code to repository

---

## Script: Short Version (1-2 minutes)

> **SHORT VERSION ONLY** — This section is included in: Short, Medium, Long

### [0:00-0:15] Hook

**VISUAL:** Quick cuts of familiar frustrations—overflowing inbox, context switching between apps, "reply all" chains

**NARRATION:**
> "You have ideas. Good ones. But somewhere between your phone, your laptop, your inbox, and that spreadsheet nobody updates... they die. Not because they're bad. Because your environment kills them."

### [0:15-0:45] Problem + Solution

**VISUAL:** Constraint list (slide 3), then workflow diagram (slide 5)

**NARRATION:**
> "SpeakUp is a workflow pattern that fixes this. Ideation happens anywhere—your phone, a conversation, a whiteboard. Execution happens in one place—an IDE with AI assistance. Everything gets captured automatically to a system of record. No manual logging. No lost context. No excuses."

### [0:45-1:15] Proof Point

**VISUAL:** Productivity slide (slide 16), commit graph animation

**NARRATION:**
> "In 8 hours, one person produced 30 commits: a working protocol implementation, security verification, this briefing deck, and full documentation. Not a team. One person. The constraint isn't capability. It's environment."

### [1:15-1:30] Call to Action

**VISUAL:** GitHub repository page, QR code

**NARRATION:**
> "Everything is open source. The briefing, the code, the verification evidence. Link in the description. Go see for yourself."

**[END SHORT VERSION]**

---

## Script: Medium Version (5-8 minutes)

> **MEDIUM VERSION ADDS** — This section is included in: Medium, Long

*Includes all content from Short version, plus:*

### [1:30-2:30] The Eight Constraints (Expanded)

**VISUAL:** Constraint table (slide 3), with meme/disaster inserts for each

**NARRATION:**
> "Let's break down what's actually killing your productivity.
>
> **Fragmented workflows**—you're juggling five apps that don't talk to each other.
> [VISUAL: Person spinning plates]
>
> **Tool accessibility**—your AI assistant is blocked, or it's outside your trust boundary.
> [VISUAL: "Access Denied" screen]
>
> **Inbox-centric work**—critical decisions buried in email threads from six months ago.
> [VISUAL: Inbox with 10,000 unread]
>
> **Knowledge attrition**—Bob retired and took everything he knew with him.
> [VISUAL: Empty desk, tumbleweed]
>
> These aren't character flaws. They're environmental problems. And environmental problems have environmental solutions."

### [2:30-4:00] The Workflow Model (Expanded)

**VISUAL:** Workflow diagram (slide 5), animated to show flow

**NARRATION:**
> "The SpeakUp workflow has two active phases and one passive phase.
>
> **Ideation**—this is thinking work. Happens on your phone, in conversations, on a whiteboard. AI helps you brainstorm, refine, and structure ideas. No constraints on location.
>
> **Execution**—this is building work. Happens in an IDE—VSCode, JetBrains, whatever you use. AI assists with code, documents, artifacts. Within your trust boundaries.
>
> **System of Record**—this is automatic. Git captures everything. Every commit is a checkpoint. Every artifact is versioned. You don't have to remember to document—it happens as a side effect of working.
>
> The key insight: you can jump between ideation and execution at any time. They're not sequential phases. They're modes of work."

### [4:00-5:30] Security and Compliance

**VISUAL:** Security slide (slide 7), classification marking example (slide 8)

**NARRATION:**
> "Now, if you work in government or defense, you're already thinking about objections.
>
> 'We can't use cloud AI.' Fine. Use local models.
> 'We can't use GitHub.' Fine. Use GitLab or self-host.
> 'We have classification requirements.' Fine. The workflow supports proper markings.
>
> The SpeakUp repository itself contains no PII, no CUI, no classified information. Verified by automated scans. You can review it without relaxing any rules.
>
> Your implementation choices—where AI runs, where code lives, what devices you use—those are yours. The pattern is agnostic."

### [5:30-6:00] Value Proposition

**VISUAL:** Value proposition slide (slide 9), comparison table

**NARRATION:**
> "Here's the core point: with the right environment, one person can do the work of an entire team.
>
> Not by working harder. By removing friction. By letting AI handle the mechanical parts. By capturing knowledge automatically instead of hoping someone writes it down.
>
> This isn't about replacing people. It's about multiplying them."

### [6:00-6:30] Call to Action (Expanded)

**VISUAL:** Next steps slide (slide 19), repository page

**NARRATION:**
> "Here's what to do next:
>
> One—review the briefing deck. It's designed to be read without a presenter.
>
> Two—identify a pilot area. Something small where you can test the pattern.
>
> Three—set up the environment. Repository, IDE, AI access.
>
> Four—iterate. Ideation, execution, review. Let the system of record build itself.
>
> Everything you need is in the repository. Link in the description."

**[END MEDIUM VERSION]**

---

## Script: Long Version (15-20 minutes)

> **LONG VERSION ADDS** — This section is included in: Long only

*Includes all content from Medium version, plus:*

### [6:30-9:00] Technical Deep Dive: DTN Implementation

**VISUAL:** Screen recording of DTN demo, protocol diagrams, terminal output

**NARRATION:**
> "Let me show you what this looks like in practice.
>
> During the development of SpeakUp, I implemented a Delay-Tolerant Networking stack. That's Bundle Protocol version 7, TCP Convergence Layer, the whole thing. From scratch.
>
> [SHOW: Code structure, test output]
>
> This isn't toy code. It handles connection interruptions, bundle fragmentation, custody transfer. It's the kind of thing that would normally take a team weeks.
>
> [SHOW: 5-hour transfer test running]
>
> Right now, there's a test running—5 hours of continuous data transfer with simulated signal loss. Every interruption is logged. Every recovery is verified.
>
> The point isn't that DTN is special. The point is that this level of implementation is achievable by one person, in hours, with the right workflow."

### [9:00-12:00] Verification and Evidence

**VISUAL:** Verification artifacts slide (slide 15), scan results, attestation documents

**NARRATION:**
> "Let's talk about verification. Because in regulated environments, 'trust me' doesn't cut it.
>
> The SpeakUp repository includes automated verification:
>
> **PII Scan**—checks for phone numbers, SSNs, IP addresses. Pass.
>
> **Malware Scan**—ClamAV detection. Pass.
>
> **Secrets Scan**—API keys, credentials. Pass.
>
> **MAC Address Scan**—hardware identifiers. Pass.
>
> [SHOW: Scan output, attestation document]
>
> Every scan produces objective evidence. Not 'we reviewed it'—actual output that anyone can verify.
>
> This is what defensible looks like. When someone in your security office asks 'how do we know this is safe?', you hand them the scan results."

### [12:00-15:00] Scrum Guide Alignment

**VISUAL:** Scrum principles slide (slide 4), comparison with SpeakUp workflow

**NARRATION:**
> "If your organization uses Scrum or Agile, you might wonder how this fits.
>
> The Scrum Guide emphasizes three things: transparency, inspection, and adaptation.
>
> **Transparency**—SpeakUp delivers this through Git. Every decision, every change, every artifact is visible. No hidden work.
>
> **Inspection**—the system of record enables this. You can review any point in history. You can see what changed and why.
>
> **Adaptation**—the ideation-execution loop supports this. You're not locked into a two-week sprint. You can pivot in minutes.
>
> SpeakUp isn't anti-Agile. It's Agile taken seriously. The principles, not just the ceremonies."

### [15:00-17:00] Implementation Patterns

**VISUAL:** Repository structure, configuration examples

**NARRATION:**
> "Let's get practical. How do you actually implement this?
>
> **Repository structure**—keep it flat. Source code, documentation, verification artifacts all in one place. Don't hide things in nested folders.
>
> **Commit discipline**—each commit should be a coherent unit of work. Not 'WIP' or 'fix'. Actual descriptions of what changed and why.
>
> **AI integration**—use Claude Code, GitHub Copilot, Cursor, whatever works in your environment. The key is having it available in your IDE, not in a separate browser tab.
>
> **Mobile ideation**—use whatever captures thoughts quickly. Voice memos, notes app, chat with AI. The format doesn't matter. Getting ideas out of your head does.
>
> [SHOW: Example workflow from idea to commit]
>
> This isn't rigid. Adapt it to your context. The pattern is what matters, not the specific tools."

### [17:00-18:30] Objection Handling

**VISUAL:** FAQ-style slides, common objections with responses

**NARRATION:**
> "Let me address objections I've heard:
>
> 'This only works for solo developers.'
> No. The pattern scales. Each person maintains their own ideation-execution loop, but the system of record is shared. Collaboration happens through the repository, not through meetings.
>
> 'AI can't handle real engineering work.'
> It can't do everything. But it can handle 80% of the mechanical work—boilerplate, documentation, test scaffolding. That frees you for the 20% that requires judgment.
>
> 'My organization will never approve this.'
> That's why SpeakUp exists. It's designed to be reviewable, verifiable, and compliant. Show them the scan results. Show them the attestation. Make 'no' difficult.
>
> 'I don't have time to learn a new workflow.'
> You don't have time not to. The question isn't whether this takes time. It's whether it saves more time than it costs. The answer is yes, dramatically."

### [18:30-20:00] Closing and Extended Call to Action

**VISUAL:** Summary slide, repository page, contact information

**NARRATION:**
> "Here's the summary:
>
> SpeakUp is a workflow pattern for knowledge work. Ideation anywhere, execution in an IDE, automatic capture to Git.
>
> It works within security constraints. It produces verifiable evidence. It multiplies individual capability.
>
> The repository is open source. The briefing is self-contained. The verification is automated.
>
> If you're tired of fighting your environment, if you have ideas that deserve to exist, if you want to do work that matters instead of work that's required—try this.
>
> Clone the repository. Read the briefing. Pick a small project. See what happens.
>
> Link in the description. I'll see you in the commits."

**[END LONG VERSION]**

---

## B-Roll and Meme Suggestions

| Topic | Suggested Visual | Source/Notes |
|-------|------------------|--------------|
| Fragmented workflows | Person juggling, dropping items | Stock footage or animation |
| Email overload | Inbox counter spinning up | Screen recording or stock |
| Knowledge attrition | Empty desk, tumbleweed | Office Space clip or stock |
| Tool restrictions | "Access Denied" screen | Generic error screen |
| AI assistance | Pair programming visual | Stock or screen recording |
| Productivity | Time-lapse coding session | Screen recording |
| Git commits | Commit graph animation | GitHub contribution graph |
| Security scans | Terminal output scrolling | Actual scan output |
| Success/completion | Satisfying "build succeeded" | Compilation output |
| Call to action | QR code, GitHub page | Repository screenshot |

---

## Production Notes

- **Narration**: Can be recorded by author or generated via AI voice (ElevenLabs, etc.)
- **Slide integration**: Export briefing slides as images, overlay with Ken Burns effect
- **Editing tools**: DaVinci Resolve (free), Descript, or Kapwing
- **Music**: Subtle background track, royalty-free (Epidemic Sound, Artlist)
- **Captions**: Auto-generate, then review for accuracy
- **Chapters**: Add YouTube chapters matching section timestamps

---

## Distribution Checklist

- [ ] Short version: LinkedIn, Twitter/X, TikTok (vertical crop)
- [ ] Medium version: YouTube (primary), internal comms
- [ ] Long version: YouTube (playlist with chapters), training portals
- [ ] All versions: Include repository link in description
- [ ] All versions: Add QR code overlay at CTA
- [ ] YouTube: Create custom thumbnails for each version
- [ ] YouTube: Add end screens linking to other versions
