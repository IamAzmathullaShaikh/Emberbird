import React from 'react';
import type { WsaStatus } from '../lib/types';

interface SubsystemControlsProps {
  status: WsaStatus;
  busy: boolean;
  feedback: string | null;
  onLaunch: (target?: string) => void;
  onShutdown: () => void;
}

/**
 * Quick Launch & Control Panel — surfaced only when a usable subsystem
 * registration exists. Returns `null` (not a disabled shell) otherwise, so the
 * UI never advertises controls for a subsystem that is not there.
 */
export const SubsystemControls: React.FC<SubsystemControlsProps> = ({
  status,
  busy,
  feedback,
  onLaunch,
  onShutdown,
}) => {
  if (status.state === 'NOT_INSTALLED' || status.state === 'UNKNOWN') return null;

  return (
    <div className="mt-4 pt-4 border-t border-border-DEFAULT/80 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-text-secondary">Subsystem Controls</span>
        {feedback && <span className="text-[11px] text-accent">{feedback}</span>}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => onLaunch('wsa://settings')}
          disabled={busy}
          className="px-3 py-1.5 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-xs font-semibold shadow transition-all flex items-center gap-1.5"
        >
          <span>⚙️</span> Open Settings
        </button>
        <button
          type="button"
          onClick={() => onLaunch('wsa://com.android.vending')}
          disabled={busy}
          className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold shadow transition-all flex items-center gap-1.5"
        >
          <span>🛍️</span> Open Play Store
        </button>
        <button
          type="button"
          onClick={onShutdown}
          disabled={busy}
          className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-raised disabled:opacity-50 text-text-secondary text-xs font-medium border border-border-DEFAULT transition-all flex items-center gap-1.5"
        >
          <span>⏹️</span> Shut Down WSA
        </button>
      </div>
    </div>
  );
};
