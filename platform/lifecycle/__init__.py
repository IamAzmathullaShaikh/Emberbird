"""Runtime lifecycle snapshot reader (PH-02 engine's Python side, PH-20/PH-21).

The Rust core (`apps/manager/src-tauri/src/runtime_state.rs`) owns the
lifecycle: it derives state, applies the recovery rules and *writes* the
snapshot. This module is the read-side contract: it reads the same file, with
the same schema version, the same SCREAMING_SNAKE_CASE wire names and the same
recovery rules — pinned against the Rust source by a test, so the two cannot
drift.

Zero-Mock law: nothing here invents state. A missing snapshot is reported as
absent; a corrupt or future-schema snapshot raises rather than being guessed
into something optimistic; recovery never claims more than the persisted
evidence supports.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

#: Must match ``LIFECYCLE_SCHEMA_VERSION`` in ``runtime_state.rs``.
SCHEMA_VERSION = 1

#: Wire name for every lifecycle state, mirroring serde's
#: ``rename_all = "SCREAMING_SNAKE_CASE"`` on the Rust ``RuntimeState`` enum.
KNOWN_STATES: frozenset[str] = frozenset(
    {
        "UNKNOWN",
        "NOT_INSTALLED",
        "CHECKING",
        "INSTALLING",
        "INSTALLED",
        "STARTING",
        "RUNNING",
        "STOPPING",
        "STOPPED",
        "DEGRADED",
        "BROKEN",
        "UPDATING",
        "ROLLING_BACK",
        "UNINSTALLING",
    }
)

#: In-flight states — a recovered state may never be one of these.
BUSY_STATES: frozenset[str] = frozenset(
    {"CHECKING", "INSTALLING", "STARTING", "STOPPING", "UPDATING", "ROLLING_BACK", "UNINSTALLING"}
)

#: Recovery rules, mirroring Rust ``fn reconcile`` in ``runtime_state.rs``:
#: a restart may recover a state to something *less* specific, never more.
#: ``None`` targets mean "restored exactly". Pinned to the Rust source by
#: ``tests/test_lifecycle.py::test_recovery_rules_match_the_rust_engine``.
RECOVERY_RULES: dict[str, tuple[str | None, str | None]] = {
    # Nothing a restart can invalidate: restored exactly.
    "UNKNOWN": (None, None),
    "NOT_INSTALLED": (None, None),
    "INSTALLED": (None, None),
    "BROKEN": (None, None),
    # In flight when the process ended: re-check reality.
    "CHECKING": ("UNKNOWN", "RE_DETECT"),
    "INSTALLING": ("UNKNOWN", "RE_DETECT"),
    "UNINSTALLING": ("UNKNOWN", "RE_DETECT"),
    # The change did not finish: a fault is present; undo it first.
    "UPDATING": ("BROKEN", "ROLL_BACK"),
    "ROLLING_BACK": ("BROKEN", "ROLL_BACK"),
    # Whether the runtime runs cannot survive a restart: start it to prove it.
    "STARTING": ("INSTALLED", "RESTART"),
    "STOPPING": ("INSTALLED", "RESTART"),
    "RUNNING": ("INSTALLED", "RESTART"),
    "STOPPED": ("INSTALLED", "RESTART"),
    # A fault cannot be confirmed across a restart, only re-checked.
    "DEGRADED": ("INSTALLED", "RE_DETECT"),
}

#: (The outcome — ``RESTORED`` / ``RE_ESTABLISHED`` / ``INTERRUPTED`` — is
#: derived the way the Rust engine does it: an outcome is ``INTERRUPTED``
#: exactly when the persisted state was in flight, i.e. in ``BUSY_STATES``.)


class LifecycleSnapshotError(Exception):
    """The snapshot exists but cannot be trusted. Never silently ignored."""


def default_snapshot_path() -> Path:
    """The Rust engine's snapshot path.

    ``%LOCALAPPDATA%\\Emberbird\\lifecycle.json``, overridable via
    ``EMBERBIRD_LIFECYCLE_PATH`` (useful for tests and for pointing the CLI at
    a snapshot from another machine).
    """
    override = os.environ.get("EMBERBIRD_LIFECYCLE_PATH")
    if override:
        return Path(override)
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        raise LifecycleSnapshotError("LOCALAPPDATA is not set; cannot locate the lifecycle snapshot")
    return Path(base) / "Emberbird" / "lifecycle.json"


def read_snapshot(path: Path) -> dict[str, Any] | None:
    """Read and validate a persisted lifecycle snapshot.

    Returns ``None`` when no snapshot exists (absence is evidence, not an
    error). Raises :class:`LifecycleSnapshotError` for malformed content or a
    schema this build cannot read — the difference between "we do not know"
    and "we cannot tell".
    """
    if not path.is_file():
        return None
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LifecycleSnapshotError(f"lifecycle snapshot is not valid JSON: {exc}") from exc
    if not isinstance(body, dict):
        raise LifecycleSnapshotError("lifecycle snapshot is not a JSON object")
    version = body.get("version")
    if not isinstance(version, int):
        raise LifecycleSnapshotError(f"lifecycle snapshot has no integer schema version: {version!r}")
    if version != SCHEMA_VERSION:
        raise LifecycleSnapshotError(
            f"unsupported lifecycle schema version {version} (this tool reads {SCHEMA_VERSION})"
        )
    state = body.get("state")
    if not isinstance(state, str) or state not in KNOWN_STATES:
        raise LifecycleSnapshotError(f"lifecycle snapshot carries an unknown state: {state!r}")
    history = body.get("history", [])
    if not isinstance(history, list):
        raise LifecycleSnapshotError("lifecycle snapshot history is not a list")
    for change in history:
        if not isinstance(change, dict) or not {"from", "to", "at", "reason"} <= set(change):
            raise LifecycleSnapshotError(f"lifecycle history entry is malformed: {change!r}")
    return body


def recover(state: str) -> dict[str, Any]:
    """Apply the recovery rules to a persisted state.

    Mirrors Rust ``RuntimeStateMachine::recover``: recovery is a re-baselining,
    not a transition — the result may be *less* specific than what was
    persisted, never more.
    """
    if state not in RECOVERY_RULES:
        raise LifecycleSnapshotError(f"no recovery rule for state {state!r}")
    presumed, action = RECOVERY_RULES[state]
    if presumed is None:
        return {"was": state, "presumed": state, "action": None, "outcome": "RESTORED"}
    outcome = "INTERRUPTED" if state in BUSY_STATES else "RE_ESTABLISHED"
    return {
        "was": state,
        "presumed": presumed,
        "action": action,
        "outcome": outcome,
    }


def describe(path: Path | None = None) -> dict[str, Any]:
    """Full read-side description: presence, recovery verdict, audit trail."""
    path = path or default_snapshot_path()
    snapshot = read_snapshot(path)
    if snapshot is None:
        return {"snapshot_present": False, "path": str(path)}
    verdict = recover(snapshot["state"])
    history = snapshot.get("history", [])
    return {
        "snapshot_present": True,
        "path": str(path),
        "schema_version": snapshot["version"],
        "recovery": verdict,
        "trail": history,
        "last_move_at": history[-1]["at"] if history else None,
    }
