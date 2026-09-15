# Emberbird registry fixture - MAPPED TO PUBLISHED REALITY (L1 sources):
# tag wsa-v2311.40000.5.0 ships BOTH editions; Windows_11_2407.40000.4.0 ships
# a separate standard cut with a different hash. Registry entries are (tag x edition).
FIXTURE = {
    "schema_version": 1,
    "migration_version": 2,
    "compatibility_level": "backward",
    "generation": {
        "tool": "tests/fixture.py",
        "mode": "test-fixture",
        "source": "synthetic reality-mapped fixture",
        "generated_at": "2026-09-15T00:00:00Z",
    },
    "releases": [
        {
            "release_id": "wsa-2311-standard",
            "tag": "wsa-v2311.40000.5.0",
            "kind": "subsystem",
            "wsa_version": "2407.40000.4.0",
            "channel": "retail",
            "edition": "standard",
            "architectures": ["x64"],
            "root_solution": "magisk",
            "gapps_variant": "pico",
            "status": "published",
            "published_at": "2026-09-13T23:06:31Z",
            "provenance": {
                "tool": "tests/fixture.py",
                "mode": "test-fixture",
                "generated_at": "2026-09-15T00:00:00Z",
            },
            "recommended": True,
            "assets": [
                {
                    "filename": "WSA_2407.40000.4.0_x64.7z",
                    "sha256": "ea95b7ed0c94bae65ef26bb403244a13540e47a7f78bf9f655ab65b13ff38c03",
                    "arch": "x64",
                    "role": "package",
                    "source_url": "https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/wsa-v2311.40000.5.0/WSA_2407.40000.4.0_x64.7z",
                    "source_type": "derived",
                    "hash_source": "published-manifest",
                    "verified_at": "2026-09-15T00:00:00Z",
                    "size_bytes": 770223955
                }
            ],
            "validation_reports": [
                {"report_type": "magisk", "result": "VERIFIED", "report_file": "magisk-validation-report.json"}
            ]
        },
        {
            "release_id": "wsa-2311-banking",
            "tag": "wsa-v2311.40000.5.0",
            "kind": "subsystem",
            "wsa_version": "2407.40000.4.0",
            "channel": "retail",
            "edition": "banking",
            "architectures": ["x64"],
            "root_solution": "none",
            "gapps_variant": "pico",
            "status": "published",
            "published_at": "2026-09-13T23:06:31Z",
            "provenance": {
                "tool": "tests/fixture.py",
                "mode": "test-fixture",
                "generated_at": "2026-09-15T00:00:00Z",
            },
            "assets": [
                {
                    "filename": "WSA_2407.40000.4.0_x64_vanilla.7z",
                    "sha256": "fc671cdab4d486a0a830196957cf9614f320fe8936d5d6d22f25cf62298c0cac",
                    "arch": "x64",
                    "role": "package",
                    "source_url": "https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/wsa-v2311.40000.5.0/WSA_2407.40000.4.0_x64_vanilla.7z",
                    "source_type": "derived",
                    "hash_source": "published-manifest",
                    "verified_at": "2026-09-15T00:00:00Z",
                    "size_bytes": 755302772
                }
            ]
        },
        {
            "release_id": "manager-0.2.2",
            "tag": "v0.2.2",
            "kind": "manager",
            "channel": "stable",
            "edition": "manager",
            "architectures": ["x64"],
            "status": "published",
            "published_at": "2026-09-14T00:00:00Z",
            "provenance": {
                "tool": "tests/fixture.py",
                "mode": "test-fixture",
                "generated_at": "2026-09-15T00:00:00Z",
            },
            "assets": [
                {
                    "filename": "WSABuildsManager-Setup-0.2.2-x64.exe",
                    "sha256": "887443bad0aeb3eec04ff367b4768edad2cc0e1b2fcd6b9b255f5bfd3181466a",
                    "arch": "x64",
                    "role": "package",
                    "source_url": "https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/v0.2.2/WSABuildsManager-Setup-0.2.2-x64.exe",
                    "source_type": "generated",
                    "hash_source": "sidecar",
                    "verified_at": "2026-09-15T00:00:00Z",
                    "size_bytes": 2548160
                }
            ]
        }
    ],
    "vault": [
        {
            "artifact": "WSA_2407.40000.4.0_x64.7z",
            "source_url": "https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/wsa-v2311.40000.5.0/WSA_2407.40000.4.0_x64.7z",
            "sha256": "ea95b7ed0c94bae65ef26bb403244a13540e47a7f78bf9f655ab65b13ff38c03",
            "mirror_status": "unverified",
            "last_verified_at": "2026-09-15T00:00:00Z",
            "availability_score": 100
        }
    ]
}
