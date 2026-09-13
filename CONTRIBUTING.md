# Contributing to WSABuilds

Thank you for your interest in contributing to **WSABuilds**! This project maintains modified Windows Subsystem for Android (WSA) builds integrated with Magisk, Google Play Services (GApps), and ARM translation (Houdini).

To maintain code quality, reproducibility, and stability, please review these guidelines before opening an issue or submitting a Pull Request.

---

## Code of Conduct

We are committed to providing a welcoming, inclusive, and harassment-free environment for all contributors and community members. Please treat others with respect and constructive collaboration.

---

## How to Report Bugs

Before filing a bug report:
1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md) and existing [Issues](https://github.com/IamAzmathullaShaikh/WSABuilds/issues) to see if the problem has already been reported or solved.
2. Confirm you are running on a supported Windows build (Windows 11 Build 22000.526+ or Windows 10 22H2 Build 19045.2311+ with required KBs).
3. If reporting a new issue, use the [Bug Report Form](.github/ISSUE_TEMPLATE/bug_report.yml) and provide:
   - Complete WSA version string (e.g., `2407.40000.4.0`)
   - Windows build version (`winver`)
   - Hardware specifications (CPU architecture, GPU)
   - Step-by-step reproduction instructions
   - Relevant logcat or installation logs

---

## Development & Testing Workflow

### 1. Prerequisites
- **For Linux / WSL2 Build Pipeline**:
  - Ubuntu 22.04+ or Debian 12+
  - Dependencies: `e2fsprogs`, `attr`, `unzip`, `qemu-utils`, `python3`, `python3-venv`, `aria2`, `p7zip-full`, `shellcheck`
- **For Native Windows Standalone Builder**:
  - Windows 10 / 11 (x64 or arm64)
  - Python 3.10+ (standard library only; no external pip dependencies required for `build_local.py`)
  - 7-Zip installed and available on `PATH`

### 2. Local Linting & Validation
All contributions must pass local quality checks before submitting a PR:

```bash
# 1. ShellCheck validation for Bash scripts
shellcheck -x -S warning --exclude=SC2034,SC2174 MagiskOnWSA/scripts/*.sh

# 2. Python syntax and bytecode validation
python -m compileall -q MagiskOnWSA/scripts/ "WSABuilds Utilities/" tests/

# 3. Actionlint for GitHub Actions workflows
actionlint .github/workflows/*.yml

# 4. Offline test suite
pytest tests/
```

---

## Commit Message Conventions

This repository strictly enforces **Conventional Commits**. Please format commit messages as:

```text
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

### Supported Types:
- `feat`: New feature or build capability (e.g., `feat(build): add native Windows standalone builder`)
- `fix`: Bug fix (e.g., `fix(ci): downgrade broken action versions to valid releases`)
- `docs`: Documentation updates (e.g., `docs: update troubleshooting guide`)
- `refactor`: Code refactoring without changing observable behavior
- `ci`: CI/CD workflow changes (e.g., `ci: update matrix configuration`)
- `chore`: Maintenance tasks (e.g., `chore: update .gitignore`)

---

## Pull Request Guidelines

1. **Keep PRs Focused**: One logical change per PR. Avoid bundling unrelated fixes or features together.
2. **Never Commit Secrets or Local Paths**:
   - Do not commit Personal Access Tokens (PATs), API keys, or machine-specific paths (e.g. `C:\Users\<Username>\...`).
3. **Preserve Documentation Integrity**: Update relevant documentation, README files, or troubleshooting guides alongside code changes.
4. **CI Verification**: Ensure all GitHub Actions checks (`Lint`, `Build`) pass cleanly on your fork prior to requesting review.
