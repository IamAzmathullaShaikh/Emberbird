# Contributing to WSABuilds

Thank you for your interest in contributing to **WSABuilds**!

Our mission is to provide the easiest, most reliable, and community-supported way to install, update, manage, and troubleshoot Windows Subsystem for Android (WSA) after Microsoft's official deprecation.

Please review these guidelines to ensure a productive and smooth collaboration.

---

## 1. Guiding Principle

Every contribution must answer this core question:
> **"Will this help users install, update, manage, or troubleshoot WSA more easily?"**

We prioritize simplicity, reliability, automation, and community trust over feature bloat or speculative architecture.

---

## 2. Branching Strategy

Our repository operates on a strict three-tier branch hierarchy:

| Branch | Purpose | Merge Policy |
|---|---|---|
| **`master`** | Production releases and verified stable builds. | Requires 2 maintainer reviews; all CI checks must pass; linear history enforced. |
| **`experimental`** | Feature development, automation testing, and prototypes. | Requires 1 maintainer review; automated CI checks must pass. |
| **`gh-pages`** | Static website deployment (`wsabuilds.azmathulla.dev` - Status: Planned Feature). | Automated deployment via GitHub Actions; direct pushes restricted to CI. |

All pull requests should target `experimental` for new features or `master` for critical bug fixes and documentation corrections.

---

## 3. Pull Request Process

1. **Fork & Branch**: Fork the repository and create a feature branch from `master` or `experimental`:
   ```bash
   git checkout -b feature/my-enhancement
   ```
2. **Keep PRs Focused**: Submit small, focused pull requests addressing a single issue or feature. Avoid combining unrelated changes.
3. **Run Local Quality Gates**:
   Ensure all automated verification checks pass before opening your PR:
   ```bash
   # 1. Run unit tests
   python -m unittest discover -s tests -v

   # 2. Verify all Markdown links
   python scripts/check_doc_links.py

   # 3. Verify security & secret cleanliness
   python scripts/security_scan.py
   ```
4. **Follow Conventional Commits**:
   Format commit messages clearly:
   - `feat(component): add new capability`
   - `fix(workflow): resolve runner timeout`
   - `docs(troubleshooting): add error code 0x80370102`
   - `chore(deps): bump certifi dependency`
5. **Complete the PR Template**: Ensure every item on the `.github/PULL_REQUEST_TEMPLATE.md` checklist is completed.

---

## 4. Issue Reporting Process

We use structured GitHub Issue Forms to ensure actionable, reproducible reports:

- **Bug Reports**: Use the [Bug Report Form](.github/ISSUE_TEMPLATE/bug_report.yml). Provide exact Windows build numbers (`winver`), WSA flavor, hardware specs, and error messages.
- **Application Compatibility**: Use the [Compatibility Report Form](.github/ISSUE_TEMPLATE/compatibility_report.yml) to contribute real-world testing results for Android apps (e.g. banking, social, gaming).
- **Feature Proposals**: Use the [Feature Request Form](.github/ISSUE_TEMPLATE/feature_request.yml) to explain user impact and differentiator alignment.

---

## 5. Code Review Expectations

- **Response Time**: Maintainers strive to review pull requests within 48 to 72 hours.
- **Constructive Collaboration**: Reviews focus on code quality, security hygiene, user simplicity, and test coverage.
- **Automated Gates**: Pull requests cannot be merged if any GitHub Actions check fails (`Unit Tests`, `Doc Link Verifier`, `Security Scanner`).

---

## 6. Community Standards & Code of Conduct

We are dedicated to providing a respectful, welcoming, and inclusive experience for everyone.

- Be respectful and courteous in discussions, issue comments, and code reviews.
- Focus on constructive feedback and helping fellow users troubleshoot problems.
- Unacceptable behavior (harassment, personal attacks, or spam) will result in moderation action or account banning.
