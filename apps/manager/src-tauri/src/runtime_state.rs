//! The runtime lifecycle state engine (PH-02).
//!
//! The Manager UI (`state.rs`) presents install state; the CLI (`platform/cli`)
//! drives it. This module is the *lifecycle* both surfaces must eventually
//! share: fourteen states, a declared legal-transition table, an audit trail,
//! and recovery rules for what a restart may honestly assume.
//!
//! It exists now because PH-02's exit checklist requires the model *before*
//! any surface can present lifecycle state honestly — which is what `state.rs`
//! already does for install state.

use std::path::{Path, PathBuf};

use chrono::{SecondsFormat, Utc};
use serde::{Deserialize, Serialize};

use crate::detector::detect_subsystem;
use crate::state::SubsystemState;

/// Authoritative lifecycle states for the Android runtime on Windows.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, specta::Type)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum RuntimeState {
    Unknown,
    NotInstalled,
    Checking,
    Installing,
    Installed,
    Starting,
    Running,
    Stopping,
    Stopped,
    Degraded,
    Broken,
    Updating,
    RollingBack,
    Uninstalling,
}

/// A refused state change. Callers must handle it: an illegal move is a typed
/// error, never a silently wrong status surface.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TransitionError {
    /// The table does not allow this move.
    IllegalMove {
        from: RuntimeState,
        to: RuntimeState,
    },
    /// The machine is already in the requested state.
    AlreadyInState(RuntimeState),
}

impl std::fmt::Display for TransitionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TransitionError::IllegalMove { from, to } => {
                write!(
                    f,
                    "illegal lifecycle move {} -> {}",
                    from.as_str(),
                    to.as_str()
                )
            }
            TransitionError::AlreadyInState(state) => {
                write!(f, "already in state {}", state.as_str())
            }
        }
    }
}

impl std::error::Error for TransitionError {}

/// A recorded state change: what moved, when, and why.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, specta::Type)]
pub struct StateChange {
    pub from: RuntimeState,
    pub to: RuntimeState,
    /// Capture time, UTC, RFC 3339 with milliseconds.
    pub at: String,
    /// Why the move happened (for example "health check failed").
    pub reason: String,
}

impl RuntimeState {
    pub fn as_str(self) -> &'static str {
        match self {
            RuntimeState::Unknown => "UNKNOWN",
            RuntimeState::NotInstalled => "NOT_INSTALLED",
            RuntimeState::Checking => "CHECKING",
            RuntimeState::Installing => "INSTALLING",
            RuntimeState::Installed => "INSTALLED",
            RuntimeState::Starting => "STARTING",
            RuntimeState::Running => "RUNNING",
            RuntimeState::Stopping => "STOPPING",
            RuntimeState::Stopped => "STOPPED",
            RuntimeState::Degraded => "DEGRADED",
            RuntimeState::Broken => "BROKEN",
            RuntimeState::Updating => "UPDATING",
            RuntimeState::RollingBack => "ROLLING_BACK",
            RuntimeState::Uninstalling => "UNINSTALLING",
        }
    }

    /// Short, UI-ready label. Surfaces must render exactly this so state
    /// wording cannot drift per view.
    pub fn label(self) -> &'static str {
        match self {
            RuntimeState::Unknown => "Unknown",
            RuntimeState::NotInstalled => "Not Installed",
            RuntimeState::Checking => "Checking",
            RuntimeState::Installing => "Installing",
            RuntimeState::Installed => "Installed",
            RuntimeState::Starting => "Starting",
            RuntimeState::Running => "Running",
            RuntimeState::Stopping => "Stopping",
            RuntimeState::Stopped => "Stopped",
            RuntimeState::Degraded => "Degraded",
            RuntimeState::Broken => "Broken",
            RuntimeState::Updating => "Updating",
            RuntimeState::RollingBack => "Rolling Back",
            RuntimeState::Uninstalling => "Uninstalling",
        }
    }

    /// True while an operation is in flight. A surface may not offer a
    /// conflicting action in these states.
    pub fn is_busy(self) -> bool {
        matches!(
            self,
            RuntimeState::Checking
                | RuntimeState::Installing
                | RuntimeState::Starting
                | RuntimeState::Stopping
                | RuntimeState::Updating
                | RuntimeState::RollingBack
                | RuntimeState::Uninstalling
        )
    }

    /// The states reachable in one legal step. Anything else is rejected.
    ///
    /// Every settled state can re-enter `Checking`: reality can change behind
    /// the application, and re-checking is the only honest way to reconcile.
    pub fn legal_next(self) -> &'static [RuntimeState] {
        use RuntimeState::*;
        match self {
            Unknown => &[Checking],
            NotInstalled => &[Checking, Installing],
            Checking => &[Installed, NotInstalled, Unknown, Broken],
            Installing => &[Installed, Broken, NotInstalled],
            Installed => &[Starting, Updating, Uninstalling, Stopped, Broken, Checking],
            Starting => &[Running, Degraded, Broken],
            Running => &[Stopping, Degraded, Broken, Updating, Uninstalling, Checking],
            Stopping => &[Stopped, Broken],
            Stopped => &[Starting, Installing, Uninstalling, Checking, Broken],
            Degraded => &[Running, Stopping, Broken, Updating, Uninstalling, Checking],
            Broken => &[Installing, RollingBack, Uninstalling, Checking],
            Updating => &[Running, Stopped, RollingBack, Broken],
            RollingBack => &[Running, Stopped, Installed, Broken],
            Uninstalling => &[NotInstalled, Broken],
        }
    }

    /// Whether this state can move to `next` in one legal step.
    pub fn can_transition_to(self, next: RuntimeState) -> bool {
        self.legal_next().contains(&next)
    }

    /// Map a detection verdict (`state.rs`) onto the lifecycle.
    ///
    /// Detection can never report an in-flight operation, so busy states are
    /// unreachable here by construction — they are entered only by explicit
    /// transitions.
    pub fn from_subsystem(state: SubsystemState) -> RuntimeState {
        match state {
            SubsystemState::Unknown => RuntimeState::Unknown,
            SubsystemState::NotInstalled => RuntimeState::NotInstalled,
            SubsystemState::PartiallyInstalled => RuntimeState::Broken,
            SubsystemState::InstalledOutdated => RuntimeState::Installed,
            SubsystemState::Installed => RuntimeState::Installed,
        }
    }
}

/// The lifecycle machine. Owns the current state and the audit trail.
#[derive(Debug, Clone)]
pub struct RuntimeStateMachine {
    current: RuntimeState,
    history: Vec<StateChange>,
}

impl RuntimeStateMachine {
    pub fn new(initial: RuntimeState) -> Self {
        RuntimeStateMachine {
            current: initial,
            history: Vec::new(),
        }
    }

    pub fn current(&self) -> RuntimeState {
        self.current
    }

    pub fn history(&self) -> &[StateChange] {
        &self.history
    }

    pub fn legal_next(&self) -> &'static [RuntimeState] {
        self.current.legal_next()
    }

    /// Move to `next` if the table allows it; record the move either way the
    /// caller can observe. A refused move changes no state and writes no
    /// history — an illegal transition is a typed error the caller handles.
    pub fn transition(
        &mut self,
        next: RuntimeState,
        reason: &str,
    ) -> Result<StateChange, TransitionError> {
        if next == self.current {
            return Err(TransitionError::AlreadyInState(self.current));
        }
        if !self.current.can_transition_to(next) {
            return Err(TransitionError::IllegalMove {
                from: self.current,
                to: next,
            });
        }
        let change = StateChange {
            from: self.current,
            to: next,
            at: now(),
            reason: reason.to_string(),
        };
        self.current = next;
        self.history.push(change.clone());
        Ok(change)
    }

    /// A snapshot suitable for persisting across sessions.
    pub fn snapshot(&self) -> PersistedLifecycle {
        PersistedLifecycle {
            version: LIFECYCLE_SCHEMA_VERSION,
            state: self.current,
            history: self.history.clone(),
        }
    }

    /// Serialize this lifecycle for storage.
    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(&self.snapshot())
    }

    /// Rebuild a machine from persisted evidence, reconciled with the fact that
    /// the process is starting fresh.
    ///
    /// Recovery is deliberately **not** a transition. A transition is a move the
    /// application chose; this is a re-baselining forced by a restart. The rule
    /// is one-directional: a recovered state may be *less* specific than what
    /// was persisted, never more.
    pub fn recover(snapshot: PersistedLifecycle) -> Result<RecoveryReport, RecoveryError> {
        if snapshot.version != LIFECYCLE_SCHEMA_VERSION {
            return Err(RecoveryError::UnsupportedSchema {
                found: snapshot.version,
                expected: LIFECYCLE_SCHEMA_VERSION,
            });
        }

        let was = snapshot.state;
        match reconcile(was) {
            // Nothing a restart can invalidate: restore exactly, trail intact.
            None => Ok(RecoveryReport {
                machine: RuntimeStateMachine {
                    current: was,
                    history: snapshot.history,
                },
                outcome: RecoveryOutcome::Restored { state: was },
            }),
            // Re-baseline: keep the audit trail, then record the recovery
            // itself so the trail shows the restart, not a silent jump.
            Some((presumed, action)) => {
                let mut history = snapshot.history;
                history.push(StateChange {
                    from: was,
                    to: presumed,
                    at: now(),
                    reason: format!("restart recovery: {}", action.as_str()),
                });
                Ok(RecoveryReport {
                    machine: RuntimeStateMachine {
                        current: presumed,
                        history,
                    },
                    outcome: if was.is_busy() {
                        RecoveryOutcome::Interrupted {
                            was,
                            presumed,
                            action,
                        }
                    } else {
                        RecoveryOutcome::ReEstablished {
                            was,
                            presumed,
                            action,
                        }
                    },
                })
            }
        }
    }
}

/// The schema version of a persisted lifecycle. Bump on any breaking change;
/// `recover` refuses anything it cannot read rather than guessing.
pub const LIFECYCLE_SCHEMA_VERSION: u32 = 1;

/// What survives a restart.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, specta::Type)]
pub struct PersistedLifecycle {
    pub version: u32,
    /// The state the process last recorded.
    pub state: RuntimeState,
    /// The audit trail as recorded, so a recovery cannot erase history.
    pub history: Vec<StateChange>,
}

/// What must happen before the persisted state can be trusted again.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum RecoveryAction {
    /// Gather evidence from the machine again.
    ReDetect,
    /// Start the runtime, which is the only way to prove it runs.
    Restart,
    /// Undo the half-applied change before anything else.
    RollBack,
}

impl RecoveryAction {
    /// Stable token for logs and evidence.
    pub fn as_str(self) -> &'static str {
        match self {
            RecoveryAction::ReDetect => "RE_DETECT",
            RecoveryAction::Restart => "RESTART",
            RecoveryAction::RollBack => "ROLL_BACK",
        }
    }

    /// Whether the recovery can be performed without elevation.
    pub fn is_automatic(self) -> bool {
        matches!(self, RecoveryAction::ReDetect | RecoveryAction::Restart)
    }
}

/// How a persisted state was reconciled with a restart.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE", tag = "kind")]
pub enum RecoveryOutcome {
    /// The persisted state asserted nothing a restart can invalidate.
    Restored { state: RuntimeState },
    /// The persisted state asserted something that cannot survive a restart.
    ReEstablished {
        was: RuntimeState,
        presumed: RuntimeState,
        action: RecoveryAction,
    },
    /// An operation was in flight when the process ended.
    Interrupted {
        was: RuntimeState,
        presumed: RuntimeState,
        action: RecoveryAction,
    },
}

/// A rejected recovery. Never silently ignored.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RecoveryError {
    UnsupportedSchema { found: u32, expected: u32 },
}

impl std::fmt::Display for RecoveryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RecoveryError::UnsupportedSchema { found, expected } => write!(
                f,
                "unsupported lifecycle schema {found} (this build writes {expected})"
            ),
        }
    }
}

impl std::error::Error for RecoveryError {}

/// The recovered machine together with how it was reconciled.
#[derive(Debug, Clone)]
pub struct RecoveryReport {
    pub machine: RuntimeStateMachine,
    pub outcome: RecoveryOutcome,
}

/// Map a persisted state onto what a fresh process may honestly assume.
///
/// `None` means the state can be restored unchanged.
fn reconcile(persisted: RuntimeState) -> Option<(RuntimeState, RecoveryAction)> {
    use RuntimeState::*;
    match persisted {
        // Nothing a restart can invalidate: no live-process claim, no operation
        // in flight. These are restored exactly.
        Unknown | NotInstalled | Installed | Broken => None,
        // In flight when the process ended: the outcome is unknown, so nothing
        // may be concluded from it — least of all that it succeeded.
        Checking | Installing | Uninstalling => Some((Unknown, RecoveryAction::ReDetect)),
        // Installed, but the change did not finish. A fault is present and the
        // half-applied change must be undone; `BROKEN -> ROLLING_BACK` is legal.
        Updating | RollingBack => Some((Broken, RecoveryAction::RollBack)),
        // The runtime is installed; whether it is running cannot survive a
        // restart, and starting it is the only way to establish that.
        Starting | Stopping | Running | Stopped => Some((Installed, RecoveryAction::Restart)),
        // A fault cannot be confirmed across a restart, only re-checked.
        Degraded => Some((Installed, RecoveryAction::ReDetect)),
    }
}

/// Failures reading a persisted lifecycle.
#[derive(Debug)]
pub enum LifecycleLoadError {
    Io(std::io::Error),
    Schema(RecoveryError),
    /// The file exists but is not the JSON shape this build writes.
    Malformed(String),
}

impl std::fmt::Display for LifecycleLoadError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            LifecycleLoadError::Io(error) => write!(f, "lifecycle store I/O error: {error}"),
            LifecycleLoadError::Schema(error) => write!(f, "lifecycle schema refused: {error}"),
            LifecycleLoadError::Malformed(detail) => {
                write!(f, "lifecycle snapshot malformed: {detail}")
            }
        }
    }
}

impl std::error::Error for LifecycleLoadError {}

impl From<std::io::Error> for LifecycleLoadError {
    fn from(error: std::io::Error) -> Self {
        LifecycleLoadError::Io(error)
    }
}

impl From<serde_json::Error> for LifecycleLoadError {
    fn from(error: serde_json::Error) -> Self {
        LifecycleLoadError::Malformed(error.to_string())
    }
}

impl From<RecoveryError> for LifecycleLoadError {
    fn from(error: RecoveryError) -> Self {
        LifecycleLoadError::Schema(error)
    }
}

/// Where persisted lifecycle snapshots live.
pub struct LifecycleStore {
    path: PathBuf,
}

impl LifecycleStore {
    pub fn new(path: impl Into<PathBuf>) -> Self {
        LifecycleStore { path: path.into() }
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    /// Write the snapshot atomically, so a crash mid-write cannot leave a torn
    /// file that a later run would have to interpret.
    pub fn save(&self, machine: &RuntimeStateMachine) -> Result<(), LifecycleLoadError> {
        let body = machine.to_json()?;
        if let Some(parent) = self.path.parent() {
            if !parent.as_os_str().is_empty() {
                std::fs::create_dir_all(parent)?;
            }
        }
        let staged = self.path.with_extension("tmp");
        std::fs::write(&staged, body)?;
        std::fs::rename(&staged, &self.path)?;
        Ok(())
    }

    /// Read the snapshot, if any.
    ///
    /// A corrupt or unreadable snapshot is an **error**, never a silent
    /// `UNKNOWN`: the difference is between "we do not know" and "we cannot
    /// tell", and only the caller can decide how to re-detect.
    pub fn load(&self) -> Result<Option<RecoveryReport>, LifecycleLoadError> {
        match std::fs::read_to_string(&self.path) {
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(None),
            Err(error) => Err(LifecycleLoadError::Io(error)),
            Ok(body) => {
                let snapshot: PersistedLifecycle = serde_json::from_str(&body)?;
                Ok(Some(RuntimeStateMachine::recover(snapshot)?))
            }
        }
    }

    /// Remove the snapshot. Absence is not an error.
    pub fn clear(&self) -> Result<(), LifecycleLoadError> {
        match std::fs::remove_file(&self.path) {
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
            other => other.map_err(LifecycleLoadError::Io),
        }
    }
}

/// How a fresh process reconciled its persisted lifecycle with live detection.
#[derive(Debug, Clone, Serialize, specta::Type)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE", tag = "kind")]
pub enum ReconciliationOutcome {
    /// No snapshot existed; the lifecycle is detection's verdict.
    Fresh { state: RuntimeState },
    /// A snapshot was recovered and then refined by detection.
    Recovered {
        /// What the recovery rule produced before detection refined it.
        recovered: RuntimeState,
        /// The state after detection's verdict was folded in.
        state: RuntimeState,
        /// The action the recovery rule demanded (RE_DETECT / RESTART / ROLL_BACK).
        action: String,
    },
    /// The snapshot could not be trusted (corrupt, future schema): refused
    /// loudly, never silently replaced with an optimistic default.
    Unreadable { reason: String },
}

/// The command surface's payload: the reconciled lifecycle plus its audit tail.
#[derive(Debug, Clone, Serialize, specta::Type)]
pub struct LifecycleReport {
    /// The current lifecycle state, reconciled with live detection.
    pub state: RuntimeState,
    /// Whether an operation is in flight (surfaces must not offer conflicting
    /// actions in these states).
    pub busy: bool,
    /// The states reachable in one legal step from here.
    pub legal_next: Vec<RuntimeState>,
    /// How this process reconciled the persisted lifecycle, if one existed.
    pub outcome: ReconciliationOutcome,
    /// The last audit entries, newest last, capped for transport.
    pub history_tail: Vec<StateChange>,
}

/// Audit-tail length sent over IPC — the trail can grow without bound, the
/// surface needs only the recent moves.
const HISTORY_TAIL_LEN: usize = 8;

/// Reconcile a lifecycle with live detection evidence.
///
/// Recovery rules (never more specific than persisted — a restart cannot prove
/// a live process) produce the baseline; detection refines it through the one
/// universal legal hop (`Checking`), because reality may have changed behind
/// the application. In-flight states are unreachable by construction: detection
/// cannot report an operation it did not start. The load failure, if any,
/// arrives as its display reason — `LifecycleLoadError` wraps a non-`Clone`
/// `io::Error`.
fn reconcile_with_detection(
    persisted: Result<Option<RecoveryReport>, String>,
) -> (RuntimeStateMachine, ReconciliationOutcome) {
    // Detection's verdict, folded in through the one universal legal hop
    // (`Checking`): every settled state may re-enter `Checking`, and detection
    // only ever returns a settled state — so this hop cannot manufacture an
    // operation the host never performed.
    let detected = RuntimeState::from_subsystem(detect_subsystem().state);
    let refine_with_detection = |machine: &mut RuntimeStateMachine, why: &str| {
        let _ = machine.transition(RuntimeState::Checking, why);
        let _ = machine.transition(detected, "live detection verdict");
    };

    match persisted {
        Err(reason) => {
            let mut machine = RuntimeStateMachine::new(RuntimeState::Unknown);
            refine_with_detection(
                &mut machine,
                "persisted lifecycle was unreadable; re-checking reality",
            );
            (machine, ReconciliationOutcome::Unreadable { reason })
        }
        Ok(Some(report)) => {
            let (recovered, action) = match &report.outcome {
                RecoveryOutcome::Restored { state } => (*state, "RE_STORED".to_string()),
                RecoveryOutcome::ReEstablished {
                    presumed, action, ..
                } => (*presumed, action.as_str().to_string()),
                RecoveryOutcome::Interrupted {
                    presumed, action, ..
                } => (*presumed, action.as_str().to_string()),
            };
            let mut machine = report.machine;
            refine_with_detection(
                &mut machine,
                "reconciling persisted lifecycle with live detection",
            );
            let final_state = machine.current();
            (
                machine,
                ReconciliationOutcome::Recovered {
                    recovered,
                    state: final_state,
                    action,
                },
            )
        }
        Ok(None) => {
            let machine = RuntimeStateMachine::new(detected);
            (machine, ReconciliationOutcome::Fresh { state: detected })
        }
    }
}

/// Build the IPC report for the reconciled lifecycle.
pub fn lifecycle_report() -> LifecycleReport {
    lifecycle_report_with_store(&LifecycleStore::new(default_store_path()))
}

/// `lifecycle_report` against an explicit store — the seam that makes the IPC
/// path testable without touching the real user-data file.
///
/// When detection says the host disagrees with the recovered baseline (for
/// example persisted `RUNNING` recovered as `INSTALLED`, but the host now
/// reports `NotInstalled`), the **detection verdict wins** — the persisted
/// trail is evidence about the past, the host is evidence about now. A corrupt
/// or future-schema snapshot is never overwritten: the refusal is reported and
/// the file is left for forensics.
pub fn lifecycle_report_with_store(store: &LifecycleStore) -> LifecycleReport {
    let load_result = store.load();
    let (machine, outcome) = reconcile_with_detection(match &load_result {
        Ok(value) => Ok(value.clone()),
        Err(error) => Err(error.to_string()),
    });
    if matches!(
        outcome,
        ReconciliationOutcome::Recovered { .. } | ReconciliationOutcome::Fresh { .. }
    ) {
        // Persist the reconciled trail so the next start's recovery reconciles
        // against evidence recorded *now*, not a snapshot from before this
        // process existed. A persistence failure is non-fatal: the report
        // stands on live detection, and the next start simply sees the old file.
        let _ = store.save(&machine);
    }
    LifecycleReport {
        state: machine.current(),
        busy: machine.current().is_busy(),
        legal_next: machine.legal_next().to_vec(),
        outcome,
        history_tail: machine
            .history()
            .iter()
            .rev()
            .take(HISTORY_TAIL_LEN)
            .rev()
            .cloned()
            .collect(),
    }
}

/// Where the lifecycle snapshot lives. `%LOCALAPPDATA%\Emberbird\lifecycle.json`
/// — the same vendor directory `backup.rs` already established for app data.
pub fn default_store_path() -> PathBuf {
    std::env::var("LOCALAPPDATA")
        .map(|base| PathBuf::from(base).join("Emberbird").join("lifecycle.json"))
        .unwrap_or_else(|_| PathBuf::from("lifecycle.json"))
}

fn now() -> String {
    Utc::now().to_rfc3339_opts(SecondsFormat::Millis, true)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicUsize, Ordering};

    static TEMP_COUNTER: AtomicUsize = AtomicUsize::new(0);

    /// A unique temp-store path per call, so parallel test runs never share a
    /// snapshot file.
    fn temp_store(tag: &str) -> LifecycleStore {
        let n = TEMP_COUNTER.fetch_add(1, Ordering::Relaxed);
        LifecycleStore::new(std::env::temp_dir().join(format!(
            "emberbird-lifecycle-{}-{}-{}-{}.json",
            tag,
            std::process::id(),
            n,
            chrono::Utc::now().timestamp_nanos_opt().unwrap_or_default()
        )))
    }

    fn machine_in(state: RuntimeState) -> RuntimeStateMachine {
        RuntimeStateMachine::new(state)
    }

    #[test]
    fn every_state_is_reachable_from_unknown() {
        let mut seen = vec![RuntimeState::Unknown];
        let mut queue = vec![RuntimeState::Unknown];
        while let Some(state) = queue.pop() {
            for next in state.legal_next() {
                if !seen.contains(next) {
                    seen.push(*next);
                    queue.push(*next);
                }
            }
        }
        const ALL: [RuntimeState; 14] = [
            RuntimeState::Unknown,
            RuntimeState::NotInstalled,
            RuntimeState::Checking,
            RuntimeState::Installing,
            RuntimeState::Installed,
            RuntimeState::Starting,
            RuntimeState::Running,
            RuntimeState::Stopping,
            RuntimeState::Stopped,
            RuntimeState::Degraded,
            RuntimeState::Broken,
            RuntimeState::Updating,
            RuntimeState::RollingBack,
            RuntimeState::Uninstalling,
        ];
        for state in ALL {
            assert!(seen.contains(&state), "{} is unreachable", state.as_str());
        }
        assert_eq!(seen.len(), 14);
    }

    #[test]
    fn legal_moves_are_accepted() {
        let mut machine = machine_in(RuntimeState::NotInstalled);
        let change = machine
            .transition(RuntimeState::Installing, "user requested install")
            .expect("NOT_INSTALLED -> INSTALLING is legal");
        assert_eq!(change.from, RuntimeState::NotInstalled);
        assert_eq!(change.to, RuntimeState::Installing);
        assert_eq!(machine.current(), RuntimeState::Installing);
        assert_eq!(machine.history().len(), 1);
    }

    #[test]
    fn illegal_moves_are_rejected_and_leave_no_trace() {
        let mut machine = machine_in(RuntimeState::NotInstalled);
        let error = machine
            .transition(RuntimeState::Running, "skipping every step")
            .expect_err("NOT_INSTALLED -> RUNNING must be refused");
        assert!(matches!(error, TransitionError::IllegalMove { .. }));
        assert_eq!(machine.current(), RuntimeState::NotInstalled);
        assert!(
            machine.history().is_empty(),
            "a refused move writes no history"
        );

        // STOPPED -> ROLLING_BACK is likewise outside the table.
        let mut stopped = machine_in(RuntimeState::Stopped);
        assert!(stopped
            .transition(RuntimeState::RollingBack, "no rollback from stopped")
            .is_err());
        assert_eq!(stopped.current(), RuntimeState::Stopped);
    }

    #[test]
    fn transitioning_to_the_current_state_is_refused() {
        let mut machine = machine_in(RuntimeState::Installed);
        let error = machine
            .transition(RuntimeState::Installed, "no-op")
            .expect_err("a self-transition is not a move");
        assert!(matches!(error, TransitionError::AlreadyInState(_)));
    }

    #[test]
    fn detection_states_map_onto_the_lifecycle() {
        use SubsystemState::*;
        assert_eq!(RuntimeState::from_subsystem(Unknown), RuntimeState::Unknown);
        assert_eq!(
            RuntimeState::from_subsystem(NotInstalled),
            RuntimeState::NotInstalled
        );
        // A partially installed subsystem is a fault, not a working runtime.
        assert_eq!(
            RuntimeState::from_subsystem(PartiallyInstalled),
            RuntimeState::Broken
        );
        assert_eq!(
            RuntimeState::from_subsystem(InstalledOutdated),
            RuntimeState::Installed
        );
        assert_eq!(
            RuntimeState::from_subsystem(Installed),
            RuntimeState::Installed
        );
    }

    #[test]
    fn detection_can_never_report_an_in_flight_operation() {
        use SubsystemState::*;
        for state in [
            Unknown,
            NotInstalled,
            PartiallyInstalled,
            InstalledOutdated,
            Installed,
        ] {
            let mapped = RuntimeState::from_subsystem(state);
            assert!(
                !mapped.is_busy(),
                "detection mapped {:?} onto in-flight {}",
                state,
                mapped.as_str()
            );
        }
    }

    #[test]
    fn history_records_reasons_with_non_decreasing_timestamps() {
        let mut machine = machine_in(RuntimeState::NotInstalled);
        machine
            .transition(RuntimeState::Installing, "step 1")
            .unwrap();
        machine
            .transition(RuntimeState::Installed, "step 2")
            .unwrap();
        machine
            .transition(RuntimeState::Starting, "step 3")
            .unwrap();
        let history = machine.history();
        assert_eq!(history.len(), 3);
        for pair in history.windows(2) {
            assert!(
                pair[1].at >= pair[0].at,
                "timestamps must not decrease: {} then {}",
                pair[0].at,
                pair[1].at
            );
        }
        assert!(history.iter().all(|c| !c.reason.is_empty()));
    }

    #[test]
    fn labels_and_tokens_are_stable_and_distinct() {
        const ALL: [RuntimeState; 14] = [
            RuntimeState::Unknown,
            RuntimeState::NotInstalled,
            RuntimeState::Checking,
            RuntimeState::Installing,
            RuntimeState::Installed,
            RuntimeState::Starting,
            RuntimeState::Running,
            RuntimeState::Stopping,
            RuntimeState::Stopped,
            RuntimeState::Degraded,
            RuntimeState::Broken,
            RuntimeState::Updating,
            RuntimeState::RollingBack,
            RuntimeState::Uninstalling,
        ];
        let mut labels: Vec<&str> = ALL.iter().map(|s| s.label()).collect();
        labels.sort_unstable();
        labels.dedup();
        assert_eq!(labels.len(), 14, "labels must be distinct");

        let mut tokens: Vec<&str> = ALL.iter().map(|s| s.as_str()).collect();
        tokens.sort_unstable();
        tokens.dedup();
        assert_eq!(tokens.len(), 14, "tokens must be distinct");

        assert_eq!(RuntimeState::Unknown.label(), "Unknown");
        assert_eq!(RuntimeState::NotInstalled.label(), "Not Installed");
        assert_eq!(RuntimeState::NotInstalled.as_str(), "NOT_INSTALLED");
    }

    #[test]
    fn a_snapshot_round_trips_through_json() {
        let mut machine = machine_in(RuntimeState::NotInstalled);
        machine
            .transition(RuntimeState::Installing, "round trip")
            .unwrap();
        machine
            .transition(RuntimeState::Installed, "round trip")
            .unwrap();

        let json = machine.to_json().expect("snapshot serializes");
        let parsed: PersistedLifecycle = serde_json::from_str(&json).expect("snapshot parses");
        assert_eq!(parsed.version, LIFECYCLE_SCHEMA_VERSION);
        assert_eq!(parsed.state, RuntimeState::Installed);
        assert_eq!(parsed.history.len(), 2);
        assert_eq!(parsed.history[1].reason, "round trip");
    }

    #[test]
    fn a_snapshot_survives_a_restart_through_the_store() {
        let store = temp_store("survives");
        let mut machine = machine_in(RuntimeState::NotInstalled);
        machine
            .transition(RuntimeState::Installing, "install")
            .unwrap();
        machine
            .transition(RuntimeState::Installed, "install done")
            .unwrap();
        store.save(&machine).expect("save succeeds");

        let loaded = store
            .load()
            .expect("load succeeds")
            .expect("a snapshot exists");
        assert_eq!(loaded.machine.current(), RuntimeState::Installed);
        assert_eq!(loaded.machine.history().len(), 2);
        store.clear().unwrap();
    }

    #[test]
    fn an_atomic_save_leaves_no_staged_file_behind() {
        let store = temp_store("atomic");
        store
            .save(&machine_in(RuntimeState::Installed))
            .expect("save succeeds");
        let staged = store.path().with_extension("tmp");
        assert!(!staged.exists(), "the staged file must be renamed away");
        assert!(store.path().exists());
        store.clear().unwrap();
    }

    #[test]
    fn a_corrupt_snapshot_is_an_error_not_an_unknown_state() {
        let store = temp_store("corrupt");
        std::fs::write(store.path(), "not json at all {").unwrap();
        let error = store.load().expect_err("corrupt content is an error");
        assert!(
            !matches!(error, LifecycleLoadError::Io(_)),
            "corrupt content must not be misread as absence"
        );
        store.clear().unwrap();
    }

    #[test]
    fn a_snapshot_of_the_wrong_schema_is_refused_not_guessed() {
        let store = temp_store("future");
        let body = serde_json::json!({
            "version": LIFECYCLE_SCHEMA_VERSION + 7,
            "state": "INSTALLED",
            "history": [],
        });
        std::fs::write(store.path(), body.to_string()).unwrap();
        let error = store.load().unwrap_err();
        assert!(
            matches!(error, LifecycleLoadError::Schema(_)),
            "a future schema must be refused, got {error:?}"
        );
        store.clear().unwrap();
    }

    #[test]
    fn the_store_rejects_a_schema_it_cannot_read() {
        let store = temp_store("past");
        let body = serde_json::json!({
            "version": 0,
            "state": "INSTALLED",
            "history": [],
        });
        std::fs::write(store.path(), body.to_string()).unwrap();
        let error = store.load().unwrap_err();
        assert!(matches!(error, LifecycleLoadError::Schema(_)));
        store.clear().unwrap();
    }

    #[test]
    fn a_settled_snapshot_is_restored_unchanged() {
        let snapshot = machine_in(RuntimeState::Installed).snapshot();
        let report = RuntimeStateMachine::recover(snapshot).expect("a settled state restores");
        assert_eq!(
            report.outcome,
            RecoveryOutcome::Restored {
                state: RuntimeState::Installed
            }
        );
        assert_eq!(report.machine.current(), RuntimeState::Installed);
        assert!(report.machine.history().is_empty());
    }

    #[test]
    fn recovery_keeps_the_audit_trail_and_records_itself() {
        let mut machine = machine_in(RuntimeState::NotInstalled);
        machine
            .transition(RuntimeState::Installing, "install")
            .unwrap();
        machine
            .transition(RuntimeState::Installed, "install done")
            .unwrap();
        machine
            .transition(RuntimeState::Updating, "upgrade started")
            .unwrap();
        let snapshot = machine.snapshot();

        let report = RuntimeStateMachine::recover(snapshot).expect("recovers");
        // The trail survived: three recorded moves plus the recovery itself.
        assert_eq!(report.machine.history().len(), 4);
        let last = report.machine.history().last().unwrap();
        assert_eq!(last.from, RuntimeState::Updating);
        assert_eq!(last.to, RuntimeState::Broken);
        assert!(last.reason.contains("ROLL_BACK"));
        assert!(matches!(
            report.outcome,
            RecoveryOutcome::Interrupted { .. }
        ));
    }

    #[test]
    fn a_persisted_running_state_is_not_claimed_after_a_restart() {
        let snapshot = machine_in(RuntimeState::Running).snapshot();
        let report = RuntimeStateMachine::recover(snapshot).expect("recovers");
        match report.outcome {
            RecoveryOutcome::ReEstablished {
                was,
                presumed,
                action,
            } => {
                assert_eq!(was, RuntimeState::Running);
                assert_eq!(presumed, RuntimeState::Installed);
                assert_eq!(action, RecoveryAction::Restart);
            }
            other => panic!("expected a re-established outcome, got {other:?}"),
        }
        assert_eq!(report.machine.current(), RuntimeState::Installed);
        assert!(action_is_automatic(&report));
    }

    #[test]
    fn an_interrupted_install_never_claims_a_completed_install() {
        let mut machine = machine_in(RuntimeState::NotInstalled);
        machine
            .transition(RuntimeState::Installing, "install")
            .unwrap();
        let snapshot = machine.snapshot();
        let report = RuntimeStateMachine::recover(snapshot).expect("recovers");
        assert_eq!(report.machine.current(), RuntimeState::Unknown);
        assert!(
            !matches!(
                report.outcome,
                RecoveryOutcome::Restored {
                    state: RuntimeState::Installed
                }
            ),
            "an interrupted install must never be recovered as installed"
        );
        match report.outcome {
            RecoveryOutcome::Interrupted {
                presumed, action, ..
            } => {
                assert_eq!(presumed, RuntimeState::Unknown);
                assert_eq!(action, RecoveryAction::ReDetect);
            }
            other => panic!("expected an interrupted outcome, got {other:?}"),
        }
    }

    #[test]
    fn an_interrupted_update_demands_a_rollback_it_can_perform() {
        let mut machine = machine_in(RuntimeState::Installed);
        machine
            .transition(RuntimeState::Updating, "upgrade")
            .unwrap();
        let snapshot = machine.snapshot();
        let report = RuntimeStateMachine::recover(snapshot).expect("recovers");
        assert_eq!(report.machine.current(), RuntimeState::Broken);
        // The demanded rollback must actually be a legal move from BROKEN.
        assert!(report
            .machine
            .current()
            .can_transition_to(RuntimeState::RollingBack));
    }

    #[test]
    fn an_interrupted_start_or_stop_leaves_a_restartable_runtime() {
        for persisted in [RuntimeState::Starting, RuntimeState::Stopping] {
            let snapshot = machine_in(persisted).snapshot();
            let report = RuntimeStateMachine::recover(snapshot).expect("recovers");
            assert_eq!(report.machine.current(), RuntimeState::Installed);
            assert!(
                report
                    .machine
                    .current()
                    .can_transition_to(RuntimeState::Starting),
                "{:?} must recover to a runtime that can start again",
                persisted
            );
        }
    }

    #[test]
    fn a_persisted_fault_is_rechecked_rather_than_believed() {
        let snapshot = machine_in(RuntimeState::Degraded).snapshot();
        let report = RuntimeStateMachine::recover(snapshot).expect("recovers");
        match report.outcome {
            RecoveryOutcome::ReEstablished {
                was,
                presumed,
                action,
            } => {
                assert_eq!(was, RuntimeState::Degraded);
                assert_eq!(presumed, RuntimeState::Installed);
                assert_eq!(action, RecoveryAction::ReDetect);
                assert!(action.is_automatic());
            }
            other => panic!("expected a re-established outcome, got {other:?}"),
        }
    }

    #[test]
    fn recovery_never_promotes_an_unknown_into_a_claim() {
        // UNKNOWN restores as UNKNOWN — never guessed into something stronger.
        let snapshot = machine_in(RuntimeState::Unknown).snapshot();
        let report = RuntimeStateMachine::recover(snapshot).expect("recovers");
        assert_eq!(report.machine.current(), RuntimeState::Unknown);

        // Property across every state: recovery never claims a live process or
        // an operation in flight.
        const ALL: [RuntimeState; 14] = [
            RuntimeState::Unknown,
            RuntimeState::NotInstalled,
            RuntimeState::Checking,
            RuntimeState::Installing,
            RuntimeState::Installed,
            RuntimeState::Starting,
            RuntimeState::Running,
            RuntimeState::Stopping,
            RuntimeState::Stopped,
            RuntimeState::Degraded,
            RuntimeState::Broken,
            RuntimeState::Updating,
            RuntimeState::RollingBack,
            RuntimeState::Uninstalling,
        ];
        for persisted in ALL {
            let snapshot = machine_in(persisted).snapshot();
            let report = RuntimeStateMachine::recover(snapshot).expect("recovers");
            let recovered = report.machine.current();
            assert!(
                !recovered.is_busy(),
                "recovering {:?} into in-flight {} claims an operation nobody performed",
                persisted,
                recovered.as_str()
            );
            assert_ne!(
                recovered,
                RuntimeState::Running,
                "a restart cannot prove the runtime is running"
            );
            assert_ne!(recovered, RuntimeState::Starting);
            assert_ne!(recovered, RuntimeState::Stopping);
        }
    }

    #[test]
    fn a_failed_health_check_rolls_back_into_service() {
        let mut machine = machine_in(RuntimeState::Running);
        machine
            .transition(RuntimeState::Updating, "upgrade")
            .unwrap();
        // Health check fails mid-upgrade.
        machine
            .transition(RuntimeState::RollingBack, "health check failed")
            .unwrap();
        machine
            .transition(RuntimeState::Running, "rollback restored service")
            .unwrap();
        assert_eq!(machine.current(), RuntimeState::Running);
        assert_eq!(machine.history().len(), 3);
    }

    fn action_is_automatic(report: &RecoveryReport) -> bool {
        match &report.outcome {
            RecoveryOutcome::ReEstablished { action, .. }
            | RecoveryOutcome::Interrupted { action, .. } => action.is_automatic(),
            RecoveryOutcome::Restored { .. } => true,
        }
    }

    // ------------------------------------------------------------------
    // Consumer API (IPC reconciliation) tests.
    // ------------------------------------------------------------------

    #[test]
    fn a_fresh_process_reports_detection_without_a_snapshot() {
        let store = temp_store("fresh");
        let report = lifecycle_report_with_store(&store);
        match &report.outcome {
            ReconciliationOutcome::Fresh { state } => {
                assert_eq!(
                    report.state, *state,
                    "report state must come from the outcome"
                );
            }
            other => panic!("expected a fresh outcome, got {other:?}"),
        }
        assert!(!report.busy, "detection verdicts are never in-flight");
        assert!(report.history_tail.is_empty(), "no snapshot means no trail");
        // The reconciled verdict is persisted for the next start.
        assert!(
            store.path().exists(),
            "the reconciled trail must be persisted"
        );
        store.clear().unwrap();
    }

    #[test]
    fn a_recovered_snapshot_is_refined_by_detection_and_re_persisted() {
        let store = temp_store("recovered");
        // Seed a snapshot whose persisted state is settled, so recovery
        // restores it exactly and detection then refines it.
        let mut machine = machine_in(RuntimeState::NotInstalled);
        machine
            .transition(RuntimeState::Installing, "install")
            .unwrap();
        machine
            .transition(RuntimeState::Installed, "install done")
            .unwrap();
        store.save(&machine).unwrap();

        let report = lifecycle_report_with_store(&store);
        match &report.outcome {
            ReconciliationOutcome::Recovered {
                recovered,
                state,
                action,
            } => {
                assert_eq!(
                    *recovered,
                    RuntimeState::Installed,
                    "INSTALLED restores exactly"
                );
                assert_eq!(*state, report.state, "outcome state must match the report");
                assert_eq!(action, "RE_STORED");
            }
            other => panic!("expected a recovered outcome, got {other:?}"),
        }
        // The audit trail survived the round trip and grew with the
        // reconciliation hops, then was persisted back.
        assert!(!report.history_tail.is_empty());
        assert!(store.path().exists());
        store.clear().unwrap();
    }

    #[test]
    fn detection_wins_over_a_stale_baseline() {
        let store = temp_store("stale");
        // Persist a trail that ends INSTALLED; if the host now reports
        // anything else, the report must reflect the host, not the trail.
        let mut machine = machine_in(RuntimeState::NotInstalled);
        machine
            .transition(RuntimeState::Installing, "install")
            .unwrap();
        machine
            .transition(RuntimeState::Installed, "install done")
            .unwrap();
        store.save(&machine).unwrap();

        let report = lifecycle_report_with_store(&store);
        let detected = RuntimeState::from_subsystem(detect_subsystem().state);
        assert_eq!(
            report.state, detected,
            "the host is evidence about now; the trail is evidence about the past"
        );
        store.clear().unwrap();
    }

    #[test]
    fn the_reconciled_state_is_always_settled() {
        // No matter what the store contained, the report's state is one
        // detection could legitimately produce — never in-flight.
        let store = temp_store("settled");
        let body = serde_json::json!({
            "version": LIFECYCLE_SCHEMA_VERSION,
            "state": "RUNNING",
            "history": [],
        });
        std::fs::write(store.path(), body.to_string()).unwrap();

        let report = lifecycle_report_with_store(&store);
        assert!(
            !report.busy,
            "reconciliation must never present an in-flight state"
        );
        assert!(report.legal_next.contains(&RuntimeState::Checking));
        store.clear().unwrap();
    }

    #[test]
    fn an_unreadable_snapshot_is_refused_and_preserved_for_forensics() {
        let store = temp_store("forensics");
        std::fs::write(store.path(), "{ this is not json").unwrap();

        let report = lifecycle_report_with_store(&store);
        match &report.outcome {
            ReconciliationOutcome::Unreadable { reason } => {
                assert!(
                    reason.contains("malformed"),
                    "the refusal must name the cause, got: {reason}"
                );
            }
            other => panic!("expected an unreadable outcome, got {other:?}"),
        }
        // The corrupt file is NOT silently overwritten with a healthy snapshot.
        let raw = std::fs::read_to_string(store.path()).unwrap();
        assert!(
            raw.contains("not json"),
            "corrupt evidence must be preserved, not clobbered"
        );
        store.clear().unwrap();
    }

    #[test]
    fn a_future_schema_snapshot_is_also_preserved_not_clobbered() {
        let store = temp_store("future-preserve");
        let body = serde_json::json!({
            "version": LIFECYCLE_SCHEMA_VERSION + 7,
            "state": "INSTALLED",
            "history": [],
        });
        std::fs::write(store.path(), body.to_string()).unwrap();

        let report = lifecycle_report_with_store(&store);
        assert!(matches!(
            report.outcome,
            ReconciliationOutcome::Unreadable { .. }
        ));
        let raw = std::fs::read_to_string(store.path()).unwrap();
        assert!(
            raw.contains("INSTALLED"),
            "future-schema evidence must be preserved"
        );
        store.clear().unwrap();
    }

    #[test]
    fn the_report_state_is_consistent_with_its_own_fields() {
        let store = temp_store("consistent");
        let report = lifecycle_report_with_store(&store);
        assert_eq!(report.state.is_busy(), report.busy);
        let expected: Vec<RuntimeState> = report.state.legal_next().to_vec();
        assert_eq!(report.legal_next, expected);
        store.clear().unwrap();
    }
}
