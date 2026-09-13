pub mod commands;
pub mod detector;
pub mod env;
pub mod releases;

use commands::{check_for_updates, detect_wsa_status, get_latest_releases, validate_manager_env};

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            detect_wsa_status,
            check_for_updates,
            get_latest_releases,
            validate_manager_env
        ])
        .run(tauri::generate_context!())
        .expect("error while running WSABuilds Manager application");
}
