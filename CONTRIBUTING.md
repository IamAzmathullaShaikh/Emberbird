# Contributing to Emberbird

Thank you for your interest in contributing to **Emberbird**!

Our mission is to provide the easiest, most reliable, and community-supported way to install, update, manage, and troubleshoot Windows Subsystem for Android (WSA) after Microsoft's official deprecation.

Please review these guidelines to ensure a productive and smooth collaboration.

---

## 1. The 30-Minute Contributor Quickstart

We have engineered our developer experience so that any new contributor can clone the repository, run the full verification battery, understand our architectural model, and submit their first pull request in **under 30 minutes**.

### Step 1: Clone and Enter the Repository (1 minute)
```bash
git clone https://github.com/IamAzmathullaShaikh/Emberbird.git
cd Emberbird
```

### Step 2: Set Up Virtual Environment (2 minutes)
The core tooling and test suite are stdlib-first (Python 3.10+):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# Optional: install jsonschema to run schema-contract validation
python -m pip install jsonschema
```

### Step 3: Run the Full Offline Test Battery (1 minute)
```bash
python -m unittest discover -s tests
```
*Expected output: `289+ tests ... OK (skipped=19)`. Runs 100% offline with zero network calls.*

### Step 4: Run the Quality & Security Gates (2 minutes)
```powershell
# 1. Release registry reality gate (must exit 0)
python platform/release-engine/release_engine/__main__.py validate --schema

# 2. Markdown local link checker
python scripts/check_doc_links.py

# 3. Secret and credential scanner
python scripts/security_scan.py

# 4. Distribution metadata validator
python scripts/validate_distribution.py
```

### Step 5: Understand the Architecture (10 minutes)
Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/EMBERBIRD_CHARTER.md](docs/EMBERBIRD_CHARTER.md).
- **Core Doctrine**: **Published Artifacts Are Truth**.
- **Registry Independence**: All consumer surfaces (Web Portal, Desktop Manager, Winget) derive release metadata solely from `data/releases/releases.json`. No consumer hardcodes release tags or scrapes GitHub HTML/APIs.

### Step 6: Create Your Branch and Make Your Change (10 minutes)
Create a focused branch from `main`:
```bash
git checkout -b feature/my-improvement
```

### Step 7: Submit Pull Request (4 minutes)
Push your branch and open a PR targeting `main` following Conventional Commits format.

---

## 2. Branching Strategy

Our repository operates on a clear branch hierarchy:

| Branch | Role | Purpose & Policy |
|---|---|---|
| **`main`** | **Default Integration** | Primary branch for verified stable changes, documentation, and releases. PRs target here. |
| **`master`** | **Historical Default** | Protected infrastructure branch maintained for backward compatibility and CI workflows. |
| **`experimental`** | **Staging & Prototypes** | Feature prototypes, pre-merge staging, and exploratory automation testing. |
| **`gh-pages`** | **Deployment Source** | Live GitHub Pages documentation build source. Automated CI pushes only. |

All pull requests should target **`main`** (or `experimental` for exploratory prototypes).

---

## 3. Pull Request Process

1. **Keep PRs Focused**: Submit small, focused pull requests addressing a single issue or feature. Avoid combining unrelated changes.
2. **Run Local Quality Gates**:
   Ensure all automated verification checks pass before opening your PR:
   ```bash
   python -m unittest discover -s tests
   python platform/release-engine/release_engine/__main__.py validate --schema
   python scripts/check_doc_links.py
   python scripts/security_scan.py
   ```
3. **Follow Conventional Commits**:
   Format commit messages clearly:
   - `feat(component): add new capability`
   - `fix(workflow): resolve runner timeout`
   - `docs(troubleshooting): add error code 0x80370102`
   - `chore(deps): bump certifi dependency`
4. **Complete the PR Template**: Ensure every item on the `.github/PULL_REQUEST_TEMPLATE.md` checklist is completed.

---

## 4. Issue Reporting Process

We use structured GitHub Issue Forms to ensure actionable, reproducible reports:

- **Bug Reports**: Use the [Bug Report Form](.github/ISSUE_TEMPLATE/bug_report.yml). Provide exact Windows build numbers (`winver`), WSA flavor, hardware specs, and error messages.
- **Application Compatibility**: Use the [Compatibility Report Form](.github/ISSUE_TEMPLATE/compatibility_report.yml) to contribute real-world testing results for Android apps.
- **Feature Proposals**: Use the [Feature Request Form](.github/ISSUE_TEMPLATE/feature_request.yml) to explain user impact and differentiator alignment.

---

## 5. Code Review Expectations

- **Response Time**: Maintainers strive to review pull requests within 48 to 72 hours.
- **Constructive Collaboration**: Reviews focus on code quality, security hygiene, user simplicity, and test coverage.
- **Automated Gates**: Pull requests cannot be merged if any GitHub Actions check fails (`Unit Tests`, `Doc Link Verifier`, `Security Scanner`, `Reality Gate`).

---

## 6. Community Standards & Code of Conduct

We are dedicated to providing a respectful, welcoming, and inclusive experience for everyone.
- Be respectful and courteous in discussions, issue comments, and code reviews.
- Focus on constructive feedback and helping fellow users troubleshoot problems.
- Unacceptable behavior (harassment, personal attacks, or spam) will result in moderation action or account banning.
