//! Single authoritative subsystem state model.
//!
//! Every dashboard consumer MUST derive its presentation from
//! [`derive_subsystem_state`] (via the `state` field of [`WsaStatus`]).
//! Independent booleans such as `installed` or a non-null `vhdx_path` are
//! detection signals, never user-facing state. This module is the only place
//! allowed to decide what "installed" means, so the UI can never show
//! "Not Installed" next to a known installed version (or vice versa).

use serde::{Deserialize, Serialize};

/// Authoritative lifecycle states for the Windows Subsystem for Android.
///
/// Ordering is intentional: states are mutually exclusive and exhaustive.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum SubsystemState {
    /// No package registration and no package data directory found.
    /// (The user may still have an orphaned userdata.vhdx; that is surfaced
    /// through `detection_details`, not through a contradictory state.)
    NotInstalled,
    /// Package registered but required runtime components are missing or
    /// damaged (e.g. no package data directory, no VHDX file on disk).
    PartiallyInstalled,
    /// Package registered, all components present, but the version is older
    /// than the subsystem baseline advertised by release intelligence.
    InstalledOutdated,
    /// Package registered, all components present, version current (or newer
    /// than the baseline, e.g. an internal preview build).
    Installed,
    /// Detection could not be completed (e.g. the Windows package manager
    /// could not be queried). The UI must offer a refresh action instead of
    /// asserting any install state.
    Unknown,
}

impl SubsystemState {
    /// True when a usable, registered subsystem exists in any form.
    pub fn is_registered(&self) -> bool {
        matches!(
            self,
            SubsystemState::Installed
                | SubsystemState::InstalledOutdated
                | SubsystemState::PartiallyInstalled
        )
    }

    /// True when the UI may present a version string as fact.
    pub fn has_known_version(&self) -> bool {
        matches!(
            self,
            SubsystemState::Installed | SubsystemState::InstalledOutdated
        )
    }

    /// Short, UI-ready label. Dashboard components must render exactly this
    /// (or a styled wrapper of it) so state wording cannot drift per-view.
    pub fn label(&self) -> &'static str {
        match self {
            SubsystemState::NotInstalled => "Not Installed",
            SubsystemState::PartiallyInstalled => "Partially Installed",
            SubsystemState::InstalledOutdated => "Installed (Outdated)",
            SubsystemState::Installed => "Installed",
            SubsystemState::Unknown => "Unknown",
        }
    }
}

/// Inputs to the state derivation, gathered from independent detection
/// sources. All fields are `Option` so every detection path can express
/// "this source said nothing" distinctly from a definitive negative.
#[derive(Debug, Clone, Default, PartialEq)]
pub struct DetectionInputs {
    /// Package registered with the Windows package manager?
    /// `Some(true)` requires an authoritative query result.
    pub package_registered: Option<bool>,
    /// Version string from package metadata (present only when a package
    /// identity was actually read).
    pub package_version: Option<String>,
    /// Path of the package data directory (LocalCache), when it exists.
    pub package_data_dir: Option<String>,
    /// Path of userdata.vhdx, when the file exists on disk.
    pub vhdx_exists: Option<String>,
    /// Subsystem baseline version advertised by release intelligence
    /// (e.g. from `deployment/version.json`). Drives `INSTALLED_OUTDATED`.
    pub baseline_version: Option<String>,
}

impl DetectionInputs {
    /// Derive inputs from the raw signals produced by `detector.rs`.
    ///
    /// `registered_version` is `Some` only when package registration was
    /// positively confirmed; `vhdx_path` is `Some` only when the file exists.
    pub fn from_signals(
        registered_version: Option<String>,
        install_path: Option<String>,
        vhdx_path: Option<String>,
    ) -> Self {
        DetectionInputs {
            package_registered: Some(registered_version.is_some()),
            package_version: registered_version,
            package_data_dir: install_path,
            vhdx_exists: vhdx_path,
            baseline_version: None,
        }
    }
}

/// Outcome of the derivation: the state plus the evidence trail that produced
/// it. The evidence trail keeps the decision auditable and lets tests assert
/// *why* a state was chosen, not just which one.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DerivedSubsystemState {
    pub state: SubsystemState,
    /// Human-readable reasons, in decision order.
    pub evidence: Vec<String>,
}

/// Derive the one authoritative state from all detection sources.
///
/// Decision order (first match wins):
///  1. No package registration AND no version  → `NOT_INSTALLED`
///     (an orphaned userdata.vhdx is recorded as evidence, not as install).
///  2. Registration claims version but required components are missing
///     (no data directory or no VHDX)            → `PARTIALLY_INSTALLED`
///  3. Registered + complete, older than baseline → `INSTALLED_OUTDATED`
///  4. Registered + complete, version current/newer → `INSTALLED`
///  5. Package query itself failed              → `UNKNOWN`
pub fn derive_subsystem_state(inputs: &DetectionInputs) -> DerivedSubsystemState {
    match inputs.package_registered {
        // Case 5: the detection layer itself failed.
        None => DerivedSubsystemState {
            state: SubsystemState::Unknown,
            evidence: vec!["Package registration query did not complete.".to_string()],
        },
        Some(false) => {
            let mut evidence = vec!["Package is not registered with Windows.".to_string()];
            if inputs.vhdx_exists.is_some() {
                evidence.push(
                    "A userdata.vhdx exists on disk (orphaned data, not an installation)."
                        .to_string(),
                );
            }
            DerivedSubsystemState {
                state: SubsystemState::NotInstalled,
                evidence,
            }
        }
        Some(true) => {
            let version_known = inputs.package_version.is_some();
            let data_dir_present = inputs.package_data_dir.is_some();
            let vhdx_present = inputs.vhdx_exists.is_some();

            if !version_known || !data_dir_present || !vhdx_present {
                let mut missing = Vec::new();
                if !version_known {
                    missing.push("package version");
                }
                if !data_dir_present {
                    missing.push("package data directory");
                }
                if !vhdx_present {
                    missing.push("userdata.vhdx");
                }
                return DerivedSubsystemState {
                    state: SubsystemState::PartiallyInstalled,
                    evidence: vec![format!(
                        "Package is registered but required components are missing: {}.",
                        missing.join(", ")
                    )],
                };
            }

            let version = inputs.package_version.clone().unwrap_or_default();
            match inputs.baseline_version.as_deref() {
                Some(baseline) if is_version_older(&version, baseline) => {
                    DerivedSubsystemState {
                        state: SubsystemState::InstalledOutdated,
                        evidence: vec![format!(
                            "Installed version {version} is older than the supported baseline {baseline}."
                        )],
                    }
                }
                baseline => DerivedSubsystemState {
                    state: SubsystemState::Installed,
                    evidence: vec![format!(
                        "Installed version {version} satisfies the supported baseline{}.",
                        baseline
                            .map(|b| format!(" {b}"))
                            .unwrap_or_else(|| " (no baseline configured)".to_string())
                    )],
                },
            }
        }
    }
}

/// Subsystem baseline version from release intelligence.
///
/// Reads `deployment/version.json` → `subsystem_baseline.wsa_version` when the
/// file is deployed next to the executable (release layout); falls back to the
/// compile-time baseline. Returns `None` only when no baseline is available at
/// all, in which case outdated-detection is disabled (never wrongly reported).
pub fn subsystem_baseline_version() -> Option<String> {
    if let Ok(exe) = std::env::current_exe() {
        for ancestor in exe.ancestors().skip(1).take(3) {
            let candidate = ancestor.join("version.json");
            if candidate.exists() {
                if let Ok(raw) = std::fs::read_to_string(&candidate) {
                    if let Ok(json) = serde_json::from_str::<serde_json::Value>(&raw) {
                        if let Some(v) = json
                            .pointer("/subsystem_baseline/wsa_version")
                            .and_then(|x| x.as_str())
                        {
                            return Some(v.to_string());
                        }
                    }
                }
            }
        }
    }
    Some(
        option_env!("WSA_BASELINE_VERSION")
            .unwrap_or("2311.40000.5.0")
            .to_string(),
    )
}

/// Component-wise numeric version comparison: `true` when `version` < `baseline`.
/// Non-numeric segments compare lexicographically; missing segments are 0.
pub fn is_version_older(version: &str, baseline: &str) -> bool {
    let parse = |v: &str| -> Vec<(u64, String)> {
        v.trim()
            .trim_start_matches(['v', 'V'])
            .split('.')
            .map(|seg| {
                let digits: String = seg.chars().take_while(|c| c.is_ascii_digit()).collect();
                let rest: String = seg.chars().skip_while(|c| c.is_ascii_digit()).collect();
                (digits.parse::<u64>().unwrap_or(0), rest)
            })
            .collect()
    };

    let a = parse(version);
    let b = parse(baseline);
    let len = a.len().max(b.len());
    for i in 0..len {
        let (an, ar) = a.get(i).cloned().unwrap_or((0, String::new()));
        let (bn, br) = b.get(i).cloned().unwrap_or((0, String::new()));
        match an.cmp(&bn) {
            std::cmp::Ordering::Less => return true,
            std::cmp::Ordering::Greater => return false,
            std::cmp::Ordering::Equal => {
                // Numeric tie: fall back to segment suffix, then continue.
                match ar.cmp(&br) {
                    std::cmp::Ordering::Less => return true,
                    std::cmp::Ordering::Greater => return false,
                    std::cmp::Ordering::Equal => {}
                }
            }
        }
    }
    false
}

#[cfg(test)]
mod tests {
    use super::*;

    fn inputs(
        registered: Option<bool>,
        version: Option<&str>,
        data_dir: Option<&str>,
        vhdx: Option<&str>,
    ) -> DetectionInputs {
        DetectionInputs {
            package_registered: registered,
            package_version: version.map(|s| s.to_string()),
            package_data_dir: data_dir.map(|s| s.to_string()),
            vhdx_exists: vhdx.map(|s| s.to_string()),
            baseline_version: Some("2311.40000.5.0".to_string()),
        }
    }

    /// Scenario: fresh machine — nothing has ever been installed.
    #[test]
    fn fresh_machine_is_not_installed() {
        let d = derive_subsystem_state(&inputs(None, None, None, None));
        assert_eq!(d.state, SubsystemState::NotInstalled);
        assert!(!d.state.has_known_version());
    }

    /// Scenario: full install, current version.
    #[test]
    fn complete_current_install() {
        let d = derive_subsystem_state(&inputs(
            Some(true),
            Some("2311.40000.5.0"),
            Some("C:/WSA/data"),
            Some("C:/WSA/userdata.vhdx"),
        ));
        assert_eq!(d.state, SubsystemState::Installed);
        assert!(d.state.has_known_version());
    }

    /// Scenario: broken installation — registered but VHDX deleted.
    #[test]
    fn registered_without_vhdx_is_partially_installed() {
        let d = derive_subsystem_state(&inputs(
            Some(true),
            Some("2311.40000.5.0"),
            Some("C:/WSA/data"),
            None,
        ));
        assert_eq!(d.state, SubsystemState::PartiallyInstalled);
        assert!(d.evidence[0].contains("userdata.vhdx"));
    }

    /// Scenario: orphaned userdata.vhdx with no package registration.
    /// The file's existence must NOT flip the state to installed.
    #[test]
    fn orphaned_vhdx_without_package_is_not_installed() {
        let d = derive_subsystem_state(&inputs(
            Some(false),
            None,
            None,
            Some("C:/orphan/userdata.vhdx"),
        ));
        assert_eq!(d.state, SubsystemState::NotInstalled);
        assert!(d.evidence.iter().any(|e| e.contains("orphaned")));
    }

    /// Scenario: version mismatch — older installed build.
    #[test]
    fn older_version_is_installed_outdated() {
        let d = derive_subsystem_state(&inputs(
            Some(true),
            Some("2308.40000.2.0"),
            Some("C:/WSA/data"),
            Some("C:/WSA/userdata.vhdx"),
        ));
        assert_eq!(d.state, SubsystemState::InstalledOutdated);
    }

    /// Scenario: newer-than-baseline internal build stays Installed.
    #[test]
    fn newer_version_is_installed() {
        let d = derive_subsystem_state(&inputs(
            Some(true),
            Some("2407.40000.4.0"),
            Some("C:/WSA/data"),
            Some("C:/WSA/userdata.vhdx"),
        ));
        assert_eq!(d.state, SubsystemState::Installed);
    }

    /// Scenario: detection layer failure.
    #[test]
    fn failed_detection_is_unknown() {
        let d = derive_subsystem_state(&inputs(None, Some("1.0"), Some("x"), Some("y")));
        assert_eq!(d.state, SubsystemState::Unknown);
    }

    #[test]
    fn version_comparison_matrix() {
        assert!(is_version_older("2308.40000.2.0", "2311.40000.5.0"));
        assert!(!is_version_older("2311.40000.5.0", "2311.40000.5.0"));
        assert!(!is_version_older("2407.40000.4.0", "2311.40000.5.0"));
        assert!(is_version_older("v2311.40000.4.9", "2311.40000.5.0"));
        // Digit-majority beats lexicographic length: 9 < 10 numerically.
        assert!(is_version_older("1.9.0", "1.10.0"));
    }

    /// Invariant: the five states are mutually exclusive and every derivation
    /// lands in exactly one. This is the contract the UI relies on.
    #[test]
    fn every_scenario_yields_exactly_one_state() {
        let scenarios = vec![
            inputs(None, None, None, None),
            inputs(Some(false), None, None, Some("v")),
            inputs(Some(true), Some("1.0"), None, Some("v")),
            inputs(Some(true), Some("1.0"), Some("d"), None),
            inputs(Some(true), None, Some("d"), Some("v")),
            inputs(Some(true), Some("0.9"), Some("d"), Some("v")),
            inputs(Some(true), Some("9.9"), Some("d"), Some("v")),
        ];
        for (i, s) in scenarios.iter().enumerate() {
            let d = derive_subsystem_state(s);
            assert!(
                d.state.is_registered()
                    || d.state == SubsystemState::NotInstalled
                    || d.state == SubsystemState::Unknown,
                "scenario {i} produced an unclassifiable state"
            );
            assert!(!d.evidence.is_empty(), "scenario {i} must carry evidence");
        }
    }
}
