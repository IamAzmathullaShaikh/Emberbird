"""Test helper: import scripts/build_registry.py as a module.

scripts/ is not a package (no __init__.py by design — its scripts are
entry points), so tests that exercise the generator add its directory to
sys.path and import it once.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

_loaded = None


def load_generator():
    """Return the build_registry module (imported once, cached)."""
    global _loaded
    if _loaded is None:
        import build_registry as _gen

        _loaded = _gen
    return _loaded
