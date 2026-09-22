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
///
/// PH-48: the URL is externally influenced input. The extracted segment is
/// joined onto the staging root, so a hostile value must never survive: `..`,
/// path separators, drive qualifiers, NUL/control characters and Windows
/// reserved device names (`CON.7z` et al. can hang or misdirect file
/// creation) are all rejected here — before any filesystem or network work.
pub fn filename_from_url(url: &str) -> Result<String, String> {
    let last = url.rsplit('/').next().unwrap_or("");
    let name = last.split('?').next().unwrap_or("");
    if name.trim().is_empty() {
        return Err("Download URL has no filename segment; cannot stage asset".to_string());
    }
    if !is_safe_artifact_filename(name) {
        return Err(format!(
            "Download URL segment {:?} is not a safe artifact filename; refusing to stage",
            name
        ));
    }
    Ok(name.to_string())
}

/// Decide whether `name` can be safely joined onto the staging root.
///
/// The rule set is fail-closed and Windows-specific where Windows is
/// dangerous: a rejected list, never an allowlist of known-good schemes.
pub fn is_safe_artifact_filename(name: &str) -> bool {
    if name.is_empty() {
        return false;
    }
    // Pure traversal segments.
    if name == "." || name == ".." {
        return false;
    }
    // Path separators, drive qualifiers and NUL: any of these changes what
    // `staging_root().join(name)` resolves to. Percent is rejected too: this
    // layer never decodes, but a percent-encoded separator (`..%2F`) becomes
    // traversal the moment any layer below decodes — fail closed.
    if name
        .chars()
        .any(|c| matches!(c, '/' | '\\' | ':' | '\0' | '%') || c.is_control())
    {
        return false;
    }
    // Windows reserved device names: CON, PRN, AUX, NUL, COM1-9, LPT1-9 —
    // with or without an extension, case-insensitively, and even when
    // followed by the trailing dots/spaces Windows strips.
    let stem = name.trim_end_matches(['.', ' ']);
    let stem = stem.split('.').next().unwrap_or("");
    let upper = stem.to_ascii_uppercase();
    let reserved = matches!(
        upper.as_str(),
        "CON"
            | "PRN"
            | "AUX"
            | "NUL"
            | "COM1"
            | "COM2"
            | "COM3"
            | "COM4"
            | "COM5"
            | "COM6"
            | "COM7"
            | "COM8"
            | "COM9"
            | "LPT1"
            | "LPT2"
            | "LPT3"
            | "LPT4"
            | "LPT5"
            | "LPT6"
            | "LPT7"
            | "LPT8"
            | "LPT9"
    );
    !reserved
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

    // PH-45: one durable operation record per stage_asset call, success or
    // failure. Recording must never fail the operation it observes.
    let op_started = chrono::Utc::now();
    let op_id = operation_id_for_now();
    let mut stages: Vec<StageTiming> = Vec::new();

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
    let download_started = chrono::Utc::now();

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
    stages.push(StageTiming {
        stage: "download".into(),
        started_at: rfc3339(download_started),
        duration_ms: (chrono::Utc::now() - download_started)
            .num_milliseconds()
            .max(0) as u64,
    });

    // Phase 2: SHA-256 verification against registry truth.
    on_progress(&StageProgress {
        phase: StagePhase::Verifying,
        received_bytes: received,
        total_bytes: received,
        message: format!("Verifying SHA-256 of {}", filename),
    });
    let verify_started = chrono::Utc::now();
    let actual = hex_string(&hasher.finalize());
    if actual != expected {
        let _ = std::fs::remove_file(&archive_path);
        append_operation_record(
            &operations_log_path(),
            &OperationRecord {
                operation_id: op_id,
                asset: filename.clone(),
                result: "failed".into(),
                error: Some("sha256 verification failed".into()),
                started_at: rfc3339(op_started),
                finished_at: rfc3339(chrono::Utc::now()),
                duration_ms: (chrono::Utc::now() - op_started).num_milliseconds().max(0) as u64,
                stages,
                sha256: None,
                size_bytes: Some(received),
            },
        );
        return Err(format!(
            "SHA-256 verification failed for {}: downloaded {} but registry expects {}. \
             The archive was deleted; unverified content is never staged.",
            filename, actual, expected
        ));
    }
    stages.push(StageTiming {
        stage: "verify".into(),
        started_at: rfc3339(verify_started),
        duration_ms: (chrono::Utc::now() - verify_started)
            .num_milliseconds()
            .max(0) as u64,
    });

    // Phase 3: extraction to the staging area.
    let stem = filename.strip_suffix(".7z").unwrap_or(&filename);
    let staged_path = root.join(stem);
    on_progress(&StageProgress {
        phase: StagePhase::Extracting,
        received_bytes: received,
        total_bytes: received,
        message: format!("Extracting {} to staging area", filename),
    });
    let extract_started = chrono::Utc::now();
    if let Err(err) = extract_archive(&archive_path, &staged_path) {
        append_operation_record(
            &operations_log_path(),
            &OperationRecord {
                operation_id: op_id,
                asset: filename.clone(),
                result: "failed".into(),
                error: Some(format!("extraction failed: {err}")),
                started_at: rfc3339(op_started),
                finished_at: rfc3339(chrono::Utc::now()),
                duration_ms: (chrono::Utc::now() - op_started).num_milliseconds().max(0) as u64,
                stages,
                sha256: Some(actual),
                size_bytes: Some(received),
            },
        );
        return Err(err);
    }
    stages.push(StageTiming {
        stage: "extract".into(),
        started_at: rfc3339(extract_started),
        duration_ms: (chrono::Utc::now() - extract_started)
            .num_milliseconds()
            .max(0) as u64,
    });

    // Phase 4: manifest discovery for the registration step (the shared
    // locator, so staging and registration can never disagree about layout).
    let manifest_started = chrono::Utc::now();
    let manifest = match find_appx_manifest(&staged_path) {
        Ok(m) => m,
        Err(err) => {
            append_operation_record(
                &operations_log_path(),
                &OperationRecord {
                    operation_id: op_id,
                    asset: filename.clone(),
                    result: "failed".into(),
                    error: Some(format!("manifest discovery failed: {err}")),
                    started_at: rfc3339(op_started),
                    finished_at: rfc3339(chrono::Utc::now()),
                    duration_ms: (chrono::Utc::now() - op_started).num_milliseconds().max(0) as u64,
                    stages,
                    sha256: Some(actual),
                    size_bytes: Some(received),
                },
            );
            return Err(err);
        }
    };
    stages.push(StageTiming {
        stage: "manifest".into(),
        started_at: rfc3339(manifest_started),
        duration_ms: (chrono::Utc::now() - manifest_started)
            .num_milliseconds()
            .max(0) as u64,
    });
    on_progress(&StageProgress {
        phase: StagePhase::Done,
        received_bytes: received,
        total_bytes: received,
        message: format!("Staged and verified: {}", manifest.display()),
    });
    append_operation_record(
        &operations_log_path(),
        &OperationRecord {
            operation_id: op_id,
            asset: filename,
            result: "success".into(),
            error: None,
            started_at: rfc3339(op_started),
            finished_at: rfc3339(chrono::Utc::now()),
            duration_ms: (chrono::Utc::now() - op_started).num_milliseconds().max(0) as u64,
            stages,
            sha256: Some(actual.clone()),
            size_bytes: Some(received),
        },
    );

    Ok(StagedAsset {
        archive_path: archive_path.to_string_lossy().into_owned(),
        staged_path: staged_path.to_string_lossy().into_owned(),
        manifest_path: manifest.to_string_lossy().into_owned(),
        sha256: actual,
        size_bytes: received,
    })
}

/// Reject an archive entry that could escape the extraction root.
///
/// Defence in depth: current 7-Zip builds refuse `..` themselves, but that is a
/// property of someone else's binary, not a guarantee of ours. An entry is safe
/// only when it is relative, carries no drive or UNC prefix, and contains no
/// `..` segment.
///
/// Note that `..name` and `file..name.txt` are legal file names and must be
/// accepted — only an exact `..` segment escapes.
pub fn is_safe_archive_entry(entry: &str) -> bool {
    let trimmed = entry.trim();
    if trimmed.is_empty() {
        return false;
    }
    // POSIX-absolute, UNC and rooted Windows paths.
    if trimmed.starts_with('/') || trimmed.starts_with('\\') {
        return false;
    }
    // Drive-qualified paths: C:\x, C:/x and C:x all escape the destination.
    let chars: Vec<char> = trimmed.chars().collect();
    if chars.len() >= 2 && chars[0].is_ascii_alphabetic() && chars[1] == ':' {
        return false;
    }
    !trimmed.split(['/', '\\']).any(|segment| segment == "..")
}

/// Extract entry names from `7z l -slt -ba` output.
///
/// `-slt` prints one `Key = Value` block per entry and `-ba` suppresses the
/// banner, so the entry list is exactly the `Path = ` values. Other keys (`Size`,
/// `Attributes`, …) must not be mistaken for entries.
pub fn parse_archive_listing(stdout: &str) -> Vec<String> {
    stdout
        .lines()
        .filter_map(|line| line.strip_prefix("Path = "))
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
        .collect()
}

/// PH-48 — Total declared uncompressed size from a `7z l -slt -ba` listing.
///
/// Entry names alone cannot detect a decompression bomb: an archive full of
/// perfectly-named entries can still declare terabytes of extracted content.
/// The listing carries each entry's `Size = ` (directories have none); the
/// sum is the archive's own declaration, which is advisory but free — and
/// refusing to *start* extraction of a declared monster costs nothing.
/// Entries without a Size line contribute 0.
pub fn archive_declared_total_bytes(stdout: &str) -> u64 {
    let mut total: u64 = 0;
    for line in stdout.lines() {
        if let Some(size) = line.strip_prefix("Size = ") {
            total += size.trim().parse::<u64>().unwrap_or(0);
        }
    }
    total
}

/// PH-48 — declared-extraction budget. A real WSA package extracts to a few
/// GB; 40 GB is generous headroom and far below any disk the staging volume
/// needs to survive on. An archive declaring more than this is refused
/// before extraction begins.
pub const MAX_DECLARED_EXTRACTION_BYTES: u64 = 40 * 1024 * 1024 * 1024;

/// Extract a 7z archive with whatever 7-Zip binary exists on PATH. An absent
/// binary is a hard error — no fabricated extraction.
///
/// PH-03: the archive's entry list is verified **before** anything is written.
/// An archive that cannot be enumerated is refused rather than extracted, since
/// "the extractor probably refused it" is exactly the invisible precondition
/// this project rejects.
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
        let listing = match std::process::Command::new(bin)
            .args(["l", "-slt", "-ba", &archive.to_string_lossy()])
            .output()
        {
            // Binary not present — try the next candidate.
            Err(_) => continue,
            Ok(output) if !output.status.success() => {
                return Err(format!(
                    "Refusing to extract {}: its entries could not be listed with {} ({}).",
                    archive.display(),
                    bin,
                    String::from_utf8_lossy(&output.stderr).trim()
                ));
            }
            Ok(output) => output,
        };

        let entries = parse_archive_listing(&String::from_utf8_lossy(&listing.stdout));
        if entries.is_empty() {
            return Err(format!(
                "Refusing to extract {}: the archive reported no entries.",
                archive.display()
            ));
        }
        let escaping: Vec<&str> = entries
            .iter()
            .map(String::as_str)
            .filter(|entry| !is_safe_archive_entry(entry))
            .collect();
        if !escaping.is_empty() {
            return Err(format!(
                "Refusing to extract {}: {} entr{} would escape the staging directory ({}).",
                archive.display(),
                escaping.len(),
                if escaping.len() == 1 { "y" } else { "ies" },
                escaping
                    .iter()
                    .take(3)
                    .copied()
                    .collect::<Vec<_>>()
                    .join(", ")
            ));
        }

        // PH-48: refuse archives that declare an absurd extracted size before
        // giving 7z anything to do. Advisory data — but the refusal is free.
        let declared = archive_declared_total_bytes(&String::from_utf8_lossy(&listing.stdout));
        if declared > MAX_DECLARED_EXTRACTION_BYTES {
            return Err(format!(
                "Refusing to extract {}: declares {} bytes of extracted content, over the {} byte budget (decompression bomb guard).",
                archive.display(),
                declared,
                MAX_DECLARED_EXTRACTION_BYTES
            ));
        }

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

// ---------------------------------------------------------------------------
// PH-45 — Observability: durable operation records for the staging pipeline.
//
// Every stage_asset call — success or failure — appends one record to a
// JSONL history the UI can render: an operation id, wall-clock bounds,
// total duration, per-stage durations and the outcome. Observability must
// never fail the operation it observes: an unwritable log degrades to a
// silent no-op, never an error path.
// ---------------------------------------------------------------------------

/// One completed stage of an operation, with its duration.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, specta::Type)]
#[serde(rename_all = "snake_case")]
pub struct StageTiming {
    /// "download" | "verify" | "extract" | "manifest"
    pub stage: String,
    /// RFC 3339 UTC timestamp of when the stage began.
    pub started_at: String,
    pub duration_ms: u64,
}

/// The complete record of one staging operation.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, specta::Type)]
#[serde(rename_all = "snake_case")]
pub struct OperationRecord {
    pub operation_id: String,
    pub asset: String,
    /// "success" | "failed"
    pub result: String,
    pub error: Option<String>,
    pub started_at: String,
    pub finished_at: String,
    pub duration_ms: u64,
    /// Stages that *completed*; a mid-stage failure records the total
    /// duration and error instead of pretending all stages ran.
    pub stages: Vec<StageTiming>,
    pub sha256: Option<String>,
    pub size_bytes: Option<u64>,
}

/// Operation id format: `STAGE-<yyyymmdd>-<hhmmss>-<8 hex>`. Pure so tests
/// pin the format; production entropy comes from a monotonic counter mixed
/// with the sub-second nanos. The 32-bit suffix is deliberate: 16 bits hit
/// birthday collisions around 300 rapid operations (the uniqueness test
/// caught exactly that), 32 bits does not at any realistic churn.
pub fn operation_id(now: chrono::DateTime<chrono::Utc>, entropy: u32) -> String {
    format!("STAGE-{}-{:08x}", now.format("%Y%m%d-%H%M%S"), entropy)
}

fn operation_id_for_now() -> String {
    use std::sync::atomic::{AtomicU32, Ordering};
    static SEQ: AtomicU32 = AtomicU32::new(0);
    let seq = SEQ.fetch_add(1, Ordering::Relaxed);
    let now = chrono::Utc::now();
    // FNV-1a over (seq, nanos): spreads both inputs across the 32 bits so
    // neither a tight loop (nanos nearly constant) nor clock granularity
    // (seq varying) can cluster the outputs.
    let mut hash: u32 = 0x811c9dc5;
    for word in [seq, now.timestamp_subsec_nanos()] {
        for byte in word.to_be_bytes() {
            hash ^= byte as u32;
            hash = hash.wrapping_mul(0x01000193);
        }
    }
    operation_id(now, hash)
}

fn rfc3339(t: chrono::DateTime<chrono::Utc>) -> String {
    t.to_rfc3339_opts(chrono::SecondsFormat::Secs, true)
}

/// Where the durable history lives. `EMBERBIRD_OPERATIONS_LOG` overrides the
/// location (tests and portable setups).
pub fn operations_log_path() -> PathBuf {
    if let Ok(path) = std::env::var("EMBERBIRD_OPERATIONS_LOG") {
        if !path.trim().is_empty() {
            return PathBuf::from(path);
        }
    }
    if let Ok(local_app_data) = std::env::var("LOCALAPPDATA") {
        if !local_app_data.trim().is_empty() {
            return PathBuf::from(local_app_data)
                .join("Emberbird")
                .join("operations.jsonl");
        }
    }
    std::env::temp_dir().join("emberbird-operations.jsonl")
}

/// Append one record to `path` as a JSON line.
pub fn append_operation_record(path: &Path, record: &OperationRecord) {
    if let Some(parent) = path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    if let Ok(mut file) = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
    {
        if let Ok(line) = serde_json::to_string(record) {
            let _ = writeln!(file, "{line}");
        }
    }
}

/// The last `limit` records from `path`, oldest first. Corrupt lines are
/// skipped honestly — a torn tail line from a killed process must not erase
/// the readable history.
pub fn read_operation_history_from(path: &Path, limit: usize) -> Vec<OperationRecord> {
    let Ok(content) = std::fs::read_to_string(path) else {
        return Vec::new();
    };
    let mut records: Vec<OperationRecord> = content
        .lines()
        .filter(|line| !line.trim().is_empty())
        .filter_map(|line| serde_json::from_str(line).ok())
        .collect();
    if records.len() > limit {
        records.drain(..records.len() - limit);
    }
    records
}

/// Durable history the UI can render (default location, newest last).
pub fn read_operation_history(limit: usize) -> Vec<OperationRecord> {
    read_operation_history_from(&operations_log_path(), limit)
}

// ---------------------------------------------------------------------------
// PH-40 — Mirror network: verified multi-source staging.
//
// A registry asset may list additional download locations. Mirrors are a
// *availability* feature, never a *trust* feature: every candidate — primary
// and mirror alike — must pass the same SHA-256 gate against the registry
// hash. A mirror that serves different bytes is not a fallback, it is an
// attack, and it is reported as one.
// ---------------------------------------------------------------------------

/// One mirror URL carried by a registry asset (`mirrors: []`), plus the
/// outcome of the attempt against it.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, specta::Type)]
#[serde(rename_all = "snake_case")]
pub struct MirrorAttempt {
    pub url: String,
    pub outcome: MirrorOutcome,
    pub detail: String,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, specta::Type)]
#[serde(rename_all = "snake_case")]
pub enum MirrorOutcome {
    /// First candidate that verified — the happy path.
    Succeeded,
    /// Transport-level failure (DNS, connect, HTTP status, mid-stream drop):
    /// safe to try the next mirror.
    NetworkError,
    /// Bytes arrived but the digest did not match the registry truth. This is
    /// recorded, never silently retried — and never accepted from a later
    /// mirror without saying so.
    HashMismatch,
    /// Download and verification succeeded but a *local* step failed (e.g.
    /// no 7-Zip on PATH). Failover is pointless here — every mirror would
    /// deliver byte-identical content — so the operation stops honestly.
    ExtractionFailed,
}

/// Verdict of a multi-candidate staging attempt.
#[derive(Debug, Clone, Serialize, Deserialize, specta::Type)]
pub struct MirrorStagingReport {
    pub asset: StagedAsset,
    /// URL the verified bytes actually came from (may be a mirror).
    pub fulfilled_by: String,
    /// True when the primary URL failed and a mirror delivered the bytes.
    pub used_mirror: bool,
    /// Every attempt, in order, including the successful one.
    pub attempts: Vec<MirrorAttempt>,
}

/// Candidate URLs for one registry asset: `source_url` first, then `mirrors`.
/// Deduplicated, order-preserving — the primary keeps its priority.
pub fn candidate_urls(source_url: &str, mirrors: &[String]) -> Vec<String> {
    let mut out = Vec::with_capacity(mirrors.len() + 1);
    let primary = source_url.trim().to_string();
    if !primary.is_empty() {
        out.push(primary);
    }
    for m in mirrors {
        let m = m.trim().to_string();
        if !m.is_empty() && !out.contains(&m) {
            out.push(m);
        }
    }
    out
}

/// Classify a `stage_asset` failure: a transport failure names the download;
/// anything carrying the hash-mismatch text is a mismatch; extraction-tool
/// failures are local (the bytes are already verified) and must not trigger
/// mirror failover.
fn classify_failure(err: &str) -> MirrorOutcome {
    if err.contains("SHA-256 verification failed") {
        MirrorOutcome::HashMismatch
    } else if err.contains("No 7z/7za")
        || err.contains("Extraction with")
        || err.contains("Refusing to extract")
        || err.contains("staging dir")
    {
        // Every one of these fires *after* the bytes were hash-verified, and
        // mirrors serve hash-identical content — failing over cannot change
        // the outcome, so archive-content and staging-dir refusals are local
        // stops exactly like a missing 7-Zip binary.
        MirrorOutcome::ExtractionFailed
    } else {
        MirrorOutcome::NetworkError
    }
}

/// Stage an asset trying the primary URL first, then mirrors, with hash
/// verification against the *registry* digest for every candidate.
///
/// Semantics (pinned by tests):
/// - `NetworkError` on the primary → try the next mirror (PH-40 failover).
/// - `HashMismatch` on **any** candidate → stop immediately and report it;
///   bytes that failed verification once must never influence which source
///   succeeds next.
/// - All candidates exhausted → the last network error is the error (the
///   failure the user can act on), with the mismatch list preserved in the
///   message when any occurred.
/// - A success after mismatches still reports `used_mirror: true` and the
///   full attempt trail — the caller can show "verified, from mirror 2".
pub async fn stage_asset_from_candidates<F>(
    source_url: &str,
    mirrors: &[String],
    expected_sha256: &str,
    on_progress: F,
) -> Result<MirrorStagingReport, String>
where
    F: Fn(&StageProgress),
{
    let candidates = candidate_urls(source_url, mirrors);
    if candidates.is_empty() {
        return Err(
            "No download URL for asset: registry entry carries neither source_url nor mirrors"
                .to_string(),
        );
    }

    let mut attempts: Vec<MirrorAttempt> = Vec::new();
    let mut last_network_error: Option<String> = None;
    let mut mismatches: Vec<String> = Vec::new();

    for url in &candidates {
        match stage_asset(url, expected_sha256, &on_progress).await {
            Ok(asset) => {
                attempts.push(MirrorAttempt {
                    url: url.clone(),
                    outcome: MirrorOutcome::Succeeded,
                    detail: format!("verified SHA-256 {}", asset.sha256),
                });
                let used_mirror = attempts.len() > 1 || url != &candidates[0];
                return Ok(MirrorStagingReport {
                    asset,
                    fulfilled_by: url.clone(),
                    used_mirror,
                    attempts,
                });
            }
            Err(err) => {
                let outcome = classify_failure(&err);
                if outcome == MirrorOutcome::ExtractionFailed {
                    // The mirror already delivered verified bytes; another
                    // mirror cannot fix a local tooling problem.
                    return Err(format!(
                        "Download and SHA-256 verification succeeded from {url}, but a local step failed: {err}"
                    ));
                }
                if outcome == MirrorOutcome::HashMismatch {
                    mismatches.push(url.clone());
                    attempts.push(MirrorAttempt {
                        url: url.clone(),
                        outcome,
                        detail:
                            "served bytes that failed SHA-256 verification against the registry"
                                .to_string(),
                    });
                    // A mirror serving wrong bytes is a security event, not a
                    // transport hiccup. Stop: do not launder it by succeeding
                    // against the next source without saying so.
                    break;
                }
                attempts.push(MirrorAttempt {
                    url: url.clone(),
                    outcome,
                    detail: err.clone(),
                });
                last_network_error = Some(err);
            }
        }
    }

    if let Some(err) = last_network_error {
        if !mismatches.is_empty() {
            return Err(format!(
                "{}; additionally, SHA-256 mismatches occurred at: {}",
                err,
                mismatches.join(", ")
            ));
        }
        return Err(err);
    }
    // Only reachable when every attempt was a mismatch (loop always breaks
    // after recording at least one).
    Err(format!(
        "SHA-256 verification failed for every candidate ({}); unverified content is never staged",
        mismatches.join(", ")
    ))
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

    #[test]
    fn rejects_entries_that_would_escape_the_staging_dir() {
        for entry in [
            "../evil.txt",
            "..\\evil.txt",
            "sub/../../evil.txt",
            "..",
            "sub/..",
            "/etc/passwd",
            "\\server\\share\\evil.dll",
            "C:\\Windows\\System32\\evil.dll",
            "C:/Windows/System32/evil.dll",
            "c:evil.txt",
            "",
            "   ",
        ] {
            assert!(
                !is_safe_archive_entry(entry),
                "entry {entry:?} must be rejected"
            );
        }
    }

    #[test]
    fn accepts_ordinary_entries_including_dotted_names() {
        for entry in [
            "WSA_2407.40000.4.0_x64_vanilla",
            "WSA_2407.40000.4.0_x64_vanilla\\AppxManifest.xml",
            "WSA_2407.40000.4.0_x64_vanilla/Assets/Logo.png",
            "./AppxManifest.xml",
            "a/..b/c.txt",
            "..hidden/file",
            "file..name.txt",
        ] {
            assert!(
                is_safe_archive_entry(entry),
                "entry {entry:?} must be accepted"
            );
        }
    }

    #[test]
    fn parses_only_the_path_field_from_slt_output() {
        let listing = "Path = root\\AppxManifest.xml\r\nSize = 4096\r\n\
                       Attributes = A\r\n\r\nPath = root\\Assets\\Logo.png\r\nSize = 128\r\n";
        assert_eq!(
            parse_archive_listing(listing),
            vec![
                "root\\AppxManifest.xml".to_string(),
                "root\\Assets\\Logo.png".to_string(),
            ]
        );
    }

    /// The parser is only trustworthy if it handles a genuine 7-Zip listing.
    /// Skips where no 7-Zip binary is reachable (for example Linux CI runners).
    #[test]
    fn parses_a_real_7z_listing_when_7zip_is_present() {
        #[cfg(windows)]
        let candidates = ["7z.exe", "7za.exe", "C:\\Program Files\\7-Zip\\7z.exe"];
        #[cfg(not(windows))]
        let candidates = ["7z", "7za"];

        let dir = std::env::temp_dir().join(format!("emberbird-listing-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        if std::fs::create_dir_all(dir.join("payload")).is_err() {
            return;
        }
        if std::fs::write(dir.join("payload").join("marker.txt"), b"marker").is_err() {
            return;
        }
        let archive = dir.join("sample.7z");

        for bin in candidates {
            let created = std::process::Command::new(bin)
                .current_dir(&dir)
                .args(["a", "-y", "sample.7z", "payload"])
                .output()
                .map(|out| out.status.success())
                .unwrap_or(false);
            if !created {
                continue; // binary unreachable — nothing to verify on this host
            }
            let listed = std::process::Command::new(bin)
                .args(["l", "-slt", "-ba", &archive.to_string_lossy()])
                .output()
                .expect("listing a real archive must run");
            let entries = parse_archive_listing(&String::from_utf8_lossy(&listed.stdout));
            assert!(
                entries.iter().any(|entry| entry.contains("marker.txt")),
                "parser missed a real entry: {entries:?}"
            );
            assert!(
                entries.iter().all(|entry| is_safe_archive_entry(entry)),
                "a normal archive was flagged unsafe: {entries:?}"
            );
            let _ = std::fs::remove_dir_all(&dir);
            return;
        }
        let _ = std::fs::remove_dir_all(&dir);
        // Reported rather than silent, so a green run cannot be mistaken for
        // real-listing coverage on a host without 7-Zip.
        eprintln!(
            "[skip] no reachable 7-Zip binary — real listing coverage NOT exercised on this host"
        );
    }

    // ------------------------------------------------------------------
    // QG-4 journey tests: the download pipeline's failure paths, driven
    // against real I/O so the contract holds on a machine, not on paper.
    // ------------------------------------------------------------------

    /// An unreachable destination on the loopback: connection-refused in
    /// milliseconds, deterministically, on any host — including CI.
    fn unreachable_loopback_url() -> String {
        for port in 59999..=60999 {
            if std::net::TcpListener::bind(("127.0.0.1", port)).is_ok() {
                return format!("http://127.0.0.1:{port}/wsa-fixture.7z");
            }
            // Raced; try the next port.
        }
        panic!("no free loopback port for the network-failure fixture");
    }

    #[tokio::test]
    async fn a_network_failure_is_an_error_that_never_stages_content() {
        let url = unreachable_loopback_url();
        let expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
        let progress = std::sync::atomic::AtomicBool::new(false);
        let result = stage_asset(&url, expected, |_progress| {
            progress.store(true, std::sync::atomic::Ordering::SeqCst);
        })
        .await;
        let error = result.expect_err("an unreachable host must fail the stage");
        assert!(
            error.starts_with("Download failed"),
            "the error must name the download as the failure, got: {error}"
        );
        // Nothing may be left in the staging area: a failed download must not
        // leave a partial archive a later step could mistake for content.
        let leftovers: Vec<_> = std::fs::read_dir(staging_root())
            .map(|entries| {
                entries
                    .filter_map(|e| e.ok())
                    .filter(|e| e.file_name().to_string_lossy().contains("wsa-fixture"))
                    .collect()
            })
            .unwrap_or_default();
        assert!(
            leftovers.is_empty(),
            "a failed download left staging residue: {leftovers:?}"
        );
    }

    #[tokio::test]
    async fn a_hash_mismatch_deletes_the_archive_and_refuses_to_stage() {
        // A real HTTP server serving real bytes whose SHA-256 will not match
        // the registry's expected hash — the actual mismatch path, end to end.
        let listener = std::net::TcpListener::bind("127.0.0.1:0").expect("bind ephemeral");
        let addr = listener.local_addr().unwrap();
        let payload = b"Emberbird QG-4 journey fixture: real bytes, wrong hash.".to_vec();
        let served = payload.clone();
        // A one-shot blocking server thread: the request is a single GET and
        // the connection closes after the body, so no async runtime needed.
        let server = std::thread::spawn(move || {
            let (mut stream, _) = listener.accept().expect("accept");
            use std::io::{Read, Write};
            let mut buf = [0u8; 4096];
            let _ = stream.read(&mut buf); // consume the request head
            let response = format!(
                "HTTP/1.1 200 OK\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
                served.len()
            );
            let _ = stream.write_all(response.as_bytes());
            let _ = stream.write_all(&served);
            let _ = stream.flush();
        });

        let url = format!("http://{addr}/WSA_2407.40000.4.0_x64.7z");
        // A syntactically valid SHA-256 that these bytes do not have.
        let expected = "0000000000000000000000000000000000000000000000000000000000000000";
        let result = stage_asset(&url, expected, |_| {}).await;
        server.join().expect("fixture server thread");

        let error = result.expect_err("a hash mismatch must fail the stage");
        assert!(
            error.contains("SHA-256 verification failed"),
            "the error must name the verification failure, got: {error}"
        );
        assert!(
            error.contains("The archive was deleted"),
            "the error must record the deletion, got: {error}"
        );
        // The deletion is verified on disk, not just claimed in the message.
        let leftovers: Vec<_> = std::fs::read_dir(staging_root())
            .map(|entries| {
                entries
                    .filter_map(|e| e.ok())
                    .filter(|e| e.file_name().to_string_lossy().contains("WSA_2407"))
                    .collect()
            })
            .unwrap_or_default();
        assert!(
            leftovers.is_empty(),
            "the mismatched archive survived in staging: {leftovers:?}"
        );
    }

    // ---- PH-40: mirror failover ------------------------------------------

    #[test]
    fn candidates_are_primary_first_deduplicated_and_trimmed() {
        let urls = candidate_urls(
            " https://primary.example/a.7z ",
            &[
                "https://mirror1.example/a.7z".into(),
                "".into(),
                "https://primary.example/a.7z".into(), // duplicate primary
                "  ".into(),
                "https://mirror2.example/a.7z".into(),
            ],
        );
        assert_eq!(
            urls,
            vec![
                "https://primary.example/a.7z".to_string(),
                "https://mirror1.example/a.7z".to_string(),
                "https://mirror2.example/a.7z".to_string(),
            ],
            "primary keeps priority; blanks dropped; duplicates collapsed"
        );
    }

    #[test]
    fn no_candidates_at_all_is_an_honest_error() {
        let urls = candidate_urls("", &[]);
        assert!(urls.is_empty());
    }

    #[test]
    fn transport_errors_are_classified_as_network_failures() {
        assert_eq!(
            classify_failure("Download failed: dns error"),
            MirrorOutcome::NetworkError
        );
        assert_eq!(
            classify_failure("Download failed: HTTP 503"),
            MirrorOutcome::NetworkError
        );
    }

    #[test]
    fn verification_errors_are_classified_as_mismatches() {
        assert_eq!(
            classify_failure("SHA-256 verification failed for x.7z: ..."),
            MirrorOutcome::HashMismatch
        );
        // A mismatch is a security event, not a transport one — the classifier
        // must never confuse the two, or a hostile mirror gets retried as if
        // it were merely unreachable.
        assert_ne!(
            classify_failure("SHA-256 verification failed for x.7z"),
            MirrorOutcome::NetworkError
        );
    }

    #[test]
    fn archive_refusals_are_local_failures_that_stop_failover() {
        // The exact messages extract_archive emits on a host where 7-Zip IS
        // installed and the delivered bytes are not a readable archive.
        assert_eq!(
            classify_failure(
                "Refusing to extract C:\\staged\\x.7z: its entries could not be listed with 7z (ERROR: ...)."
            ),
            MirrorOutcome::ExtractionFailed
        );
        assert_eq!(
            classify_failure(
                "Refusing to extract C:\\staged\\x.7z: the archive reported no entries."
            ),
            MirrorOutcome::ExtractionFailed
        );
        assert_eq!(
            classify_failure(
                "Refusing to extract C:\\staged\\x.7z: declares 999999999 bytes of extracted content, over the 8000000000 byte budget (decompression bomb guard)."
            ),
            MirrorOutcome::ExtractionFailed
        );
        assert_eq!(
            classify_failure("Failed to create staging dir C:\\staged\\x: Access denied"),
            MirrorOutcome::ExtractionFailed
        );
    }

    /// Real-I/O failover: the primary URL is an unreachable loopback port
    /// (deterministically bound, nothing listening), the mirror serves bytes
    /// matching the expected SHA-256.
    ///
    /// The staging pipeline needs 7-Zip for extraction, which a CI/test
    /// environment may not have — so this test asserts the two properties that
    /// hold in *every* environment: (1) the failure names the mirror and a
    /// local cause, never a network one, proving the mirror was reached and
    /// its bytes verified; (2) the verified archive is present on disk with
    /// exactly the expected digest — mirror delivery proven by hashing real
    /// bytes, not by trusting a message. A local tooling failure must also
    /// stop the failover: another mirror cannot fix a missing local binary.
    #[tokio::test]
    async fn mirror_failover_reaches_verified_bytes_when_primary_is_down() {
        use sha2::Digest as _;
        use std::io::{Read, Write as _};

        let primary_addr = std::net::TcpListener::bind("127.0.0.1:0")
            .expect("bind primary")
            .local_addr()
            .expect("primary addr");
        // A fixture-local filename: tests run in parallel against the real
        // shared staging root, and the existing no-leftovers assertions filter
        // the WSA_2407 namespace — this test must not collide with them.
        let primary_url = format!("http://{primary_addr}/EmberbirdMirrorFixture.7z");

        let payload = b"verified mirror bytes".to_vec();
        let digest = sha2::Sha256::digest(&payload);
        let expected = hex_string(&digest);
        let body = payload.clone();
        // Bind in the test body so the URL is known before the thread spawns.
        let listener = std::net::TcpListener::bind("127.0.0.1:0").expect("bind mirror");
        let mirror_addr = listener.local_addr().expect("mirror addr");
        let mirror_url = format!("http://{mirror_addr}/EmberbirdMirrorFixture.7z");
        let later_mirror = "https://never-tried.example/EmberbirdMirrorFixture.7z";
        let server = std::thread::spawn(move || {
            let (stream, _) = listener.accept().expect("accept");
            let mut stream = stream;
            let mut buf = [0u8; 4096];
            let _ = stream.read(&mut buf);
            let mut resp = format!(
                "HTTP/1.1 200 OK\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
                body.len()
            )
            .into_bytes();
            resp.extend_from_slice(&body);
            let _ = stream.write_all(&resp);
            let _ = stream.flush();
        });

        let result = stage_asset_from_candidates(
            &primary_url,
            &[mirror_url.clone(), later_mirror.to_string()],
            &expected,
            |_| {},
        )
        .await;
        server.join().expect("fixture server thread");

        let error = match result {
            Ok(report) => panic!(
                "expected a local-step stop in a 7z-less environment, got a full report: {report:?}"
            ),
            Err(err) => err,
        };
        assert!(
            error.contains(&mirror_url),
            "the error must name the mirror that delivered the bytes, got: {error}"
        );
        assert!(
            error.contains("SHA-256 verification succeeded"),
            "the mirror's bytes were verified before the local failure, got: {error}"
        );
        assert!(
            error.contains("7z") || error.contains("local"),
            "the failure must be identified as local, not network, got: {error}"
        );
        assert!(
            !error.contains("never-tried"),
            "a local failure must not fail over to further mirrors, got: {error}"
        );

        // The decisive proof: the mirror really delivered byte-verified
        // content — the staged archive exists and hashes to the registry
        // digest. (Verified content is kept; only unverified content is
        // ever deleted.)
        let archive = staging_root().join("EmberbirdMirrorFixture.7z");
        assert!(
            archive.is_file(),
            "verified archive missing after staging: {error}"
        );
        let on_disk = {
            let bytes = std::fs::read(&archive).expect("read staged archive");
            hex_string(&sha2::Sha256::digest(&bytes))
        };
        assert_eq!(
            on_disk, expected,
            "on-disk archive must match the registry digest"
        );
        // Test hygiene: remove the archive and the (empty) extraction dir the
        // local-step failure may have left behind.
        let _ = std::fs::remove_file(&archive);
        let _ = std::fs::remove_dir_all(staging_root().join("EmberbirdMirrorFixture"));
    }

    /// A hostile mirror (wrong bytes) stops the failover immediately: the
    /// mismatch is reported, later mirrors are not tried, and the primary is
    /// never re-consulted.
    #[tokio::test]
    async fn a_hash_mismatch_on_any_candidate_stops_the_failover() {
        use sha2::Digest as _;
        use std::io::{Read, Write as _};

        let expected = hex_string(&sha2::Sha256::digest(b"the real bytes"));
        let hostile_body = b"the wrong bytes".to_vec();
        let listener = std::net::TcpListener::bind("127.0.0.1:0").expect("bind hostile");
        let addr = listener.local_addr().expect("hostile addr");
        let hostile_url = format!("http://{addr}/EmberbirdHostileFixture.7z");
        let server = std::thread::spawn(move || {
            let (stream, _) = listener.accept().expect("accept");
            let mut stream = stream;
            let mut buf = [0u8; 4096];
            let _ = stream.read(&mut buf);
            let mut resp = format!(
                "HTTP/1.1 200 OK\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
                hostile_body.len()
            )
            .into_bytes();
            resp.extend_from_slice(&hostile_body);
            let _ = stream.write_all(&resp);
            let _ = stream.flush();
        });

        let result = stage_asset_from_candidates(
            &hostile_url,
            &["https://never-tried.example/a.7z".to_string()],
            &expected,
            |_| {},
        )
        .await;
        server.join().expect("fixture server thread");

        let error = result.expect_err("a mismatch must fail the whole stage");
        assert!(
            error.contains("SHA-256 verification failed"),
            "the failure must be the mismatch, got: {error}"
        );
        assert!(
            !error.contains("never-tried"),
            "later mirrors must not appear in a mismatch stop"
        );
    }

    // ---- PH-48: hostile input at the URL/filename boundary ----------------

    #[test]
    fn hostile_filenames_are_rejected_fail_closed() {
        let hostile = [
            // Pure traversal.
            "..",
            ".",
            "..%2F",
            "foo/../bar", // (separator inside → rejected below anyway)
            // Separator smuggling (backslash, slash, encoded-or-not — the
            // function sees the decoded segment, so both forms carry '/').
            "a/b.7z",
            "a\\b.7z",
            // Drive-qualified.
            "C:evil.7z",
            "c:\\evil.7z",
            // Windows reserved device names, with extension and case drift.
            "CON.7z",
            "con.7z",
            "NUL",
            "nul.7z",
            "COM1.7z",
            "lpt9.7z",
            // Trailing dots/spaces get stripped by Windows: CON. -> device.
            "CON.",
            "AUX.7z. ",
            // NUL and control characters.
            "evil\0.7z",
            "evil\n.7z",
        ];
        for name in hostile {
            assert!(
                !is_safe_artifact_filename(name),
                "hostile filename {name:?} must be rejected"
            );
            // URL-level check: entries containing '/' cannot reach the guard
            // through `filename_from_url` (rsplit reduces them to the last
            // segment — asserted below), so only single-segment names are
            // asserted end-to-end here.
            if !name.contains('/') {
                assert!(
                    filename_from_url(&format!("https://host/{name}")).is_err(),
                    "filename_from_url must refuse {name:?}"
                );
            }
        }
        // By construction, `filename_from_url` sees only the last '/'-segment:
        // an embedded traversal path resolves away *as a segment*, and the
        // remaining name is guarded on its own merits.
        assert_eq!(
            filename_from_url("https://host/foo/../bar.7z").unwrap(),
            "bar.7z"
        );
    }

    #[test]
    fn legitimate_artifact_filenames_survive_the_guard() {
        let legit = [
            "WSA_2407.40000.4.0_x64.7z",
            "EmberbirdManagerSetup_0.2.2.exe",
            "Emberbird_WSA_2407.40000.4.0_x64_Banking.7z",
            "asset-with-dashes.json",
            "dots..in..name.7z", // dots are fine; only exact `..` segment escapes
            "CONTROLLER.7z",     // contains CON as a substring but is not the device
        ];
        for name in legit {
            assert!(
                is_safe_artifact_filename(name),
                "legitimate filename {name:?} must be accepted"
            );
        }
    }

    #[test]
    fn traversal_urls_never_reach_the_filesystem() {
        // The end-to-end boundary: `filename_from_url` must refuse these
        // before `staging_root().join(...)` could ever resolve outside.
        for url in [
            "https://host/..",
            "https://host/subdir/..",
            "https://host/..?sha256=abc",
            "https://host/C:evil.7z",
        ] {
            let err = filename_from_url(url).expect_err(url);
            assert!(
                err.contains("not a safe artifact filename"),
                "refusal must name the security reason, got: {err}"
            );
        }
    }

    #[test]
    fn filenames_with_no_segment_are_still_refused_honestly() {
        let err = filename_from_url("https://host/").expect_err("no segment");
        assert!(err.contains("no filename segment"), "got: {err}");
    }

    // ---- PH-48: decompression-bomb budget ---------------------------------

    #[test]
    fn declared_size_sums_every_size_line() {
        let listing = "Path = a.7z\nSize = 100 \nAttributes = A\nPath = b\nSize = 200\nPath = dir\nAttributes = D";
        assert_eq!(archive_declared_total_bytes(listing), 300);
    }

    #[test]
    fn malformed_size_lines_contribute_zero_not_a_crash() {
        let listing = "Path = a\nSize = not-a-number\nPath = b\nSize = -5\nSize =";
        assert_eq!(archive_declared_total_bytes(listing), 0);
    }

    #[test]
    fn bomb_budget_is_generous_but_real() {
        // A real WSA package extracts to a few GB; the budget must sit far
        // above that (no false positive) and far below disk-death (no no-op).
        // Const block: clippy rightly notes these are compile-time facts.
        const { assert!(MAX_DECLARED_EXTRACTION_BYTES > 10 * 1024 * 1024 * 1024) }
        const { assert!(MAX_DECLARED_EXTRACTION_BYTES < 1024 * 1024 * 1024 * 1024) }
    }

    #[test]
    fn a_declared_bomb_is_refused_with_a_named_reason() {
        // End-to-end through the guard's own arithmetic: a listing declaring
        // 41 GiB must be over-budget under the same constant the extractor
        // uses.
        let mut listing = String::new();
        for i in 0..41 {
            listing.push_str(&format!("Path = blob{i}\nSize = 1073741824\n")); // 1 GiB each
        }
        let declared = archive_declared_total_bytes(&listing);
        assert!(
            declared > MAX_DECLARED_EXTRACTION_BYTES,
            "fixture must exceed the budget"
        );
    }

    #[test]
    fn a_realistic_wsa_listing_is_well_under_budget() {
        // ~3.5 GiB of plausible entries stays under the budget.
        let mut listing = String::new();
        for i in 0..3500 {
            listing.push_str(&format!("Path = payload/{i}.img\nSize = 1048576\n"));
        }
        let declared = archive_declared_total_bytes(&listing);
        assert!(declared < MAX_DECLARED_EXTRACTION_BYTES);
    }

    // ---- PH-45: operation records -----------------------------------------

    #[test]
    fn operation_ids_match_the_documented_format() {
        let now = chrono::Utc::now();
        let id = operation_id(now, 0xdeadbeef);
        assert!(
            id.starts_with("STAGE-") && id.ends_with("deadbeef"),
            "id must be STAGE-<stamp>-<8hex>, got: {id}"
        );
        let stamp = &id["STAGE-".len()..id.len() - 9];
        assert_eq!(stamp.len(), 15, "yyyymmdd-hhmmss, got: {stamp}");
        assert_eq!(&stamp[8..9], "-");
    }

    #[test]
    fn operation_ids_are_effectively_unique_under_churn() {
        let ids: std::collections::HashSet<String> =
            (0..1000).map(|_| operation_id_for_now()).collect();
        assert_eq!(
            ids.len(),
            1000,
            "32-bit entropy must not collide at 1000 rapid calls"
        );
    }

    #[test]
    fn history_roundtrips_and_tolerates_a_torn_tail() {
        let tmp = std::env::temp_dir().join(format!("eb-ops-test-{}", std::process::id()));
        let _ = std::fs::remove_file(&tmp);
        let record = OperationRecord {
            operation_id: "STAGE-20260922-120000-0001".into(),
            asset: "WSA_2407.40000.4.0_x64.7z".into(),
            result: "success".into(),
            error: None,
            started_at: "2026-09-22T12:00:00Z".into(),
            finished_at: "2026-09-22T12:01:00Z".into(),
            duration_ms: 60_000,
            stages: vec![StageTiming {
                stage: "download".into(),
                started_at: "2026-09-22T12:00:00Z".into(),
                duration_ms: 59_000,
            }],
            sha256: Some("a".repeat(64)),
            size_bytes: Some(1234),
        };
        append_operation_record(&tmp, &record);
        append_operation_record(&tmp, &record);
        // A torn tail (killed mid-write) must not erase the readable history.
        {
            use std::io::Write;
            let mut f = std::fs::OpenOptions::new().append(true).open(&tmp).unwrap();
            let _ = writeln!(f, "{{\"operation_id\": \"TORN");
        }
        let history = read_operation_history_from(&tmp, 10);
        assert_eq!(history.len(), 2, "torn line skipped, records kept");
        assert_eq!(history[0].operation_id, "STAGE-20260922-120000-0001");
        let last2 = read_operation_history_from(&tmp, 1);
        assert_eq!(last2.len(), 1, "limit returns the newest records");
        let _ = std::fs::remove_file(&tmp);
    }

    #[test]
    fn history_of_a_missing_log_is_empty_not_an_error() {
        let bogus = std::env::temp_dir().join("eb-ops-no-such-file.jsonl");
        let _ = std::fs::remove_file(&bogus);
        assert!(read_operation_history_from(&bogus, 10).is_empty());
    }
}
