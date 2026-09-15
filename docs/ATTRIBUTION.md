# Emberbird Attribution (P0.1)

Emberbird builds on the work of many projects and communities. This file
records what came from where; registry provenance records tie each
generated release entry to the tooling that produced it.

## 1. Direct ancestors

| Project | What Emberbird inherits | Location |
|---|---|---|
| **WSABuilds** (MustardChef + contributors) | The build pipeline, dual-edition packaging, CI conventions, and the community this platform serves | `MagiskOnWSA/` scripts derive from the upstream project |
| **MagiskOnWSA** (upstream of upstream) | The original WSA-patching approach | Conceptual ancestor of `MagiskOnWSA/` scripts |

## 2. Components embedded in builds

| Component | Author/maintainer | Role | License |
|---|---|---|---|
| **Windows Subsystem for Android** | Microsoft | The subsystem itself (MSIX), downloaded unmodified and patched per the documented patch set | Proprietary — redistributed as published |
| **Magisk** | topjohnwu | Root solution for the standard edition | GPL-3.0 |
| **MindTheGapps** | MindTheGapps team | Optional Google apps image (pico) | Apache-2.0 |
| **WSA-Addon** community sidecars | Community | Hash sidecars and supplementary build assets | Per-upstream, audited per asset |

## 3. Build-time tooling

| Tool | Role | License |
|---|---|---|
| aria2 | Multi-connection downloads in the WSA build scripts | GPL-2.0 |
| 7-Zip | MSIX extraction and repackaging | LGPL-2.1 / unRAR restriction |
| Python 3 + jsonschema | Registry generator and release engine | PSF / MIT |
| GitHub Actions runners | CI for builds, tests, validation | Runner terms |

## 4. Documentation and research sources

| Source | Used for |
|---|---|
| Upstream WSABuilds issue tracker | Product pillars in `docs/EMBERBIRD_CHARTER.md` |
| Microsoft WSA documentation | Build prerequisites and compatibility notes |
| topjohnwu/magisk-files | Magisk release channel metadata |

## 4.1 Name

"Emberbird" was chosen after a collision check against existing projects
(no meaningful conflict found as of P0); it is a project name for the
*platform*, not for Microsoft's product, which is always referred to as
the Windows Subsystem for Android.

## 5. Corrections

If you are credited incorrectly or not at all, open an issue — attribution
errors are treated as release-metadata defects and fixed in the next
registry regeneration.
