pub mod backup;
pub mod commands;
pub mod coordinator;
pub mod detector;
pub mod env;
pub mod installer;
pub mod registry;
pub mod releases;
pub mod restore;
pub mod state;

use commands::{
    check_for_updates, create_vhdx_backup, detect_wsa_status, execute_upgrade, get_latest_releases,
    list_backup_candidates, preflight_upgrade, prune_backups, restore_vhdx_backup,
    validate_manager_env,
};

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            detect_wsa_status,
            check_for_updates,
            get_latest_releases,
            validate_manager_env,
            create_vhdx_backup,
            list_backup_candidates,
            restore_vhdx_backup,
            prune_backups,
            preflight_upgrade,
            execute_upgrade
        ])
        .run(tauri::generate_context!())
        .expect("error while running Emberbird Manager application");
}
