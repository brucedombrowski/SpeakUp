# SpeakUp File Integrity Manifest

---

## Manifest Information

| Field | Value |
|-------|-------|
| Generated | 2025-12-22 22:47:39 |
| Algorithm | SHA-256 |
| Standard | FIPS 180-4 (Secure Hash Standard) |

---

## Purpose

This manifest provides cryptographic hashes for all repository files, enabling:

1. **Integrity Verification** - Detect unauthorized modifications
2. **Authenticity Confirmation** - Verify file contents match expected values
3. **Chain of Custody** - Document file state at a point in time

---

## File Hashes

| File | SHA-256 Hash |
|------|--------------|
| `./.claude/settings.local.json` | `15a91cd931e73e74564ed4e17bbb7b2d3ec4f5165f4a0cadba667786d724bdfe` |
| `./.gitignore` | `cd38de6a90d62ba7788538a877fcbb4af1b19c7c21f9714c675ff4012bc5bf01` |
| `./LICENSE` | `d0139b87a50b5130679c6e6f3d11db459b9451a6d76c0ddb28dd018fc33d8eea` |
| `./README.md` | `d4afe3037bf0fc10fd4209044d0d3c91af38e387eacf04e7fef9d0533eabd116` |
| `./artifacts/SpeakUp_ideation_user_plus_summary.md` | `23f9ec9597cec12ce3ab8b4bff9b4293848084e614f84eb330c8e33bc5fbbbe5` |
| `./artifacts/Workflow-Log.md` | `ad0f2697c44a4a08ba4a025c51926755dc3be7d11adf69815d2c181be7eedff2` |
| `./briefing/SpeakUp-Briefing.pdf` | `c564d9cd23ec16f6714bd735b7028a343bbf571c8ff9b692c8909e7a3e44faf5` |
| `./briefing/SpeakUp-Briefing.tex` | `2953481e6c1c39743bcc5fbb2f1f5c2f8829df6d413ed3bd2ed88e96d2624927` |
| `./verification/Compliance-Statement.md` | `0c4e337aa77996f7430f2f498f9940806f0aa1759081b74e484797227f395638` |
| `./verification/Requirements-Traceability.md` | `b9c702697d408f5bab94b4c8f7f4948e55a73c23b661c28ceb303ba41fe79d95` |
| `./verification/Security-Attestation.md` | `96fe1da8ddf00d6822cc4f4eabc1c97d8792fac183110650d8e89efcd2231676` |
| `./verification/scripts/check-host-security.sh` | `4fcc37397888b4d49a945df3d45357288ccaa6f534e65a931d9cc11c8b7a6497` |
| `./verification/scripts/check-mac-addresses.sh` | `edf1074a6f2a08720ef0fcc980c3ced979c6adc0089901d51ec5bf458f15477e` |
| `./verification/scripts/check-malware.sh` | `224856d4da09da560cdff31cf4ae06689b6a8a06ea22964b4ceb2e3dc4855ce0` |
| `./verification/scripts/check-pii.sh` | `76fe2f075ef0e10ecc247cc62222f58f4a36db075b6e1d12e40ac73605ede7ee` |
| `./verification/scripts/check-vulnerabilities.sh` | `45b08bd34291f39c3f6d20d9549980286ff69cd1ac5ac21151b904bc995b6bb9` |
| `./verification/scripts/generate-manifest.sh` | `3a773d59afc68086b8c8c42063911bf974613978483bc5560f96202e11be88e4` |
| `./verification/scripts/run-all-scans.sh` | `237201e67c18ea2ed836080fc67f6702cdab9e9696855d55397833177d7e1e65` |

---

## Verification Instructions

To verify file integrity, run:

```bash
shasum -a 256 <filename>
```

Compare the output hash with the value in this manifest.

---

## NIST Control Reference

| Control | Description |
|---------|-------------|
| SI-7 | Software, Firmware, and Information Integrity |
| SI-7(1) | Integrity Checks |
| SI-7(6) | Cryptographic Protection |

---

## Notes

- This manifest is regenerated with each verification run
- Binary files (PDF) are included in the hash
- The manifest itself is excluded from hashing (circular reference)
- Git commit hashes provide additional integrity verification

---

*This manifest was automatically generated for integrity verification purposes.*
