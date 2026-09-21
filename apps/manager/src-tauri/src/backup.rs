use chrono::Utc;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, specta::Type)]
pub struct BackupMetadata {
    pub id: String,
    pub timestamp: String,
    pub wsa_version: String,
    pub source_path: String,
    pub backup_path: String,
    pub file_size_bytes: u64,
    pub sha256: String,
    pub description: Option<String>,
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, specta::Type)]
pub struct BackupResult {
    pub success: bool,
    pub metadata: Option<BackupMetadata>,
    pub error: Option<String>,
}

pub fn check_wsa_running() -> bool {
    crate::detector::detect_subsystem().is_running
}

pub fn request_wsa_shutdown() -> Result<(), String> {
    #[cfg(windows)]
    {
        let output = std::process::Command::new("powershell.exe")
            .args([
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "Start-Process WsaClient.exe -ArgumentList '/shutdown' -ErrorAction SilentlyContinue",
            ])
            .output();

        match output {
            Ok(_) => Ok(()),
            Err(e) => Err(format!("Failed to invoke WsaClient /shutdown: {}", e)),
        }
    }
    #[cfg(not(windows))]
    {
        Ok(())
    }
}

pub fn verify_vhdx_unlocked(path: &Path) -> Result<(), String> {
    if !path.exists() {
        return Err(format!("Target VHDX file does not exist: {}", path.display()));
    }

    match OpenOptions::new().read(true).open(path) {
        Ok(_) => Ok(()),
        Err(e) => Err(format!(
            "VHDX is currently locked by another process (WSA may still be running): {}",
            e
        )),
    }
}

pub fn copy_and_hash_vhdx(src: &Path, dst: &Path) -> Result<(u64, String), String> {
    let mut source_file =
        File::open(src).map_err(|e| format!("Failed to open source VHDX: {}", e))?;
    let mut dest_file =
        File::create(dst).map_err(|e| format!("Failed to create backup VHDX: {}", e))?;

    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 65536];
    let mut total_bytes: u64 = 0;

    loop {
        let bytes_read = source_file
            .read(&mut buffer)
            .map_err(|e| format!("Read error during VHDX copy: {}", e))?;
        if bytes_read == 0 {
            break;
        }

        hasher.update(&buffer[..bytes_read]);
        dest_file
            .write_all(&buffer[..bytes_read])
            .map_err(|e| format!("Write error during VHDX copy: {}", e))?;
        total_bytes += bytes_read as u64;
    }

    dest_file
        .flush()
        .map_err(|e| format!("Flush error on backup VHDX: {}", e))?;
    let hash_result = format!("{:x}", hasher.finalize());

    Ok((total_bytes, hash_result))
}

pub fn get_default_vhdx_path() -> Option<PathBuf> {
    let local_app_data = std::env::var("LOCALAPPDATA").ok()?;
    let cache_dir = PathBuf::from(local_app_data)
        .join("Packages")
        .join("MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe")
        .join("LocalCache");

    let vhdx2 = cache_dir.join("userdata.2.vhdx");
    if vhdx2.exists() {
        return Some(vhdx2);
    }

    let vhdx1 = cache_dir.join("userdata.vhdx");
    if vhdx1.exists() {
        return Some(vhdx1);
    }

    Some(vhdx2)
}

pub fn get_default_backup_dir() -> PathBuf {
    if let Ok(local_app_data) = std::env::var("LOCALAPPDATA") {
        let emberbird_dir = PathBuf::from(&local_app_data).join("Emberbird").join("backups");
        if emberbird_dir.exists() {
            return emberbird_dir;
        }
        let legacy_dir = PathBuf::from(&local_app_data).join("WSABuilds").join("backups");
        if legacy_dir.exists() {
            return legacy_dir;
        }
        emberbird_dir
    } else {
        std::env::temp_dir().join("Emberbird").join("backups")
    }
}

pub fn create_vhdx_backup_impl(
    custom_source: Option<&Path>,
    custom_dest_dir: Option<&Path>,
    wsa_version_override: Option<&str>,
    note: Option<String>,
    auto_shutdown: bool,
) -> Result<BackupMetadata, String> {
    let source_path = match custom_source {
        Some(p) => p.to_path_buf(),
        None => get_default_vhdx_path()
            .ok_or_else(|| "Could not resolve default VHDX path".to_string())?,
    };

    if !source_path.exists() {
        return Err(format!(
            "Source userdata VHDX not found at: {}",
            source_path.display()
        ));
    }

    if check_wsa_running() {
        if auto_shutdown {
            let _ = request_wsa_shutdown();
            let start = std::time::Instant::now();
            let mut stopped = false;
            while start.elapsed().as_secs() < 5 {
                if !check_wsa_running() {
                    stopped = true;
                    break;
                }
                std::thread::sleep(std::time::Duration::from_millis(200));
            }
            if !stopped {
                return Err("WSA is running and failed to shut down within timeout. Please close all Android apps first.".to_string());
            }
        } else {
            return Err("WSA is currently running. Cold backup requires shutting down WSA first.".to_string());
        }
    }

    verify_vhdx_unlocked(&source_path)?;

    let base_dir = match custom_dest_dir {
        Some(d) => d.to_path_buf(),
        None => get_default_backup_dir(),
    };

    let timestamp_str = Utc::now().to_rfc3339();
    let safe_timestamp = Utc::now().format("%Y%m%d_%H%M%S").to_string();
    let backup_id = format!("backup_{}", safe_timestamp);
    let target_dir = base_dir.join(&backup_id);

    fs::create_dir_all(&target_dir)
        .map_err(|e| format!("Failed to create backup target directory: {}", e))?;

    let file_name = source_path
        .file_name()
        .map(|s| s.to_os_string())
        .unwrap_or_else(|| std::ffi::OsString::from("userdata.2.vhdx"));
    let target_vhdx = target_dir.join(file_name);
    let (file_size, sha256) = copy_and_hash_vhdx(&source_path, &target_vhdx)?;

    let status = crate::detector::detect_subsystem();
    let wsa_version = wsa_version_override
        .map(|s| s.to_string())
        .or(status.package_version)
        .unwrap_or_else(|| "2311.40000.5.0".to_string());

    let metadata = BackupMetadata {
        id: backup_id,
        timestamp: timestamp_str,
        wsa_version,
        source_path: source_path.to_string_lossy().to_string(),
        backup_path: target_vhdx.to_string_lossy().to_string(),
        file_size_bytes: file_size,
        sha256,
        description: note,
        status: "completed".to_string(),
    };

    let meta_path = target_dir.join("backup-meta.json");
    let json_bytes = serde_json::to_vec_pretty(&metadata)
        .map_err(|e| format!("Failed to serialize backup metadata: {}", e))?;
    fs::write(&meta_path, json_bytes)
        .map_err(|e| format!("Failed to write backup-meta.json: {}", e))?;

    Ok(metadata)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn test_verify_vhdx_unlocked_on_valid_file() {
        let temp_dir = std::env::temp_dir().join("wsabuilds_test_backup_unlock");
        fs::create_dir_all(&temp_dir).unwrap();
        let test_file = temp_dir.join("test_unlock.vhdx");
        fs::write(&test_file, b"test unlock content").unwrap();

        let res = verify_vhdx_unlocked(&test_file);
        assert!(res.is_ok());

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_verify_vhdx_unlocked_nonexistent() {
        let nonexistent = Path::new("C:\\nonexistent_test_file_never_exists.vhdx");
        let res = verify_vhdx_unlocked(nonexistent);
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("does not exist"));
    }

    #[test]
    fn test_copy_and_hash_vhdx_correctness() {
        let temp_dir = std::env::temp_dir().join("wsabuilds_test_copy_hash");
        fs::create_dir_all(&temp_dir).unwrap();
        let src = temp_dir.join("source.vhdx");
        let dst = temp_dir.join("dest.vhdx");

        let content = b"WSABuilds VHDX Data Stream Integrity Test";
        let mut f = File::create(&src).unwrap();
        f.write_all(content).unwrap();
        drop(f);

        let (bytes_copied, hash) = copy_and_hash_vhdx(&src, &dst).unwrap();
        assert_eq!(bytes_copied, content.len() as u64);

        let mut hasher = Sha256::new();
        hasher.update(content);
        let expected_hash = format!("{:x}", hasher.finalize());

        assert_eq!(hash, expected_hash);
        assert!(dst.exists());

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_create_vhdx_backup_flow() {
        let base_temp = std::env::temp_dir().join("wsabuilds_test_backup_flow");
        let src_dir = base_temp.join("src");
        let backup_root = base_temp.join("backups");
        fs::create_dir_all(&src_dir).unwrap();
        fs::create_dir_all(&backup_root).unwrap();

        let src_vhdx = src_dir.join("userdata.vhdx");
        fs::write(&src_vhdx, b"Android User Data Simulation").unwrap();

        let meta = create_vhdx_backup_impl(
            Some(&src_vhdx),
            Some(&backup_root),
            Some("2311.40000.5.0"),
            Some("Manual test snapshot".to_string()),
            false,
        )
        .expect("Backup creation should succeed");

        assert_eq!(meta.wsa_version, "2311.40000.5.0");
        assert_eq!(meta.file_size_bytes, 28);
        assert_eq!(meta.description, Some("Manual test snapshot".to_string()));
        assert_eq!(meta.status, "completed");

        let backup_file = PathBuf::from(&meta.backup_path);
        assert!(backup_file.exists());

        let meta_file = backup_file.parent().unwrap().join("backup-meta.json");
        assert!(meta_file.exists());

        let _ = fs::remove_dir_all(&base_temp);
    }
}
