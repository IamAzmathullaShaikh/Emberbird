use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ManagerEnvConfig {
    pub github_repo: String,
    pub repo_url: String,
    pub releases_url: String,
}

pub fn resolve_environment() -> Result<ManagerEnvConfig, String> {
    let repo = env::var("PUBLIC_GITHUB_REPO")
        .or_else(|_| env::var("VITE_PUBLIC_GITHUB_REPO"))
        .unwrap_or_else(|_| "IamAzmathullaShaikh/Emberbird".to_string());

    if repo.trim().is_empty() {
        return Err("PUBLIC_GITHUB_REPO must be explicitly configured.".to_string());
    }

    let repo_url = env::var("PUBLIC_GITHUB_REPO_URL")
        .or_else(|_| env::var("VITE_PUBLIC_GITHUB_REPO_URL"))
        .unwrap_or_else(|_| format!("https://github.com/{}", repo));

    let releases_url = env::var("PUBLIC_RELEASES_URL")
        .or_else(|_| env::var("VITE_PUBLIC_RELEASES_URL"))
        .unwrap_or_else(|_| format!("https://github.com/{}/releases", repo));

    Ok(ManagerEnvConfig {
        github_repo: repo,
        repo_url,
        releases_url,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resolve_environment_defaults() {
        let cfg = resolve_environment().expect("Environment should resolve with defaults");
        assert_eq!(cfg.github_repo, "IamAzmathullaShaikh/Emberbird");
        assert!(cfg.repo_url.contains("Emberbird"));
        assert!(cfg.releases_url.contains("releases"));
    }
}
