//! downloader.rs — Registry-to-staged-package pipeline (FB-3).
//!
//! Closes the install loop: a published registry asset is downloaded
//! (streamed, with `stage-progress` events), SHA-256-verified against the
//! registry hash (Artifact Identification Rule: identity = filename + sha256),
//! extracted to the staging area, and the AppxManifest is located for the
//! registration step. Every failure is honest; no fabricated success.
//!
//! Zero-Mock law: a hash mismatch deletes the archive and errors — unverified
//! content is never handed to the installer.

use crate::installer::find_appx_manifest;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::io::Write;
use std::path::{Path, PathBuf};

/// Tauri event name the frontend listens on for download/extract progress.
pub const STAGE_PROGRESS_EVENT: &str = "stage-progress";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, specta::Type)]
#[serde(rename_all = "snake_case")]
pub enum StagePhase {
    Downloading,
    Verifying,
    Extracting,
    Done,
}

#[derive(Debug, Clone, Serialize, Deserialize, specta::Type)]
pub struct StageProgress {
    pub phase: StagePhase,
    pub received_bytes: u64,
    pub total_bytes: u64,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, specta::Type)]
pub struct StagedAsset {
    pub archive_path: String,
    pub staged_path: String,
    pub manifest_path: String,
    pub sha256: String,
    pub size_bytes: u64,
}

/// Staging area for downloaded release packages (gitignored machine state).
pub fn staging_root() -> PathBuf {
    if let Ok(local_app_data) = std::env::var("LOCALAPPDATA") {
        if !local_app_data.trim().is_empty() {
            return PathBuf::from(local_app_data)
                .join("Emberbird")
                .join("staged");
        }
    }
    std::env::temp_dir().join("emberbird-staged")
}

/// Extract the artifact filename from a registry `source_url`.
pub fn filename_from_url(url: &str) -> Result<String, String> {
    let last = url.rsplit('/').next().unwrap_or("");
    let name = last.split('?').next().unwrap_or("");
    if name.trim().is_empty() {
        return Err("Download URL has no filename segment; cannot stage asset".to_string());
    }
    Ok(name.to_string())
}

/// Registry hashes are stored bare/lowercase; tolerate `sha256:` prefixes and
/// case drift but never whitespace.
pub fn normalize_sha256(expected: &str) -> String {
    let t = expected.trim();
    let t = if t.len() > 7 && t.as_bytes()[6] == b':' {
        &t[7..]
    } else {
        t
    };
    t.to_ascii_lowercase()
}

fn hex_string(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

/// Download `url`, stream it to the staging area with progress callbacks,
/// verify SHA-256 against the registry hash, extract, and locate the
/// AppxManifest. Any failure cleans up honestly.
pub async fn stage_asset<F>(
    url: &str,
    expected_sha256: &str,
    on_progress: F,
) -> Result<StagedAsset, String>
where
    F: Fn(&StageProgress),
{
    let filename = filename_from_url(url)?;
    let expected = normalize_sha256(expected_sha256);
    if expected.len() != 64 || !expected.chars().all(|c| c.is_ascii_hexdigit()) {
        return Err(
            "Registry asset carries no valid SHA-256; refusing to stage unverified content"
                .to_string(),
        );
    }

    let root = staging_root();
    std::fs::create_dir_all(&root).map_err(|e| {
        format!(
            "Failed to create staging directory {}: {}",
            root.display(),
            e
        )
    })?;
    let archive_path = root.join(&filename);

    // Phase 1: streamed download with rolling SHA-256.
    let mut resp = reqwest::get(url)
        .await
        .map_err(|e| format!("Download failed: {}", e))?;
    if !resp.status().is_success() {
        return Err(format!("Download failed: HTTP {}", resp.status()));
    }
    let total_bytes = resp.content_length().unwrap_or(0);

    on_progress(&StageProgress {
        phase: StagePhase::Downloading,
        received_bytes: 0,
        total_bytes,
        message: format!("Downloading {}", filename),
    });

    let mut file = std::fs::File::create(&archive_path).map_err(|e| {
        format!(
            "Failed to create archive file {}: {}",
            archive_path.display(),
            e
        )
    })?;
    let mut hasher = Sha256::new();
    let mut received: u64 = 0;
    let mut last_emit: u64 = 0;
    let emit_interval: u64 = 2 * 1024 * 1024; // 2 MiB

    loop {
        let chunk = match resp.chunk().await {
            Ok(Some(c)) => c,
            Ok(None) => break,
            Err(e) => {
                let _ = std::fs::remove_file(&archive_path);
                return Err(format!("Download stream failed: {}", e));
            }
        };
        hasher.update(&chunk);
        if let Err(e) = file.write_all(&chunk) {
            let _ = std::fs::remove_file(&archive_path);
            return Err(format!("Failed to write archive: {}", e));
        }
        received += chunk.len() as u64;
        if received - last_emit >= emit_interval {
            last_emit = received;
            on_progress(&StageProgress {
                phase: StagePhase::Downloading,
                received_bytes: received,
                total_bytes,
                message: format!(
                    "Downloading {} ({} / {} bytes)",
                    filename, received, total_bytes
                ),
            });
        }
    }
    let _ = file.flush();

    // Phase 2: SHA-256 verification against registry truth.
    on_progress(&StageProgress {
        phase: StagePhase::Verifying,
        received_bytes: received,
        total_bytes: received,
        message: format!("Verifying SHA-256 of {}", filename),
    });
    let actual = hex_string(&hasher.finalize());
    if actual != expected {
        let _ = std::fs::remove_file(&archive_path);
        return Err(format!(
            "SHA-256 verification failed for {}: downloaded {} but registry expects {}. \
             The archive was deleted; unverified content is never staged.",
            filename, actual, expected
        ));
    }

    // Phase 3: extraction to the staging area.
    let stem = filename.strip_suffix(".7z").unwrap_or(&filename);
    let staged_path = root.join(stem);
    on_progress(&StageProgress {
        phase: StagePhase::Extracting,
        received_bytes: received,
        total_bytes: received,
        message: format!("Extracting {} to staging area", filename),
    });
    extract_archive(&archive_path, &staged_path)?;

    // Phase 4: manifest discovery for the registration step (the shared
    // locator, so staging and registration can never disagree about layout).
    let manifest = find_appx_manifest(&staged_path)?;
    on_progress(&StageProgress {
        phase: StagePhase::Done,
        received_bytes: received,
        total_bytes: received,
        message: format!("Staged and verified: {}", manifest.display()),
    });

    Ok(StagedAsset {
        archive_path: archive_path.to_string_lossy().into_owned(),
        staged_path: staged_path.to_string_lossy().into_owned(),
        manifest_path: manifest.to_string_lossy().into_owned(),
        sha256: actual,
        size_bytes: received,
    })
}

/// Extract a 7z archive with whatever 7-Zip binary exists on PATH. An absent
/// binary is a hard error — no fabricated extraction.
fn extract_archive(archive: &Path, dest: &Path) -> Result<(), String> {
    if dest.exists() {
        std::fs::remove_dir_all(dest).map_err(|e| {
            format!(
                "Failed to clear previous staging dir {}: {}",
                dest.display(),
                e
            )
        })?;
    }
    std::fs::create_dir_all(dest)
        .map_err(|e| format!("Failed to create staging dir {}: {}", dest.display(), e))?;

    #[cfg(windows)]
    let candidates = ["7z.exe", "7za.exe"];
    #[cfg(not(windows))]
    let candidates = ["7z", "7za"];

    for bin in candidates {
        match std::process::Command::new(bin)
            .args([
                "x",
                "-y",
                &format!("-o{}", dest.display()),
                &archive.to_string_lossy(),
            ])
            .output()
        {
            Ok(output) if output.status.success() => return Ok(()),
            Ok(output) => {
                let stderr = String::from_utf8_lossy(&output.stderr);
                return Err(format!("Extraction with {} failed: {}", bin, stderr.trim()));
            }
            // Binary not present — try the next candidate.
            Err(_) => continue,
        }
    }
    Err(
        "No 7z/7za executable found on PATH. Install 7-Zip (https://www.7-zip.org) \
         to enable package staging."
            .to_string(),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn filename_from_url_extracts_registry_asset_names() {
        let url = "https://github.com/example/repo/releases/download/wsa-v2407.40000.4.0/WSA_2407.40000.4.0_x64.7z";
        assert_eq!(filename_from_url(url).unwrap(), "WSA_2407.40000.4.0_x64.7z");
        assert!(filename_from_url("https://example.com/").is_err());
        assert_eq!(
            filename_from_url("https://example.com/a.7z?token=x").unwrap(),
            "a.7z"
        );
    }

    #[test]
    fn normalize_sha256_tolerates_prefix_and_case() {
        assert_eq!(
            normalize_sha256(
                "SHA256:ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789"
            ),
            "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
        );
        assert_eq!(normalize_sha256("  abcd  "), "abcd");
    }

    #[test]
    fn staging_root_is_a_concrete_path() {
        let root = staging_root();
        assert!(root.file_name().is_some());
    }
}
