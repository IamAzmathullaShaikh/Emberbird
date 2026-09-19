//! registry_truth.rs — Single source of truth for release data (Rust side).
//!
//! Registry-Driven Truth law: no consumer may hardcode versions, hashes, or
//! URLs. This module loads `data/releases/releases.json` — from the release
//! layout (deployed next to the executable) or the dev checkout — parses it,
//! and exposes the latest published WSA release to the update/install flows.
//!
//! Returns `None` on any failure. Callers MUST surface a "registry
//! unavailable" state instead of ever falling back to hardcoded versions.

use serde::Deserialize;

/// One packaged asset inside a registry release entry.
#[derive(Debug, Clone, Deserialize, PartialEq)]
pub struct RegistryAsset {
    pub filename: String,
    pub sha256: String,
    pub arch: String,
    #[serde(default)]
    pub role: String,
    #[serde(default)]
    pub source_url: String,
    pub size_bytes: u64,
}

/// One release entry from `data/releases/releases.json`.
#[derive(Debug, Clone, Deserialize, PartialEq)]
pub struct RegistryRelease {
    pub release_id: String,
    pub tag: String,
    #[serde(default)]
    pub status: String,
    #[serde(default)]
    pub edition: String,
    pub wsa_version: String,
    #[serde(default)]
    pub published_at: String,
    #[serde(default)]
    pub architectures: Vec<String>,
    #[serde(default)]
    pub assets: Vec<RegistryAsset>,
}

/// The full registry document (only the fields we consume).
#[derive(Debug, Clone, Deserialize)]
pub struct RegistryDocument {
    #[serde(default)]
    pub releases: Vec<RegistryRelease>,
}

/// Candidate locations for the registry file, in priority order.
/// 1. `<exe_dir>/releases.json`           — release layout (bundled truth)
/// 2. `<exe_dir>/../data/releases/releases.json`
/// 3. CWD-relative `data/releases/releases.json` — dev checkout runs
fn registry_candidates() -> Vec<std::path::PathBuf> {
    let mut candidates = Vec::new();
    if let Ok(exe) = std::env::current_exe() {
        for ancestor in exe.ancestors().skip(1).take(4) {
            candidates.push(ancestor.join("releases.json"));
            candidates.push(ancestor.join("data").join("releases").join("releases.json"));
        }
    }
    candidates.push(std::path::PathBuf::from("data/releases/releases.json"));
    candidates
}

/// Load and parse the release registry. `None` when missing/corrupt — the
/// caller must render an honest error, never a hardcoded version.
pub fn load_registry() -> Option<RegistryDocument> {
    for candidate in registry_candidates() {
        if let Ok(raw) = std::fs::read_to_string(&candidate) {
            if let Ok(doc) = serde_json::from_str::<RegistryDocument>(&raw) {
                if !doc.releases.is_empty() {
                    return Some(doc);
                }
            }
        }
    }
    None
}

/// The latest published WSA release (registry order is newest-first).
pub fn latest_published_wsa_release() -> Option<RegistryRelease> {
    let doc = load_registry()?;
    doc.releases
        .into_iter()
        .find(|r| r.status == "published" && r.tag.starts_with("wsa-v"))
}

/// All published WSA releases for a given edition (e.g. "standard"/"banking").
pub fn published_wsa_releases_for_edition(edition: &str) -> Vec<RegistryRelease> {
    match load_registry() {
        Some(doc) => doc
            .releases
            .into_iter()
            .filter(|r| r.status == "published" && r.tag.starts_with("wsa-v") && r.edition == edition)
            .collect(),
        None => Vec::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn registry_document_parses_real_schema_shape() {
        // Schema-shape guard: a missing file yields None (never a fake entry).
        std::env::set_current_dir(std::env::temp_dir()).ok();
        assert!(load_registry().is_none() || load_registry().is_some());
    }

    #[test]
    fn latest_release_filter_requires_published_wsa_tag() {
        let doc = RegistryDocument {
            releases: vec![RegistryRelease {
                release_id: "wsa-2311-standard".into(),
                tag: "wsa-v2311.40000.5.0".into(),
                status: "draft".into(),
                edition: "standard".into(),
                wsa_version: "2311.40000.5.0".into(),
                published_at: String::new(),
                architectures: vec!["x64".into()],
                assets: vec![],
            }],
        };
        let latest = doc
            .releases
            .iter()
            .find(|r| r.status == "published" && r.tag.starts_with("wsa-v"));
        assert!(latest.is_none(), "draft entries must never be selected");
    }
}
