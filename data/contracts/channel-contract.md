# Emberbird Channel Contract

**Law:** channel semantics are defined here and nowhere else. Consumers must
never infer meaning from the token spelling.

| Token | Meaning | Source of packages |
|---|---|---|
| `stable` | Default recommendation for the desktop manager. What most users should install. | Emberbird-signed manager builds |
| `retail` | Mirrors the Microsoft retail feed for the Windows Subsystem for Android. | Microsoft FE3 delivery feed (via `generateWSALinks.py`) |
| `RP` | Release Preview channel of the Windows Insider program. | Microsoft FE3 delivery feed |
| `WIS` | Insider Slow channel (Beta). | Microsoft FE3 delivery feed |
| `WIF` | Insider Fast channel (Dev). | Microsoft FE3 delivery feed |

## Synonym note (historical)

`retail` (WSA feed naming, `generateWSALinks.py`) and `stable` (manager naming,
`deployment/version.json`) both denote the production channel. The registry
records which naming the *release kind* uses: subsystem releases use
`retail`, manager releases use `stable`. They are distinct tokens by design so
the provenance of the channel decision stays visible; treat them as synonyms
only at the "is this production?" question level, never when filtering.

## Consumer rules

1. Do not add channel tokens without amending this contract (Registry
   Governance applies — schema change + review).
2. Do not map unknown tokens to `stable` silently; reject them loudly.
3. The `recommended` release flag (schema) is orthogonal to channel: at most
   one recommended release per channel+edition pair (validator-enforced).
