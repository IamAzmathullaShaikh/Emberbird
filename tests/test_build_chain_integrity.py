#!/usr/bin/env python3
"""Build-chain integrity guards.

The E2 restructure moved the build toolchain into `tools/` and `tools/core/`
without repairing the references *inside* those files. The result was invisible
to every test (nothing executes the WSA build locally) until a real release run
failed within seconds:

    build.sh: line 52: ./download_utils.sh: No such file or directory

These guards resolve the build chain statically — every script the toolchain
invokes must exist where the toolchain expects it, and the release workflow must
agree with the toolchain about paths. They run offline in CI, so a moved file
fails a 1-second test instead of an hour-long release build.

stdlib-only; runs in CI unchanged.
"""

import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

BUILD_SH = REPO_ROOT / "tools" / "build.sh"
BUILD_LOCAL = REPO_ROOT / "tools" / "build_local.py"
RUN_SH = REPO_ROOT / "tools" / "core" / "run.sh"
INSTALL_DEPS = REPO_ROOT / "tools" / "core" / "install_deps.sh"
GENERATE_WSA_LINKS = REPO_ROOT / "tools" / "core" / "generateWSALinks.py"
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"

# Files every build path must be able to reach, relative to the repository root.
REQUIRED_BUILD_INPUTS = (
    "tools/build.sh",
    "tools/config.sh",
    "tools/build_local.py",
    "tools/generateGappsLink.py",
    "tools/core/download_utils.sh",
    "tools/core/install_deps.sh",
    "tools/core/requirements.txt",
    "tools/core/extractWSA.py",
    "tools/core/extractMagisk.py",
    "tools/core/generateWSALinks.py",
    "tools/core/generateMagiskLink.py",
    "tools/core/fixGappsProp.py",
    "tools/update-check/env_helpers.py",
    "upstream/xml/GetCookie.xml",
    "upstream/xml/WUIDRequest.xml",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


class TestBuildInputsExist(unittest.TestCase):
    def test_every_build_input_is_present(self):
        missing = [p for p in REQUIRED_BUILD_INPUTS if not (REPO_ROOT / p).is_file()]
        self.assertEqual(missing, [], f"build inputs missing from the tree: {missing}")


class TestShellReferencesResolve(unittest.TestCase):
    """A source/invocation target must exist relative to the invoking script."""

    def assert_references_resolve(self, script: Path, pattern: str):
        text = read(script)
        refs = sorted({m.group(1) for m in re.finditer(pattern, text)})
        self.assertTrue(refs, f"no references found in {script.name} — pattern drifted")
        missing = []
        for ref in refs:
            if not (script.parent / ref).resolve().is_file():
                missing.append(f"{script.relative_to(REPO_ROOT)} -> {ref}")
        self.assertEqual(missing, [], f"unresolved references: {missing}")

    def test_build_sh_references_resolve(self):
        self.assert_references_resolve(
            BUILD_SH, r"(?:python3|source)\s+([\w./-]+\.(?:py|sh))"
        )

    def test_run_sh_references_resolve(self):
        self.assert_references_resolve(RUN_SH, r"((?:\.\.?/)[\w./-]+\.sh)")

    def test_install_deps_references_resolve(self):
        self.assert_references_resolve(
            INSTALL_DEPS, r"(?:python3 -m pip install -r|source|\.)\s+([\w./-]+\.(?:txt|sh))"
        )

    def test_build_sh_does_not_use_pre_restructure_paths(self):
        text = read(BUILD_SH)
        for stale in ("./download_utils.sh", "python3 generateWSALinks.py",
                      "python3 extractWSA.py", "python3 extractMagisk.py",
                      "python3 generateMagiskLink.py", "python3 fixGappsProp.py"):
            self.assertNotIn(stale, text, f"stale pre-E2 reference in build.sh: {stale}")


class TestRelativeAssetPathsResolve(unittest.TestCase):
    """Every quoted relative path in the toolchain must resolve from its script.

    This is the guard that would have caught the E2 breakage directly:
    ``../bin/x64/lspinit`` silently became ``upstream/bin/x64/lspinit``.
    """

    RELATIVE_PATH = re.compile(r'["\']((?:\.\.?/)[^"\'\s]+)["\']')

    BUILD_SCRIPTS = (
        REPO_ROOT / "tools" / "build.sh",
        REPO_ROOT / "tools" / "core" / "run.sh",
        REPO_ROOT / "tools" / "core" / "install_deps.sh",
        REPO_ROOT / "tools" / "core" / "download_utils.sh",
    )

    def _expand(self, ref: str) -> str:
        # Only $TARGET_ARCH is substituted: it is a build-time constant with a
        # fixed set of values, so both variants can be checked statically.
        return ref.replace("$TARGET_ARCH", "x64")

    def test_all_relative_paths_resolve(self):
        missing = []
        for script in self.BUILD_SCRIPTS:
            text = read(script)
            for match in self.RELATIVE_PATH.finditer(text):
                ref = self._expand(match.group(1))
                if "$" in ref:
                    continue  # runtime-computed path, not statically checkable
                if not (script.parent / ref).resolve().exists():
                    missing.append(f"{script.relative_to(REPO_ROOT)} -> {ref}")
        self.assertEqual(missing, [], f"unresolved relative paths: {missing}")

    def test_upstream_assets_are_referenced_where_they_live(self):
        text = read(BUILD_SH)
        for ref in (
            "../upstream/bin/$TARGET_ARCH/lspinit",
            "../upstream/bin/$TARGET_ARCH/makepri.exe",
            "../upstream/installer/Install.ps1",
            "../upstream/installer/Run.bat",
            "../upstream/installer/MakePri.ps1",
            "../upstream/xml/priconfig.xml",
        ):
            self.assertIn(ref, text, f"build.sh no longer references {ref}")
            resolved = REPO_ROOT / "tools" / ref.replace("$TARGET_ARCH", "x64")
            self.assertTrue(resolved.resolve().is_file(), f"missing asset: {ref}")

    def test_no_stale_pre_restructure_asset_paths(self):
        for script in self.BUILD_SCRIPTS:
            text = read(script)
            for stale in ("../bin/", "../installer/", "../xml/"):
                self.assertNotIn(
                    f'"{stale}',
                    text,
                    f"stale pre-E2 asset path in {script.name}: {stale}",
                )


class TestPythonPathAnchors(unittest.TestCase):
    """Post-E2, a core script's repo root is three levels up, not two."""

    def test_generate_wsa_links_anchors_at_repo_root(self):
        text = read(GENERATE_WSA_LINKS)
        self.assertIn("parent.parent.parent", text)
        self.assertNotIn("BASE_DIR", text)

    def test_generate_wsa_links_paths_exist(self):
        text = read(GENERATE_WSA_LINKS)
        self.assertIn('REPO_ROOT / "upstream" / "xml"', text)
        self.assertIn('"tools" / "update-check"', text)
        self.assertTrue((REPO_ROOT / "upstream" / "xml").is_dir())
        self.assertTrue((REPO_ROOT / "tools" / "update-check" / "env_helpers.py").is_file())

    def test_build_local_anchors_at_repo_root(self):
        text = read(BUILD_LOCAL)
        self.assertIn('repo_root = script_dir.parent', text)
        self.assertIn('upstream = repo_root / "upstream"', text)
        self.assertTrue((REPO_ROOT / "upstream").is_dir())


class TestVirtualenvPathAgreement(unittest.TestCase):
    """install_deps.sh creates the venv that build.sh activates — same path."""

    def test_install_deps_and_build_sh_agree_on_venv_location(self):
        build_text = read(BUILD_SH)
        deps_text = read(INSTALL_DEPS)

        self.assertIn('PYTHON_VENV_DIR="$(dirname "$PWD")/python3-env"', build_text)
        # install_deps.sh now lives in tools/core, so it must climb two levels.
        self.assertIn('PYTHON_VENV_DIR="$(cd "$(dirname "$0")/../.." && pwd)/python3-env"', deps_text)

    def test_venv_location_is_repo_root(self):
        # build.sh cds to tools/, so dirname($PWD) is the repository root.
        self.assertEqual(
            (REPO_ROOT / "tools").parent.resolve(), REPO_ROOT.resolve()
        )


class TestReleaseWorkflowAgreesWithToolchain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import yaml

        cls.workflow = yaml.safe_load(read(RELEASE_WORKFLOW))
        cls.text = read(RELEASE_WORKFLOW)

    def test_workflow_runs_build_sh_from_tools(self):
        self.assertIn("cd tools", self.text)
        self.assertIn("bash build.sh", self.text)
        self.assertTrue(BUILD_SH.is_file())

    def test_workflow_uploads_what_build_sh_writes(self):
        """build.sh sets OUTPUT_DIR=../output from tools/ -> <repo>/output."""
        build_text = read(BUILD_SH)
        self.assertIn('OUTPUT_DIR=../output', build_text)

        build_job = self.workflow["jobs"]["build-release-package"]
        upload = next(
            s for s in build_job["steps"] if s.get("uses", "").startswith("actions/upload-artifact")
        )
        self.assertIn("output/*.7z", upload["with"]["path"])

    def test_publish_job_waits_for_the_build(self):
        publish = self.workflow["jobs"]["validate-and-publish"]
        self.assertIn("build-release-package", publish["needs"])


if __name__ == "__main__":
    unittest.main()
