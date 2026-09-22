pub mod backup;
pub mod commands;
pub mod coordinator;
pub mod detector;
pub mod doctor;
pub mod downloader;
pub mod env;
pub mod installer;
pub mod registry;
pub mod registry_truth;
pub mod releases;
pub mod restore;
pub mod runtime_state;
pub mod state;

use commands::{
    check_for_updates, create_vhdx_backup, detect_wsa_status, download_and_stage_release,
    execute_upgrade, get_host_arch, get_lifecycle_report, get_operation_history,
    install_wsa_package, launch_wsa, list_backup_candidates, preflight_upgrade, prune_backups,
    restore_vhdx_backup, run_doctor_scan, shutdown_wsa, validate_manager_env,
};

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            detect_wsa_status,
            check_for_updates,
            download_and_stage_release,
            validate_manager_env,
            create_vhdx_backup,
            list_backup_candidates,
            restore_vhdx_backup,
            prune_backups,
            preflight_upgrade,
            execute_upgrade,
            install_wsa_package,
            launch_wsa,
            shutdown_wsa,
            run_doctor_scan,
            get_host_arch,
            get_lifecycle_report,
            get_operation_history
        ])
        .run(tauri::generate_context!())
        .expect("error while running Emberbird Manager application");
}
