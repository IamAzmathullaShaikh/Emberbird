use crate::backup::{
    check_wsa_running, copy_and_hash_vhdx, verify_vhdx_unlocked,
};
use crate::registry::list_backups;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::{self, File};
use std::io::Read;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, specta::Type)]
pub struct RestorePreflight {
    pub can_restore: bool,
    pub candidate_id: String,
    pub backup_path: String,
    pub target_path: String,
    pub backup_size_bytes: u64,
    pub sha256: String,
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, specta::Type)]
pub struct RestoreResult {
    pub success: bool,
    pub candidate_id: String,
    pub restored_path: String,
    pub restored_sha256: String,
    pub message: String,
}

pub fn compute_sha256(path: &Path) -> Result<String, String> {
    let mut file = File::open(path)
        .map_err(|e| format!("Failed to open file for SHA-256 calculation: {}", e))?;
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 65536];

    loop {
        let n = file
            .read(&mut buffer)
            .map_err(|e| format!("Read error during hashing: {}", e))?;
        if n == 0 {
            break;
        }
        hasher.update(&buffer[..n]);
    }

    Ok(format!("{:x}", hasher.finalize()))
}

pub fn preflight_restore(
    candidate_id: &str,
    custom_target: Option<&Path>,
    base_dir: Option<&Path>,
) -> Result<RestorePreflight, String> {
    let candidates = list_backups(base_dir)?;
    let candidate = candidates
        .into_iter()
        .find(|c| c.id == candidate_id)
        .ok_or_else(|| format!("Backup candidate '{}' not found in registry", candidate_id))?;

    let mut errors = Vec::new();
    let mut warnings = Vec::new();

    if !candidate.is_valid {
        errors.push(
            candidate
                .validation_error
                .unwrap_or_else(|| "Backup candidate is corrupted or invalid".to_string()),
        );
    }

    let target_path = match custom_target {
        Some(p) => p.to_path_buf(),
        None => {
            let backup_path = Path::new(&candidate.backup_path);
            let filename = backup_path
                .file_name()
                .unwrap_or_else(|| std::ffi::OsStr::new("userdata.2.vhdx"));

            let local_app_data = std::env::var("LOCALAPPDATA")
                .map_err(|_| "Could not resolve LOCALAPPDATA".to_string())?;
            PathBuf::from(local_app_data)
                .join("Packages")
                .join("MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe")
                .join("LocalCache")
                .join(filename)
        }
    };

    if check_wsa_running() {
        errors.push("WSA is currently running. Please stop WSA before restoring.".to_string());
    }

    if target_path.exists() {
        if let Err(e) = verify_vhdx_unlocked(&target_path) {
            errors.push(format!("Target VHDX is locked: {}", e));
        }
        let target_name = target_path
            .file_name()
            .map(|s| s.to_string_lossy().to_string())
            .unwrap_or_else(|| "userdata VHDX".to_string());
        warnings.push(format!(
            "Existing target {} will be backed up to .pre_restore.bak before replacement.",
            target_name
        ));
    }

    let can_restore = errors.is_empty();

    Ok(RestorePreflight {
        can_restore,
        candidate_id: candidate.id,
        backup_path: candidate.backup_path,
        target_path: target_path.to_string_lossy().to_string(),
        backup_size_bytes: candidate.file_size_bytes,
        sha256: candidate.sha256,
        warnings,
        errors,
    })
}

pub fn execute_restore_impl(
    candidate_id: &str,
    custom_target: Option<&Path>,
    base_dir: Option<&Path>,
) -> Result<RestoreResult, String> {
    let preflight = preflight_restore(candidate_id, custom_target, base_dir)?;
    if !preflight.can_restore {
        return Err(format!(
            "Restore preflight failed: {}",
            preflight.errors.join("; ")
        ));
    }

    let backup_file = PathBuf::from(&preflight.backup_path);
    let target_file = PathBuf::from(&preflight.target_path);

    let disk_hash = compute_sha256(&backup_file)?;
    if disk_hash != preflight.sha256 {
        return Err(format!(
            "Candidate checksum mismatch on disk: expected {}, found {}",
            preflight.sha256, disk_hash
        ));
    }

    let mut bak_name = target_file
        .file_name()
        .map(|s| s.to_os_string())
        .unwrap_or_else(|| std::ffi::OsString::from("userdata.2.vhdx"));
    bak_name.push(".pre_restore.bak");
    let safety_backup = target_file.with_file_name(bak_name);
    let mut safety_created = false;
    if target_file.exists() {
        fs::copy(&target_file, &safety_backup)
            .map_err(|e| format!("Failed to create pre-restore safety copy: {}", e))?;
        safety_created = true;
    } else if let Some(parent) = target_file.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("Failed to create target directory: {}", e))?;
    }

    match copy_and_hash_vhdx(&backup_file, &target_file) {
        Ok((_, restored_sha256)) => {
            if restored_sha256 != preflight.sha256 {
                if safety_created {
                    let _ = fs::copy(&safety_backup, &target_file);
                    let _ = fs::remove_file(&safety_backup);
                }
                return Err(format!(
                    "Integrity verification failed on restored file: expected {}, found {}. Rollback performed.",
                    preflight.sha256, restored_sha256
                ));
            }

            if safety_created {
                let _ = fs::remove_file(&safety_backup);
            }

            Ok(RestoreResult {
                success: true,
                candidate_id: preflight.candidate_id,
                restored_path: target_file.to_string_lossy().to_string(),
                restored_sha256,
                message: "Restore completed and integrity verified successfully".to_string(),
            })
        }
        Err(copy_err) => {
            if safety_created {
                let _ = fs::copy(&safety_backup, &target_file);
                let _ = fs::remove_file(&safety_backup);
            }
            Err(format!(
                "Restore copy failed: {}. Rollback performed.",
                copy_err
            ))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::backup::BackupMetadata;

    #[test]
    fn test_compute_sha256() {
        let temp_dir = std::env::temp_dir().join("wsabuilds_test_compute_hash");
        fs::create_dir_all(&temp_dir).unwrap();
        let test_file = temp_dir.join("test.bin");
        let test_bytes = b"Hello WSABuilds Sha256";
        fs::write(&test_file, test_bytes).unwrap();

        let hash = compute_sha256(&test_file).unwrap();
        let mut hasher = Sha256::new();
        hasher.update(test_bytes);
        let expected = format!("{:x}", hasher.finalize());

        assert_eq!(hash, expected);
        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_restore_success_flow() {
        let temp_dir = std::env::temp_dir().join("wsabuilds_test_restore_success");
        let backups_dir = temp_dir.join("backups");
        let candidate_dir = backups_dir.join("backup_test_01");
        fs::create_dir_all(&candidate_dir).unwrap();

        let backup_vhdx = candidate_dir.join("userdata.vhdx");
        let content = b"Restored Android Container Data";
        fs::write(&backup_vhdx, content).unwrap();

        let mut hasher = Sha256::new();
        hasher.update(content);
        let sha256 = format!("{:x}", hasher.finalize());

        let meta = BackupMetadata {
            id: "backup_test_01".to_string(),
            timestamp: "2026-03-01T12:00:00Z".to_string(),
            wsa_version: "2311.40000.5.0".to_string(),
            source_path: "C:\\mock_src.vhdx".to_string(),
            backup_path: backup_vhdx.to_string_lossy().to_string(),
            file_size_bytes: content.len() as u64,
            sha256: sha256.clone(),
            description: Some("Restore test".to_string()),
            status: "completed".to_string(),
        };
        fs::write(
            candidate_dir.join("backup-meta.json"),
            serde_json::to_vec(&meta).unwrap(),
        )
        .unwrap();

        let target_vhdx = temp_dir.join("target_wsa").join("userdata.vhdx");
        fs::create_dir_all(target_vhdx.parent().unwrap()).unwrap();
        fs::write(&target_vhdx, b"Old data before restore").unwrap();

        let preflight =
            preflight_restore("backup_test_01", Some(&target_vhdx), Some(&backups_dir)).unwrap();
        assert!(preflight.can_restore);

        let res =
            execute_restore_impl("backup_test_01", Some(&target_vhdx), Some(&backups_dir)).unwrap();
        assert!(res.success);
        assert_eq!(res.restored_sha256, sha256);

        let read_back = fs::read(&target_vhdx).unwrap();
        assert_eq!(read_back, content);

        let _ = fs::remove_dir_all(&temp_dir);
    }
}
