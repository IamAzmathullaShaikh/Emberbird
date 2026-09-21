/**
 * UI presentation rules for the authoritative subsystem state.
 *
 * Rule: dashboard components MUST NOT branch on `WsaStatus.installed` or any
 * other raw detection signal. All install-state wording, colors, and icons
 * derive from `state` via this module so contradictory states are impossible
 * by construction (single source of truth).
 */
import type { SubsystemState, WsaStatus } from './types';

export interface SubsystemStatePresentation {
  /** Exact display label — components render this verbatim. */
  label: string;
  /** Tailwind classes for the badge container. */
  badgeClass: string;
  /** Tailwind classes for the status dot. */
  dotClass: string;
  /** Whether a usable subsystem exists (drives CTA enablement). */
  usable: boolean;
  /** Whether the UI may display a version string as fact. */
  mayShowVersion: boolean;
  /** Short guidance line shown under the state badge. */
  guidance: string;
}

const PRESENTATIONS: Record<SubsystemState, SubsystemStatePresentation> = {
  NOT_INSTALLED: {
    label: 'Not Installed',
    badgeClass: 'bg-surface-raised text-text-secondary border border-border-DEFAULT',
    dotClass: 'bg-text-muted',
    usable: false,
    mayShowVersion: false,
    guidance: 'Deploy a Emberbird edition to begin.',
  },
  PARTIALLY_INSTALLED: {
    label: 'Partially Installed',
    badgeClass: 'bg-amber-500/10 text-amber-400 border border-amber-500/30',
    dotClass: 'bg-amber-400',
    usable: false,
    mayShowVersion: true,
    guidance: 'The package is registered but components are missing. Re-deploy or repair.',
  },
  INSTALLED_OUTDATED: {
    label: 'Installed (Outdated)',
    badgeClass: 'bg-status-warn/10 text-status-warn border border-status-warn/30',
    dotClass: 'bg-status-warn',
    usable: true,
    mayShowVersion: true,
    guidance: 'A newer supported baseline is available. Check the Updates tab.',
  },
  INSTALLED: {
    label: 'Installed',
    badgeClass: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30',
    dotClass: 'bg-emerald-400',
    usable: true,
    mayShowVersion: true,
    guidance: 'Subsystem is ready.',
  },
  UNKNOWN: {
    label: 'Unknown',
    badgeClass: 'bg-surface-raised text-text-muted border border-border-DEFAULT',
    dotClass: 'bg-text-muted',
    usable: false,
    mayShowVersion: false,
    guidance: 'Detection failed. Refresh to retry.',
  },
};

/** Get the presentation for a state. Falls back to UNKNOWN presentation. */
export function getSubsystemStatePresentation(state: SubsystemState): SubsystemStatePresentation {
  return PRESENTATIONS[state] ?? PRESENTATIONS.UNKNOWN;
}

/**
 * The one approved projection of status for UI rendering. Consumers call this
 * instead of reading fields directly, guaranteeing:
 *  - the label comes from `state` only;
 *  - a version is shown iff the state says a version is known;
 *  - an orphaned VHDX path is labeled as data, never as an installation.
 */
export function projectSubsystemStatus(status: WsaStatus | null): {
  presentation: SubsystemStatePresentation;
  versionLabel: string;
  vhdxLabel: string;
  runningLabel: string | null;
} {
  if (!status) {
    return {
      presentation: getSubsystemStatePresentation('UNKNOWN'),
      versionLabel: '—',
      vhdxLabel: '—',
      runningLabel: null,
    };
  }
  const presentation = getSubsystemStatePresentation(status.state);
  const versionKnown = presentation.mayShowVersion && !!status.package_version;
  return {
    presentation,
    versionLabel: versionKnown ? status.package_version! : '—',
    vhdxLabel: status.vhdx_path
      ? status.state === 'NOT_INSTALLED'
        ? `${status.vhdx_path} (orphaned data)`
        : status.vhdx_path
      : '—',
    runningLabel:
      status.state === 'INSTALLED' || status.state === 'INSTALLED_OUTDATED'
        ? status.is_running
          ? 'Running'
          : 'Stopped'
        : null,
  };
}

/** Resolve the state for mock/browser payloads that predate the state field. */
export function normalizeStatusPayload(status: Partial<WsaStatus> | null): WsaStatus | null {
  if (!status || typeof status !== 'object') return null;
  if (status.state) {
    return status as WsaStatus;
  }
  // Legacy mock payloads: derive the closest state from the signals present.
  const installed = status.installed === true;
  return {
    installed,
    package_version: status.package_version ?? null,
    developer_mode_enabled: status.developer_mode_enabled ?? false,
    virtualization_enabled: status.virtualization_enabled ?? false,
    is_running: status.is_running ?? false,
    install_path: status.install_path ?? null,
    vhdx_path: status.vhdx_path ?? null,
    state: installed ? 'INSTALLED' : 'NOT_INSTALLED',
    state_evidence: ['Derived client-side from legacy payload (no backend state field).'],
  };
}
