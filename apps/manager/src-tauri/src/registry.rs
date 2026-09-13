use crate::backup::{get_default_backup_dir, BackupMetadata};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RestoreCandidate {
    pub id: String,
    pub timestamp: String,
    pub wsa_version: String,
    pub backup_path: String,
    pub file_size_bytes: u64,
    pub sha256: String,
    pub description: Option<String>,
    pub is_valid: bool,
    pub validation_error: Option<String>,
}

pub fn list_backups(base_dir: Option<&Path>) -> Result<Vec<RestoreCandidate>, String> {
    let root = match base_dir {
        Some(p) => p.to_path_buf(),
        None => get_default_backup_dir(),
    };

    if !root.exists() {
        return Ok(Vec::new());
    }

    let mut candidates = Vec::new();

    let entries = fs::read_dir(&root)
        .map_err(|e| format!("Failed to read backup directory {}: {}", root.display(), e))?;

    for entry in entries.flatten() {
        let entry_path = entry.path();
        if !entry_path.is_dir() {
            continue;
        }

        let meta_file = entry_path.join("backup-meta.json");
        if !meta_file.exists() {
            continue;
        }

        if let Ok(content) = fs::read_to_string(&meta_file) {
            if let Ok(meta) = serde_json::from_str::<BackupMetadata>(&content) {
                let backup_file = PathBuf::from(&meta.backup_path);
                let (is_valid, validation_error) = if !backup_file.exists() {
                    (
                        false,
                        Some("Backup VHDX file is missing from disk".to_string()),
                    )
                } else if let Ok(m) = backup_file.metadata() {
                    if m.len() != meta.file_size_bytes {
                        (
                            false,
                            Some(format!(
                                "File size mismatch: recorded {} bytes, actual {} bytes",
                                meta.file_size_bytes,
                                m.len()
                            )),
                        )
                    } else {
                        (true, None)
                    }
                } else {
                    (
                        false,
                        Some("Cannot inspect backup file metadata".to_string()),
                    )
                };

                candidates.push(RestoreCandidate {
                    id: meta.id,
                    timestamp: meta.timestamp,
                    wsa_version: meta.wsa_version,
                    backup_path: meta.backup_path,
                    file_size_bytes: meta.file_size_bytes,
                    sha256: meta.sha256,
                    description: meta.description,
                    is_valid,
                    validation_error,
                });
            }
        }
    }

    // Sort descending by timestamp (newest first)
    candidates.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));

    Ok(candidates)
}

pub fn prune_backups(base_dir: Option<&Path>, retain_count: usize) -> Result<Vec<String>, String> {
    let candidates = list_backups(base_dir)?;
    let mut pruned_ids = Vec::new();

    if candidates.len() <= retain_count {
        return Ok(pruned_ids);
    }

    let root = match base_dir {
        Some(p) => p.to_path_buf(),
        None => get_default_backup_dir(),
    };

    // Retain top retain_count candidates, prune remaining older candidates
    for to_prune in &candidates[retain_count..] {
        let dir_to_remove = root.join(&to_prune.id);
        if dir_to_remove.exists() {
            fs::remove_dir_all(&dir_to_remove)
                .map_err(|e| format!("Failed to prune backup {}: {}", to_prune.id, e))?;
            pruned_ids.push(to_prune.id.clone());
        }
    }

    Ok(pruned_ids)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_list_backups_empty_when_dir_missing() {
        let nonexistent = Path::new("C:\\wsabuilds_nonexistent_dir_12345");
        let list = list_backups(Some(nonexistent)).unwrap();
        assert!(list.is_empty());
    }

    #[test]
    fn test_list_backups_with_valid_and_invalid_candidates() {
        let temp_dir = std::env::temp_dir().join("wsabuilds_test_registry_listing");
        fs::create_dir_all(&temp_dir).unwrap();

        // 1. Valid candidate
        let c1_dir = temp_dir.join("backup_20260101_100000");
        fs::create_dir_all(&c1_dir).unwrap();
        let c1_vhdx = c1_dir.join("userdata.vhdx");
        fs::write(&c1_vhdx, b"VALID CONTENT").unwrap();

        let c1_meta = BackupMetadata {
            id: "backup_20260101_100000".to_string(),
            timestamp: "2026-01-01T10:00:00Z".to_string(),
            wsa_version: "2311.40000.5.0".to_string(),
            source_path: "C:\\source.vhdx".to_string(),
            backup_path: c1_vhdx.to_string_lossy().to_string(),
            file_size_bytes: 13,
            sha256: "fake_hash_1".to_string(),
            description: Some("First Backup".to_string()),
            status: "completed".to_string(),
        };
        fs::write(
            c1_dir.join("backup-meta.json"),
            serde_json::to_vec(&c1_meta).unwrap(),
        )
        .unwrap();

        // 2. Corrupted candidate (file size mismatch)
        let c2_dir = temp_dir.join("backup_20260201_100000");
        fs::create_dir_all(&c2_dir).unwrap();
        let c2_vhdx = c2_dir.join("userdata.vhdx");
        fs::write(&c2_vhdx, b"MISMATCH").unwrap(); // 8 bytes

        let c2_meta = BackupMetadata {
            id: "backup_20260201_100000".to_string(),
            timestamp: "2026-02-01T10:00:00Z".to_string(),
            wsa_version: "2311.40000.5.0".to_string(),
            source_path: "C:\\source.vhdx".to_string(),
            backup_path: c2_vhdx.to_string_lossy().to_string(),
            file_size_bytes: 9999, // mismatch
            sha256: "fake_hash_2".to_string(),
            description: Some("Corrupted Backup".to_string()),
            status: "completed".to_string(),
        };
        fs::write(
            c2_dir.join("backup-meta.json"),
            serde_json::to_vec(&c2_meta).unwrap(),
        )
        .unwrap();

        let candidates = list_backups(Some(&temp_dir)).unwrap();
        assert_eq!(candidates.len(), 2);

        // Check sorting: c2 has newer timestamp 2026-02-01 vs 2026-01-01
        assert_eq!(candidates[0].id, "backup_20260201_100000");
        assert!(!candidates[0].is_valid);
        assert!(candidates[0]
            .validation_error
            .as_ref()
            .unwrap()
            .contains("mismatch"));

        assert_eq!(candidates[1].id, "backup_20260101_100000");
        assert!(candidates[1].is_valid);
        assert!(candidates[1].validation_error.is_none());

        // Pruning test: retain 1 candidate
        let pruned = prune_backups(Some(&temp_dir), 1).unwrap();
        assert_eq!(pruned.len(), 1);
        assert_eq!(pruned[0], "backup_20260101_100000");

        let remaining = list_backups(Some(&temp_dir)).unwrap();
        assert_eq!(remaining.len(), 1);

        let _ = fs::remove_dir_all(&temp_dir);
    }
}
