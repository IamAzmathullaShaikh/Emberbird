# GitHub Discussions Governance & Community Guidelines

This document outlines the operational structure, category definitions, posting rules, and moderation policies for GitHub Discussions in the IamAzmathullaShaikh/WSABuilds repository: https://github.com/IamAzmathullaShaikh/WSABuilds

---

## 1. Category Definitions

| Category | Purpose | Who Can Post | Answerable |
|---|---|---|---|
| **📣 Announcements** | Official updates, release announcements, security advisories, and upstream synchronization reports. | Maintainers only | No |
| **🙋 Q&A** | Installation troubleshooting, BIOS virtualization help, and general usage questions. | All community members | **Yes** (Mark as Answer enabled) |
| **💡 Ideas** | Feature suggestions, automation proposals, and manager enhancement requests. | All community members | No (Upvoting enabled) |
| **📱 Compatibility Reports** | Android app compatibility results, Magisk module tweaks, and Play Integrity workarounds. | All community members | No |
| **🎉 Show and Tell** | Desktop setups, gamepad configurations, performance benchmarks, and user showcases. | All community members | No |

---

## 2. Category Usage Guidelines

### 📣 Announcements
- Reserved exclusively for repository maintainers.
- Used to communicate milestone completions, upstream sync summaries, breaking changes, and new release downloads.
- Community members may comment and react to announcement posts.

### 🙋 Q&A
- Intended for users experiencing issues installing, updating, or running WSA.
- **Rules before posting**:
  1. Check [docs/troubleshooting/error-codes.md](../troubleshooting/error-codes.md) to see if your error code is already solved.
  2. Search existing Q&A threads to avoid duplicates.
  3. Include your Windows version (`winver`), WSA flavor, and hardware specs.
- Once a problem is resolved, mark the most helpful response as the accepted answer.

### 💡 Ideas
- The primary venue for open-source brainstorming and feature requests.
- **Rule**: Every idea must explain how it helps users install, update, manage, or troubleshoot WSA more easily.
- Use thread upvoting to demonstrate community demand.

### 📱 Compatibility Reports
- Designed for testing notes on specific Android applications (banking apps, games, streaming).
- Posts should state:
  1. Exact application name and package ID.
  2. Tested WSA release version and root flavor (Magisk Stable, KernelSU, No Root).
  3. Steps taken (e.g. Zygisk enabled, Shamiko, DenyList, PlayIntegrityFix version).
  4. Operational outcome (Runs perfectly, requires workaround, or crashes).
- High-quality, reproducible reports are verified and merged into `compatibility/data/[AppName].json`.

### 🎉 Show and Tell
- Share your Windows 11 desktop setups, gaming configurations, controller mapping profiles, or creative use-cases.
- Keep content friendly, relevant to Android-on-Windows, and free of commercial solicitation.

---

## 3. Moderation & Code of Conduct

- **Constructive Communication**: Maintain a professional, respectful tone across all threads.
- **Zero Tolerance for Piracy or Malware**: Links to cracked APKs, warez, or malicious root modules are strictly prohibited and will be deleted immediately.
- **Duplicate Management**: Maintainers will lock and redirect duplicate threads to canonical answers.
