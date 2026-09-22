#!/usr/bin/env python3
"""TODO.md contract tests (WO-4b, Cycle S1; hardened in Cycle RA-1).

TODO.md is the single executable roadmap. These tests pin its binding
structure so the roadmap cannot silently decay:

- The Execution Contract must be present and complete.
- A phase may not claim COMPLETE while its exit checklist has unchecked
  items, unless the header explicitly annotates the pending item (e.g.
  CI ratification).
- Future phases must stay marked LOCKED.
- The execution-engine field vocabulary must exist.

Cycle RA-1 added the roadmap-integrity guards, because the superseded roadmap
had drifted in ways nothing could catch:

- No checkbox parent may be marked ``[x]`` while a descendant is unchecked.
- Every ``#### PH-*`` block must declare a Status and an Evidence line.
- A phase marked COMPLETE may contain no unchecked item, and every path it
  cites as evidence must exist on disk.
- A phase marked ABSENT may contain no checked item.
- The release ladder must be complete, and every phase must sit on it.
- Every legacy phase id (``FB-*``/``FX-*``/``QG-*``/``DX-*``/``UX-*``)
  referenced from source, tests or workflows must be resolvable in TODO.md.
- A capability that has no implementation must not be marked complete. Two
  such claims existed (``RuntimeProvider``, the ``emberbird`` CLI) and are
  pinned here as live assertions against the code, not just against prose.

Every guard is self-tested in ``TestGuardSelfCheck`` against synthetic
documents, so none of them can pass vacuously.

stdlib-only; runs in CI unchanged.
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TODO = REPO_ROOT / "TODO.md"

EXECUTION_CONTRACT_ITEMS = [
    "One active phase",
    "Phase guard",
    "Exit checklists",
    "Reality gates before merge",
    "Protected subsystems",
    "Status vocabulary",
    "Stop conditions",
    "Contracts frozen",
]

EXECUTION_ENGINE_FIELDS = ["STATUS", "BLOCKERS", "DEPENDENCIES", "FILES", "RISKS", "VALIDATION", "RESULT"]

PHASE_RE = re.compile(r"^### (.+)$", re.MULTILINE)
CHECKBOX_RE = re.compile(r"^- \[([ x!])\]", re.MULTILINE)

# --- Cycle RA-1 roadmap-integrity vocabulary -------------------------------

CHECKBOX_ANY_RE = re.compile(r"^(\s*)- \[([ x!])\] (.*)$")
PHASE_BLOCK_RE = re.compile(r"^#### (PH-\d+) · (.+)$", re.MULTILINE)
STATUS_RE = re.compile(r"\*\*Status:\*\*\s*`?([A-Z_]+)`?")
RELEASE_RE = re.compile(r"\*\*Release:\*\*\s*`([^`]+)`")
EVIDENCE_LINE_RE = re.compile(r"\*\*Evidence:\*\*\s*(.+)$", re.MULTILINE)
BACKTICK_RE = re.compile(r"`([^`]+)`")

VALID_STATUSES = {"COMPLETE", "PARTIAL", "ABSENT", "BLOCKED"}

# The canonical ladder. Order is binding: it is the release sequence.
LADDER = [
    ("0.3.x", "TRUTH"),
    ("0.4", "CONTROL"),
    ("0.5", "APPS"),
    ("0.6", "SAFE"),
    ("0.7", "INTELLIGENCE"),
    ("0.8", "PERFORMANCE"),
    ("0.9", "WINDOWS"),
    ("1.0", "PLATFORM"),
    ("2.0", "INDEPENDENCE"),
]

LEGACY_ID_RE = re.compile(r"\b(?:FB|FX|QG|DX|UX)-\d+[a-z]?\b")

# Directories that are vendored, generated, or otherwise not our source.
SKIP_DIRS = {
    ".git", "node_modules", "upstream", "target", "dist", "dist_clean",
    "__pycache__", ".astro", ".venv", "venv", "output", "download",
    "MagiskOnWSA", "MagiskOnWSAOld", "WSA_2407.40000.4.0_x64_vanilla_2",
}
CODE_SUFFIXES = {".rs", ".ts", ".tsx", ".mjs", ".js", ".py", ".ps1", ".sh"}
DOC_SUFFIXES = {".md"}
CONFIG_SUFFIXES = {".yml", ".yaml", ".toml"}

# This guard file necessarily names the symbols it guards, so scanning it would
# always match itself. It is the only file exempt from the scans.
SKIP_FILES = {Path("tests/test_todo_contract.py")}


def todo_text() -> str:
    return TODO.read_text(encoding="utf-8")


def iter_repo_files(suffixes):
    """Yield repo-relative paths with the given suffixes, skipping vendored trees."""
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        rel = path.relative_to(REPO_ROOT)
        if rel in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if rel.parts[:2] == ("docs", "archive"):
            continue
        if rel.parts[:3] == ("website", "src", "content"):
            continue
        yield rel


def read_repo_file(rel) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace")


# --- Pure checkers (self-tested below, so they cannot pass vacuously) -------


def checked_parents_with_unchecked_descendants(text: str):
    """Return descriptors for every ``[x]`` parent with unchecked descendants.

    Indentation defines the tree, which is how these lists are authored: a
    deeper line belongs to the nearest shallower line above it.
    """
    nodes = []
    for lineno, line in enumerate(text.split("\n"), 1):
        match = CHECKBOX_ANY_RE.match(line)
        if match:
            nodes.append({
                "indent": len(match.group(1)),
                "state": match.group(2),
                "text": match.group(3),
                "line": lineno,
                "kids": [],
            })

    roots, stack = [], []
    for node in nodes:
        while stack and stack[-1]["indent"] >= node["indent"]:
            stack.pop()
        (stack[-1]["kids"] if stack else roots).append(node)
        stack.append(node)

    violations = []

    def walk(node):
        bad = [kid for kid in node["kids"] if kid["state"] != "x"]
        if node["state"] == "x" and bad:
            for kid in bad:
                violations.append(
                    f"line {node['line']}: [x] {node['text'][:64]!r} "
                    f"-> unchecked line {kid['line']}: {kid['text'][:56]!r}"
                )
        for kid in node["kids"]:
            walk(kid)

    for root in roots:
        walk(root)
    return violations


def parse_phase_blocks(text: str):
    """Parse ``#### PH-NN · Title`` blocks into a dict keyed by phase id."""
    parts = PHASE_BLOCK_RE.split(text)
    blocks = {}
    for index in range(1, len(parts) - 2, 3):
        pid, title, body = parts[index], parts[index + 1], parts[index + 2]
        status = STATUS_RE.search(body)
        release = RELEASE_RE.search(body)
        evidence = EVIDENCE_LINE_RE.search(body)
        blocks[pid] = {
            "id": pid,
            "title": title.strip(),
            "status": status.group(1) if status else None,
            "release": release.group(1) if release else None,
            "evidence": evidence.group(1).strip() if evidence else None,
            "checked": len(re.findall(r"^\s*- \[x\]", body, re.MULTILINE)),
            "unchecked": len(re.findall(r"^\s*- \[[ !]\]", body, re.MULTILINE)),
        }
    return blocks


def missing_status_or_evidence(blocks):
    problems = []
    for block in sorted(blocks.values(), key=lambda b: b["id"]):
        if block["status"] not in VALID_STATUSES:
            problems.append(f"{block['id']} declares no valid Status ({block['status']!r})")
        if not block["evidence"]:
            problems.append(f"{block['id']} declares no Evidence line")
    return problems


def complete_phases_with_unchecked_items(blocks):
    return [
        f"{b['id']} is COMPLETE with {b['unchecked']} unchecked item(s)"
        for b in sorted(blocks.values(), key=lambda b: b["id"])
        if b["status"] == "COMPLETE" and b["unchecked"]
    ]


def absent_phases_with_checked_items(blocks):
    return [
        f"{b['id']} is ABSENT yet has {b['checked']} checked item(s)"
        for b in sorted(blocks.values(), key=lambda b: b["id"])
        if b["status"] == "ABSENT" and b["checked"]
    ]


def evidence_paths(evidence):
    """Backticked tokens that look like repo paths (contain a separator)."""
    return [token.strip() for token in BACKTICK_RE.findall(evidence or "") if "/" in token]


def evidence_path_problems(blocks, root):
    problems = []
    for block in sorted(blocks.values(), key=lambda b: b["id"]):
        paths = evidence_paths(block["evidence"])
        if block["status"] == "COMPLETE" and not paths:
            problems.append(f"{block['id']} is COMPLETE but cites no verifiable path")
        for rel in paths:
            if not (root / rel).exists():
                problems.append(f"{block['id']} cites a missing evidence path: {rel}")
    return problems


def ladder_problems(text):
    problems = []
    for version, name in LADDER:
        heading = f"### {version} — {name}"
        if heading not in text:
            problems.append(f"ladder milestone heading missing: {heading!r}")
    return problems


def off_ladder_phases(blocks):
    versions = {version for version, _ in LADDER}
    return [
        f"{b['id']} sits at {b['release']!r}, which is not on the ladder"
        for b in sorted(blocks.values(), key=lambda b: b["id"])
        if b["release"] not in versions
    ]


class TestExecutionContract(unittest.TestCase):
    def test_todo_exists(self):
        self.assertTrue(TODO.is_file(), "TODO.md must exist — it is the single executable roadmap")

    def test_all_execution_contract_items_present(self):
        text = todo_text()
        missing = [item for item in EXECUTION_CONTRACT_ITEMS if item not in text]
        self.assertEqual(missing, [], f"Execution Contract items missing from TODO.md: {missing}")

    def test_execution_engine_fields_documented(self):
        text = todo_text()
        missing = [f for f in EXECUTION_ENGINE_FIELDS if f not in text]
        self.assertEqual(missing, [], f"execution-engine fields missing from TODO.md: {missing}")

    def test_truth_hierarchy_documented(self):
        text = todo_text().lower()
        for needle in ["l1", "published release assets", "reality always overrides documentation"]:
            self.assertIn(needle, text, f"truth-hierarchy element missing: {needle}")


class TestPhaseHonesty(unittest.TestCase):
    """A phase section claiming COMPLETE must not hide unchecked items."""

    def test_no_phase_claims_complete_with_silent_unchecked_items(self):
        text = todo_text()
        sections = PHASE_RE.split(text)
        # sections = [prefix, title1, body1, title2, body2, ...]
        problems = []
        for i in range(1, len(sections) - 1, 2):
            title, body = sections[i], sections[i + 1]
            unchecked = len([m for m in CHECKBOX_RE.findall(body) if m != "x"])
            if unchecked and "complete" in title.lower() and "pending" not in title.lower():
                problems.append(f"phase '{title}' claims COMPLETE with {unchecked} unchecked item(s)")
        self.assertEqual(problems, [], "\n".join(problems))

    def test_future_phases_marked_locked(self):
        text = todo_text()
        self.assertIn("Future phases (LOCKED", text, "Part IV must keep future phases marked LOCKED")

    def test_recommended_policy_stated(self):
        text = todo_text().lower()
        self.assertIn("recommended", text)
        self.assertIn("policy", text)
        self.assertIn("latest", text)

    def test_artifact_identity_rule_stated(self):
        text = todo_text()
        self.assertIn("sha256", text)
        self.assertIn("filename", text)


class TestRoadmapIntegrity(unittest.TestCase):
    """Cycle RA-1: the roadmap's own claims must be structurally sound."""

    def test_no_checked_parent_with_unchecked_descendants(self):
        violations = checked_parents_with_unchecked_descendants(todo_text())
        self.assertEqual(
            violations, [],
            "a parent checkbox may not be [x] while a child is unchecked:\n" + "\n".join(violations),
        )

    def test_phase_blocks_are_present_and_well_formed(self):
        blocks = parse_phase_blocks(todo_text())
        # A parse count guards against the guard itself matching nothing.
        self.assertEqual(
            len(blocks), 51,
            f"expected the 51-phase catalogue (PH-00…PH-50), parsed {len(blocks)}",
        )
        problems = missing_status_or_evidence(blocks)
        self.assertEqual(problems, [], "\n".join(problems))

    def test_no_complete_phase_hides_unchecked_items(self):
        problems = complete_phases_with_unchecked_items(parse_phase_blocks(todo_text()))
        self.assertEqual(problems, [], "\n".join(problems))

    def test_no_absent_phase_claims_checked_items(self):
        problems = absent_phases_with_checked_items(parse_phase_blocks(todo_text()))
        self.assertEqual(problems, [], "\n".join(problems))

    def test_complete_phase_evidence_paths_exist(self):
        problems = evidence_path_problems(parse_phase_blocks(todo_text()), REPO_ROOT)
        self.assertEqual(problems, [], "\n".join(problems))

    def test_release_ladder_is_contiguous(self):
        problems = ladder_problems(todo_text())
        self.assertEqual(problems, [], "\n".join(problems))

    def test_every_phase_sits_on_the_ladder(self):
        problems = off_ladder_phases(parse_phase_blocks(todo_text()))
        self.assertEqual(problems, [], "\n".join(problems))

    def test_runtime_provider_claim_matches_the_code(self):
        """PH-22 was once marked complete with no implementation in any language.

        The guard is bidirectional: the roadmap and the repository must agree in
        both directions, so neither a false completion claim nor a silent
        implementation can pass unnoticed.
        """
        status = parse_phase_blocks(todo_text())["PH-22"]["status"]
        hits = [
            str(rel)
            for rel in iter_repo_files(CODE_SUFFIXES)
            if "RuntimeProvider" in read_repo_file(rel)
        ]
        if status == "ABSENT":
            self.assertEqual(
                hits, [],
                "a RuntimeProvider implementation now exists — promote PH-22 from ABSENT: "
                + ", ".join(hits),
            )
        else:
            self.assertTrue(
                hits,
                f"PH-22 is {status} but no RuntimeProvider implementation exists",
            )

    def test_cli_claim_matches_the_code(self):
        """PH-20 was once marked complete with no entry point at all (Cycle RA-1).

        Same bidirectional rule: a declared entry point must have an
        implementation, and a claimed implementation must have an entry point.
        """
        status = parse_phase_blocks(todo_text())["PH-20"]["status"]
        entry_points = [
            str(rel)
            for rel in iter_repo_files(CONFIG_SUFFIXES)
            if re.search(r"^\s*emberbird\s*=", read_repo_file(rel), re.MULTILINE)
        ]
        implementation = REPO_ROOT / "platform" / "cli" / "emberbird" / "__main__.py"
        if status == "ABSENT":
            self.assertEqual(
                entry_points, [],
                "an emberbird entry point now exists — promote PH-20 from ABSENT: "
                + ", ".join(entry_points),
            )
        else:
            self.assertTrue(
                entry_points,
                f"PH-20 is {status} but no emberbird entry point is declared",
            )
            self.assertTrue(
                implementation.is_file(),
                f"PH-20 is {status} but {implementation} does not exist",
            )

    def test_legacy_phase_ids_are_resolvable(self):
        """Legacy ids are referenced from source; the roadmap must define them."""
        text = todo_text()
        defined = set(LEGACY_ID_RE.findall(text))
        referenced = set()
        for rel in iter_repo_files(CODE_SUFFIXES | DOC_SUFFIXES | CONFIG_SUFFIXES):
            if rel == Path("TODO.md"):
                continue
            referenced.update(LEGACY_ID_RE.findall(read_repo_file(rel)))

        orphans = sorted(referenced - defined)
        self.assertEqual(
            orphans, [],
            "phase ids referenced from source but absent from TODO.md (never orphan a reference): "
            + ", ".join(orphans),
        )
        # The crosswalk must exist so a renumber cannot silently break the above.
        self.assertIn("Legacy crosswalk", text)
        self.assertGreater(len(referenced), 0, "no legacy ids were scanned — the scan is broken")


class TestGuardSelfCheck(unittest.TestCase):
    """Feed each guard a clean and a violating document, so none is vacuous."""

    VIOLATING = (
        "#### PH-77 · Synthetic\n"
        "- **Release:** `9.9` · **Track:** test · **Status:** COMPLETE\n"
        "- **Goal:** prove the guard bites.\n"
        "- **Evidence:** `tests/does-not-exist/synthetic.py`\n"
        "- [x] implemented\n"
        "- [ ] not implemented\n"
    )
    ABSENT_CLAIMING = (
        "#### PH-78 · Synthetic absent\n"
        "- **Release:** `0.3.x` · **Track:** test · **Status:** ABSENT\n"
        "- **Goal:** prove the absent guard bites.\n"
        "- **Evidence:** NONE — NOT IMPLEMENTED\n"
        "- [x] this should not be checked\n"
    )

    def test_parent_child_guard_bites(self):
        doc = (
            "- [x] **Parent group**\n"
            "    - [x] done child\n"
            "    - [ ] open child\n"
        )
        self.assertTrue(checked_parents_with_unchecked_descendants(doc))
        clean = (
            "- [x] **Parent group**\n"
            "    - [x] done child\n"
            "    - [x] other child\n"
        )
        self.assertEqual(checked_parents_with_unchecked_descendants(clean), [])

    def test_complete_and_absent_guards_bite(self):
        blocks = parse_phase_blocks(self.VIOLATING)
        self.assertTrue(complete_phases_with_unchecked_items(blocks))
        self.assertTrue(evidence_path_problems(blocks, REPO_ROOT))
        self.assertTrue(missing_status_or_evidence(parse_phase_blocks(
            "#### PH-79 · No metadata\n- [ ] nothing declared\n")))

        absent_blocks = parse_phase_blocks(self.ABSENT_CLAIMING)
        self.assertTrue(absent_phases_with_checked_items(absent_blocks))

    def test_clean_synthetic_phase_passes_every_guard(self):
        clean = (
            "#### PH-80 · Synthetic clean\n"
            "- **Release:** `0.3.x` · **Track:** test · **Status:** PARTIAL\n"
            "- **Goal:** satisfy every guard.\n"
            "- **Evidence:** `tests/test_todo_contract.py`\n"
            "- [x] implemented\n"
            "- [ ] remaining\n"
        )
        blocks = parse_phase_blocks(clean)
        self.assertEqual(missing_status_or_evidence(blocks), [])
        self.assertEqual(complete_phases_with_unchecked_items(blocks), [])
        self.assertEqual(absent_phases_with_checked_items(blocks), [])
        self.assertEqual(evidence_path_problems(blocks, REPO_ROOT), [])
        self.assertEqual(off_ladder_phases(blocks), [])

    def test_ladder_guard_bites(self):
        self.assertTrue(ladder_problems("no ladder here"))
        self.assertEqual(ladder_problems(todo_text()), [])


if __name__ == "__main__":
    unittest.main()
