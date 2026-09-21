#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Emberbird Manager release automation (FB-5).
    Creates and pushes the release tag after validating all prerequisites.

.DESCRIPTION
    Usage:
        .\scripts\release.ps1              # Release current version from deployment/version.json
        .\scripts\release.ps1 -DryRun      # Validate everything but don't push tag
        .\scripts\release.ps1 -SkipTests   # Skip test battery (use only if already verified)

.PARAMETER DryRun
    Validate all prerequisites and print what would be done, but do not create or push any tag.

.PARAMETER SkipTests
    Skip the full test battery. Useful when you've just run tests and want to re-run only the release step.
#>
param(
    [switch]$DryRun,
    [switch]$SkipTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$REPO_ROOT = Split-Path $PSScriptRoot -Parent
Set-Location $REPO_ROOT

function Write-Step([string]$msg) { Write-Host "`n[*] $msg" -ForegroundColor Cyan }
function Write-Ok([string]$msg)   { Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Fail([string]$msg) { Write-Host "[X] FATAL: $msg" -ForegroundColor Red; exit 1 }

# -- 1. Read version from deployment/version.json (single source of truth) --
Write-Step "Reading version from deployment/version.json"
$deploy = Get-Content "$REPO_ROOT/deployment/version.json" | ConvertFrom-Json
$VERSION = $deploy.manager.version
if (-not $VERSION -or $VERSION -notmatch '^\d+\.\d+\.\d+$') {
    Write-Fail "deployment/version.json: invalid version '$VERSION' (expected semver like 0.2.2)"
}
Write-Ok "Target version: v$VERSION"

# -- 2. Validate cross-file version consistency --
Write-Step "Validating version consistency across all manifests"

$pkgVer = (Get-Content "$REPO_ROOT/apps/manager/package.json" | ConvertFrom-Json).version
if ($pkgVer -ne $VERSION) { Write-Fail "package.json has version '$pkgVer', expected '$VERSION'" }

$cargoLine = Select-String 'version = "' "$REPO_ROOT/apps/manager/src-tauri/Cargo.toml" | Select-Object -First 1
$cargoVer = ($cargoLine.Line -replace '.*version = "([^"]+)".*','$1')
if ($cargoVer -ne $VERSION) { Write-Fail "Cargo.toml has version '$cargoVer', expected '$VERSION'" }

$tauriVer = (Get-Content "$REPO_ROOT/apps/manager/src-tauri/tauri.conf.json" | ConvertFrom-Json).version
if ($tauriVer -ne $VERSION) { Write-Fail "tauri.conf.json has version '$tauriVer', expected '$VERSION'" }

Write-Ok "All 4 version sources agree: $VERSION"

# -- 3. Check git state --
Write-Step "Checking git state"

$status = git status --porcelain 2>&1
if ($status) {
    Write-Warn "Working tree is not clean. Uncommitted changes:"
    $status | ForEach-Object { Write-Host "  $_" }
    if (-not $DryRun) {
        Write-Fail "Commit or stash changes before releasing."
    } else {
        Write-Warn "[DryRun] Would abort here - uncommitted changes present."
    }
}

$tagExists = git tag -l "v$VERSION"
if ($tagExists) {
    Write-Fail "Tag v$VERSION already exists. Bump the version to release a new one."
}

$branch = git rev-parse --abbrev-ref HEAD
Write-Ok "On branch: $branch"
Write-Ok "Tag v$VERSION does not exist yet - ready to create."

# -- 4. Full test battery --
if (-not $SkipTests) {
    Write-Step "Running full test battery"

    Set-Location "$REPO_ROOT/apps/manager"

    Write-Host "  [1/5] ESLint..."
    npm run lint
    if ($LASTEXITCODE -ne 0) { Write-Fail "ESLint failed." }
    Write-Ok "ESLint: 0 warnings"

    Write-Host "  [2/5] TypeScript typecheck..."
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { Write-Fail "TypeScript typecheck failed." }
    Write-Ok "TypeScript: 0 errors"

    Write-Host "  [3/5] Node contract tests..."
    npm test
    if ($LASTEXITCODE -ne 0) { Write-Fail "Node --test suite failed." }
    Write-Ok "Node tests: pass"

    Write-Host "  [4/5] Vitest component tests..."
    npm run test:components
    if ($LASTEXITCODE -ne 0) { Write-Fail "Vitest component tests failed." }
    Write-Ok "Vitest: pass"

    Set-Location "$REPO_ROOT/apps/manager/src-tauri"

    Write-Host "  [5a/5] cargo fmt --check..."
    cargo fmt --all -- --check
    if ($LASTEXITCODE -ne 0) { Write-Fail "cargo fmt check failed. Run: cargo fmt --all" }
    Write-Ok "Rust formatting: clean"

    Write-Host "  [5b/5] cargo clippy..."
    cargo clippy -- -D warnings
    if ($LASTEXITCODE -ne 0) { Write-Fail "cargo clippy failed." }
    Write-Ok "Clippy: 0 warnings"

    Write-Host "  [5c/5] cargo test..."
    cargo test
    if ($LASTEXITCODE -ne 0) { Write-Fail "Rust tests failed." }
    Write-Ok "Rust tests: pass"

    Set-Location $REPO_ROOT

    Write-Host "  [6/6] Python contract tests..."
    $pyResult = cmd.exe /c "python -m unittest discover -s tests 2>&1"
    $lastLine = ($pyResult -split "`n" | Where-Object { $_ -match 'OK|FAIL|ERROR' } | Select-Object -Last 1)
    if ($lastLine -notmatch 'OK') { Write-Fail "Python tests failed: $lastLine" }
    Write-Ok "Python tests: $lastLine"

    Write-Ok "Full test battery passed."
}

# -- 5. Validate Winget manifests exist for this version --
Write-Step "Validating Winget manifests for v$VERSION"
$manifestDir = "$REPO_ROOT/manifests/e/Emberbird/Manager/$VERSION"
if (-not (Test-Path $manifestDir)) {
    Write-Fail "Winget manifest directory missing: $manifestDir\n  Run: scripts/bootstrap_winget.py to generate manifests."
}
$manifests = Get-ChildItem $manifestDir -Filter "*.yaml"
if ($manifests.Count -lt 3) {
    Write-Fail "Expected 3 Winget YAML files in $manifestDir, found $($manifests.Count)"
}
Write-Ok "Winget manifests present: $($manifests.Name -join ', ')"

# -- 6. Validate distribution validator passes --
Write-Step "Running distribution validator"
python scripts/validate_distribution.py
if ($LASTEXITCODE -ne 0) { Write-Fail "Distribution validator failed." }
Write-Ok "Distribution validator: pass"

# -- 7. Create and push tag --
if ($DryRun) {
    Write-Warn "[DryRun] Would now run:"
    Write-Warn "  git tag -a v$VERSION -m 'Emberbird Manager v$VERSION'"
    Write-Warn "  git push origin v$VERSION"
    Write-Warn "[DryRun] CI would then trigger winget-release.yml (build, sign, publish, Winget PR)."
    Write-Ok "Dry run complete - all gates passed. Remove -DryRun to release."
    
    # -- Post-release: print version bump instructions --
    Write-Host ""
    Write-Host "===================================================================="
    Write-Host "  Emberbird Manager v$VERSION released successfully!"
    Write-Host "===================================================================="
    Write-Host ""
    Write-Host "To prepare the next release, update ALL 4 version sources:"
    Write-Host "  1. deployment/version.json  -> manager.version"
    Write-Host "  2. apps/manager/package.json -> version"
    Write-Host "  3. apps/manager/src-tauri/Cargo.toml -> version (first occurrence)"
    Write-Host "  4. apps/manager/src-tauri/tauri.conf.json -> version"
    Write-Host ""
    Write-Host "Then generate Winget manifests:"
    Write-Host "  python scripts/bootstrap_winget.py"
    Write-Host ""
    Write-Host "Then run this script again:"
    Write-Host "  .\scripts\release.ps1 -DryRun   # verify"
    Write-Host "  .\scripts\release.ps1            # publish"
    
    exit 0
}

Write-Step "Creating release tag v$VERSION"
git tag -a "v$VERSION" -m "Emberbird Manager v$VERSION"
Write-Ok "Tag v$VERSION created locally."

Write-Step "Pushing tag to origin"
git push origin "v$VERSION"
Write-Ok "Tag v$VERSION pushed. CI will now:"
Write-Host "  1. Build the Tauri app (NSIS installer)"
Write-Host "  2. Sign with Azure Trusted Signing (if configured)"
Write-Host "  3. Create GitHub Release with checksums"
Write-Host "  4. Submit PR to microsoft/winget-pkgs (if WINGET_TOKEN configured)"
Write-Host ""
Write-Host "Monitor at: https://github.com/IamAzmathullaShaikh/Emberbird/actions"

# -- Post-release: print version bump instructions --
Write-Host ""
Write-Host "===================================================================="
Write-Host "  Emberbird Manager v$VERSION released successfully!"
Write-Host "===================================================================="
Write-Host ""
Write-Host "To prepare the next release, update ALL 4 version sources:"
Write-Host "  1. deployment/version.json  -> manager.version"
Write-Host "  2. apps/manager/package.json -> version"
Write-Host "  3. apps/manager/src-tauri/Cargo.toml -> version (first occurrence)"
Write-Host "  4. apps/manager/src-tauri/tauri.conf.json -> version"
Write-Host ""
Write-Host "Then generate Winget manifests:"
Write-Host "  python scripts/bootstrap_winget.py"
Write-Host ""
Write-Host "Then run this script again:"
Write-Host "  .\scripts\release.ps1 -DryRun   # verify"
Write-Host "  .\scripts\release.ps1            # publish"
