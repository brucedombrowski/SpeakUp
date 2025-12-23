# Environmental Friction Patterns

Documented patterns of workplace environments that kill productivity - not through malice, but through accumulated friction.

## The "Soft No"

When a development team or organization doesn't explicitly reject your request, but:
- Never prioritizes it in the backlog
- Is legitimately overworked and can't fit it in
- Requires so many approvals that momentum dies
- Says "yes" but never allocates resources

The result is the same as "no" - your idea dies. But there's no clear decision point to escalate or appeal.

**SpeakUp solution**: Build it yourself. Document it. Present the working solution, not the request.

---

## Identity & Access Friction

### Multiple CAC Cards
- Switching between cards for different systems
- Each card = different trust boundary
- Physical card swap + PIN entry + application restart
- Context switch penalty compounded by authentication overhead

### Multiple VPNs
- Different networks for different classification levels
- VPN conflicts (can't run two simultaneously)
- Disconnect/reconnect cycle between tasks
- "Which VPN am I on?" uncertainty

### Constant PIN Prompts
- CAC timeout during complex tasks
- Re-authentication interrupts flow state
- PIN entry fatigue leads to shortcuts
- Screen locks during long compilations/builds

### "Certificate Not Found" Error
- The dreaded error with no clear cause
- Sometimes the card is fine, sometimes the reader, sometimes the middleware
- **The universal fix**: Restart your laptop
- 10-minute reboot cycle to fix a 2-second authentication
- Happens at the worst possible moment (demo, deadline, flow state)

**Compound effect**: A 30-second task becomes 5 minutes when you factor in:
1. Switch CAC card
2. Enter PIN
3. Wait for system to recognize
4. Switch VPN
5. Re-authenticate to application
6. Remember what you were doing

---

## Development Environment Friction

### "Give Me My Sandbox!"
- Need a dev environment to test something? Submit a ticket.
- Wait 2 weeks for provisioning
- Get an environment that doesn't match production
- Environment expires, lose all your work
- Rinse and repeat

**What you want**: A place to experiment without breaking anything or waiting for anyone.

**What you get**: Bureaucracy that treats experimentation as a risk rather than a necessity.

---

## Communication Friction

### Email Overload
- Critical decisions buried in threads
- No single source of truth
- "Did you see my email?" as workflow
- Reply-all chaos

### Meeting Culture
- Decisions made verbally, never documented
- "Let's schedule a meeting to discuss"
- Calendar Tetris blocks deep work
- Status meetings that could be async

### Tool Fragmentation
- Slack + Teams + Email + JIRA + Confluence
- Same information in multiple places
- "Where was that conversation?"
- Notification fatigue

---

## Security Theater vs. Actual Security

Patterns that feel secure but add friction without proportional risk reduction:

| Pattern | Friction | Actual Security Value |
|---------|----------|----------------------|
| Password rotation every 30 days | High (leads to Post-it notes) | Low (NIST now recommends against) |
| Blocking all USB devices | Medium | Medium (but breaks legitimate workflows) |
| Air-gapped development | Very High | High (but often overkill) |
| Multiple CAC cards | High | Medium (could be consolidated) |

---

## The SpeakUp Response

For each friction pattern, ask:
1. **Is this friction necessary?** Some security controls are worth the cost.
2. **Can it be automated?** If you must do it, can a script handle it?
3. **Can it be consolidated?** Multiple systems → single system of record
4. **Can it be documented?** At minimum, capture the workaround

The goal isn't to eliminate all friction - some is legitimate security. The goal is to:
- Recognize when friction is killing your ideas
- Document the patterns so others can learn
- Build workflows that route around unnecessary friction
- Make the case for change with evidence, not complaints

---

## Contributing

Add your own environmental friction patterns. Format:

```markdown
### Pattern Name

Description of the friction.

**Impact**: How it affects productivity.
**Workaround**: If any exists.
**Root cause**: Why it exists (often legitimate, sometimes not).
```

---

*"The constraint isn't capability. It's environment."*
