import React from 'react';
import type { LifecycleReport } from '../lib/types';

/**
 * UI labels for the 14 lifecycle states — mirrors `RuntimeState::label()` in
 * runtime_state.rs. Surface wording must not drift per view, so this is the
 * single render map on the frontend.
 */
const STATE_LABELS: Record<LifecycleReport['state'], string> = {
  UNKNOWN: 'Unknown',
  NOT_INSTALLED: 'Not Installed',
  CHECKING: 'Checking',
  INSTALLING: 'Installing',
  INSTALLED: 'Installed',
  STARTING: 'Starting',
  RUNNING: 'Running',
  STOPPING: 'Stopping',
  STOPPED: 'Stopped',
  DEGRADED: 'Degraded',
  BROKEN: 'Broken',
  UPDATING: 'Updating',
  ROLLING_BACK: 'Rolling Back',
  UNINSTALLING: 'Uninstalling',
};

/**
 * Colour by lifecycle *class*, not per state: settled-healthy, in-flight,
 * faulted, or unknowable. The engine's `busy` flag decides busy-ness —
 * a surface must not re-derive what the backend already declared.
 */
function presentation(state: LifecycleReport['state'], busy: boolean): { dot: string; badge: string } {
  if (busy) return { dot: 'bg-amber-400', badge: 'bg-amber-500/10 text-amber-400 border-amber-500/30' };
  switch (state) {
    case 'RUNNING':
    case 'INSTALLED':
    case 'STOPPED':
      return { dot: 'bg-emerald-400', badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' };
    case 'DEGRADED':
    case 'BROKEN':
      return { dot: 'bg-rose-500', badge: 'bg-rose-500/10 text-rose-400 border-rose-500/30' };
    case 'UNKNOWN':
    case 'NOT_INSTALLED':
      return { dot: 'bg-ember-ash/50', badge: 'bg-ember-charcoal text-ember-ash border-ember-ash/30' };
    default:
      return { dot: 'bg-amber-400', badge: 'bg-amber-500/10 text-amber-400 border-amber-500/30' };
  }
}

/** How the reconciliation is explained to the user, honestly. */
function outcomeNote(report: LifecycleReport): string | null {
  switch (report.outcome.kind) {
    case 'RECOVERED': {
      const recovered = STATE_LABELS[report.outcome.recovered];
      if (report.outcome.action === 'ROLL_BACK') {
        return `Recovered from an interrupted change — a rollback is required before trust.`;
      }
      if (report.outcome.action === 'RESTART') {
        return `Recovered from a restart: the previous session recorded ${recovered}; start the runtime to confirm it runs.`;
      }
      return `Recovered from a restart; the previous record (${recovered}) was re-checked against the machine.`;
    }
    case 'UNREADABLE':
      return `The saved lifecycle record could not be read (${report.outcome.reason}); it was preserved untouched and reality was re-checked instead.`;
    default:
      return null;
  }
}

interface LifecycleBadgeProps {
  report: LifecycleReport | null;
}

/**
 * The runtime lifecycle surface (PH-08 consumer for the PH-02 engine).
 *
 * Renders ONLY what the report declares: the state label, the backend's own
 * busy verdict, and the reconciliation note when there is one. No state is
 * invented while the report loads — the placeholder says "checking", which is
 * the truth. A refused/absent report is rendered as an error, never silently
 * as a healthy state (Zero-Mock law).
 */
export const LifecycleBadge: React.FC<LifecycleBadgeProps> = ({ report }) => {
  if (!report) {
    return (
      <span
        data-testid="lifecycle-badge"
        className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium bg-ember-charcoal text-ember-ash border border-ember-ash/30"
      >
        <span className="w-2 h-2 rounded-full bg-ember-ash/50 animate-pulse" />
        Checking lifecycle…
      </span>
    );
  }

  const { dot, badge } = presentation(report.state, report.busy);
  const note = outcomeNote(report);

  return (
    <span
      data-testid="lifecycle-badge"
      className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium border ${badge}`}
      title={report.history_tail.length > 0 ? `Last move: ${report.history_tail[report.history_tail.length - 1].reason}` : undefined}
    >
      <span className={`w-2 h-2 rounded-full ${dot}`} />
      {STATE_LABELS[report.state]}
      {note && <span className="sr-only"> — {note}</span>}
    </span>
  );
};
