# Ember Release Engine (Metadata Service, P0.4)

The importable Python package lives at `platform/release_engine/` (underscore):
hyphens are illegal in Python module names, so `python -m platform.release_engine
validate` resolves there. This directory holds the service project definition.

## Capabilities (P0 contract)

- `latest_wsa()`, `latest_manager()` - newest published release per kind
- `by_channel()`, `by_edition()`, `by_tag()`, `by_id()` - filtered lookups
- `hash_for()` - asset hash lookup by filename (and cut hash when ambiguous)
- `load()` - registry load + integrity checks (lifecycle references, hash
  well-formedness, recommended uniqueness, vault agreement)

## Registry Independence

This service reads `data/releases/releases.json` from disk ONLY. It performs
zero network access. Website, Manager, Winget and CLI consume the registry
through this contract - never through the GitHub API.
