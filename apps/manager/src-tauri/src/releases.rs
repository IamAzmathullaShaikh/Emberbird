use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ReleaseAsset {
    pub name: String,
    pub size: u64,
    pub browser_download_url: String,
    pub architecture: String,
    pub root_flavor: String,
    pub gapps_flavor: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ReleaseInfo {
    pub tag_name: String,
    pub name: String,
    pub published_at: String,
    pub body: String,
    pub assets: Vec<ReleaseAsset>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct UpdateStatus {
    pub update_available: bool,
    pub current_version: String,
    pub latest_version: String,
    pub latest_release: Option<ReleaseInfo>,
}

pub fn clean_version(ver: &str) -> String {
    ver.trim().trim_start_matches(|c| c == 'v' || c == 'V').to_string()
}

pub fn compare_semver(current: &str, latest: &str) -> i32 {
    let c_parts: Vec<u64> = clean_version(current)
        .split('.')
        .filter_map(|s| s.parse::<u64>().ok())
        .collect();

    let l_parts: Vec<u64> = clean_version(latest)
        .split('.')
        .filter_map(|s| s.parse::<u64>().ok())
        .collect();

    let max_len = std::cmp::max(c_parts.len(), l_parts.len());

    for i in 0..max_len {
        let c_num = *c_parts.get(i).unwrap_or(&0);
        let l_num = *l_parts.get(i).unwrap_or(&0);
        if l_num > c_num {
            return 1; // latest is higher
        } else if l_num < c_num {
            return -1; // current is higher
        }
    }
    0
}

pub fn is_update_available(current: &str, latest: &str) -> bool {
    compare_semver(current, latest) > 0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_clean_version() {
        assert_eq!(clean_version("v2311.40000.5.0"), "2311.40000.5.0");
        assert_eq!(clean_version("V1.0.0 "), "1.0.0");
    }

    #[test]
    fn test_compare_semver() {
        assert_eq!(compare_semver("2311.40000.5.0", "2311.40000.5.0"), 0);
        assert_eq!(compare_semver("2311.40000.5.0", "2311.40000.6.0"), 1);
        assert_eq!(compare_semver("2311.40000.6.0", "2311.40000.5.0"), -1);
    }

    #[test]
    fn test_is_update_available() {
        assert!(is_update_available("2311.40000.5.0", "2311.40000.6.0"));
        assert!(!is_update_available("2311.40000.5.0", "2311.40000.5.0"));
    }
}
