use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum InstallStage {
    Idle,
    ValidatingPackage,
    Extracting,
    Registering,
    Verifying,
    Completed,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstallProgress {
    pub stage: InstallStage,
    pub percentage: u8,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct InstallResult {
    pub success: bool,
    pub package_path: String,
    pub message: String,
}

pub fn verify_developer_mode() -> Result<(), String> {
    let status = crate::detector::detect_subsystem();
    if !status.developer_mode_enabled {
        return Err(
            "Windows Developer Mode is required for sideloading WSA packages. Enable it in Windows Settings > System > For developers.".to_string()
        );
    }
    Ok(())
}

pub fn find_appx_manifest(package_dir: &Path) -> Result<PathBuf, String> {
    if !package_dir.exists() {
        return Err(format!(
            "Package directory does not exist: {}",
            package_dir.display()
        ));
    }

    let direct_manifest = package_dir.join("AppxManifest.xml");
    if direct_manifest.exists() {
        return Ok(direct_manifest);
    }

    // Search 1 level down
    if let Ok(entries) = std::fs::read_dir(package_dir) {
        for entry in entries.flatten() {
            let p = entry.path();
            if p.is_dir() {
                let sub_manifest = p.join("AppxManifest.xml");
                if sub_manifest.exists() {
                    return Ok(sub_manifest);
                }
            }
        }
    }

    Err(format!(
        "AppxManifest.xml not found in package directory: {}",
        package_dir.display()
    ))
}

pub fn register_wsa_package(manifest_path: &Path) -> Result<InstallResult, String> {
    verify_developer_mode()?;

    if !manifest_path.exists() {
        return Err(format!(
            "Manifest path not found: {}",
            manifest_path.display()
        ));
    }

    #[cfg(windows)]
    {
        let manifest_str = manifest_path.to_string_lossy().to_string();
        let cmd = format!(
            "Add-AppxPackage -Register \"{}\" -ForceApplicationShutdown -ForceUpdateFromAnyVersion",
            manifest_str
        );

        let output = std::process::Command::new("powershell.exe")
            .args(["-NoProfile", "-NonInteractive", "-Command", &cmd])
            .output()
            .map_err(|e| format!("Failed to spawn PowerShell Add-AppxPackage: {}", e))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            if stderr.contains("0x80073D28") || stderr.to_lowercase().contains("administrator privileges required") {
                // Attempt to request UAC elevation via Start-Process -Verb RunAs
                let escaped = manifest_str.replace('\'', "''");
                let elev_cmd = format!(
                    "$proc = Start-Process powershell.exe -PassThru -Verb RunAs -Wait -ArgumentList '-NoProfile', '-NonInteractive', '-Command', \"Add-AppxPackage -Register '\"\"{}\"\"' -ForceApplicationShutdown -ForceUpdateFromAnyVersion\"; exit $proc.ExitCode",
                    escaped
                );
                if let Ok(elev_out) = std::process::Command::new("powershell.exe")
                    .args(["-NoProfile", "-NonInteractive", "-Command", &elev_cmd])
                    .output()
                {
                    if elev_out.status.success() {
                        return Ok(InstallResult {
                            success: true,
                            package_path: manifest_str,
                            message: "WSA package registered successfully with administrator elevation".to_string(),
                        });
                    }
                }

                return Err(format!(
                    "Administrator privileges are required to install WSA services (error 0x80073D28). Please approve the Windows UAC elevation prompt, run Emberbird Manager as Administrator, or execute this command in an elevated PowerShell terminal:\nAdd-AppxPackage -Register \"{}\" -ForceApplicationShutdown -ForceUpdateFromAnyVersion",
                    manifest_str
                ));
            }
            return Err(format!("Add-AppxPackage failed: {}", stderr.trim()));
        }

        Ok(InstallResult {
            success: true,
            package_path: manifest_str,
            message: "WSA package registered successfully via AppX deployment API".to_string(),
        })
    }

    #[cfg(not(windows))]
    {
        Ok(InstallResult {
            success: true,
            package_path: manifest_path.to_string_lossy().to_string(),
            message: "Simulated registration on non-Windows environment".to_string(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn test_find_appx_manifest_direct() {
        let temp_dir = std::env::temp_dir().join("wsabuilds_test_manifest_direct");
        fs::create_dir_all(&temp_dir).unwrap();
        let manifest = temp_dir.join("AppxManifest.xml");
        fs::write(&manifest, b"<Package></Package>").unwrap();

        let found = find_appx_manifest(&temp_dir).unwrap();
        assert_eq!(found, manifest);

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_find_appx_manifest_nested() {
        let temp_dir = std::env::temp_dir().join("wsabuilds_test_manifest_nested");
        let sub = temp_dir.join("WSA_Extracted");
        fs::create_dir_all(&sub).unwrap();
        let manifest = sub.join("AppxManifest.xml");
        fs::write(&manifest, b"<Package></Package>").unwrap();

        let found = find_appx_manifest(&temp_dir).unwrap();
        assert_eq!(found, manifest);

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_find_appx_manifest_missing() {
        let temp_dir = std::env::temp_dir().join("wsabuilds_test_manifest_missing");
        fs::create_dir_all(&temp_dir).unwrap();

        let res = find_appx_manifest(&temp_dir);
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("AppxManifest.xml not found"));

        let _ = fs::remove_dir_all(&temp_dir);
    }
}
