"""Emberbird command-line interface (PH-20).

The CLI is deliberately a *surface*, not a second implementation: it owns
argument parsing and presentation, and delegates every fact to a platform
engine. That is what keeps it from drifting from the engines it reports on.
"""

__version__ = "1.0.0"

__all__ = ["__version__"]
