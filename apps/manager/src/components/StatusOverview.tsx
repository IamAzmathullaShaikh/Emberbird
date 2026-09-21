import React from 'react';
import { projectSubsystemStatus } from '../lib/state';
import type { WsaStatus } from '../lib/types';

interface StatusOverviewProps {
  status: WsaStatus;
}

/**
 * Subsystem state header, environment facts, and on-disk paths.
 *
 * Every install-state word/colour comes from `projectSubsystemStatus` — this
 * component never branches on raw detection signals (single source of truth).
 */
export const StatusOverview: React.FC<StatusOverviewProps> = ({ status }) => {
  const { presentation, versionLabel } = projectSubsystemStatus(status);

  return (
    <>
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
          Subsystem Status &amp; Environment
        </h2>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${presentation.dotClass}`} />
          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${presentation.badgeClass}`}>
            {presentation.label}
          </span>
          <span className="text-xs font-mono text-accent">
            {versionLabel !== '—' ? versionLabel : ''}
          </span>
        </div>
      </div>

      <div className={`p-3 rounded-xl text-xs ${presentation.badgeClass} bg-opacity-40`}>
        {presentation.guidance}
        {status.state_evidence.length > 0 && (
          <ul className="mt-1.5 space-y-0.5 text-[11px] opacity-80">
            {status.state_evidence.map((e, i) => (
              <li key={i}>• {e}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <div className="p-3.5 rounded-xl bg-surface-raised/60 border border-border-DEFAULT/80">
          <div className="text-text-muted font-medium">Virtualization (Hyper-V / BIOS)</div>
          <div className="mt-1 font-semibold text-sm flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${status.virtualization_enabled ? 'bg-emerald-400' : 'bg-rose-500'}`}></span>
            <span className={status.virtualization_enabled ? 'text-white' : 'text-rose-400'}>
              {status.virtualization_enabled ? 'Enabled' : 'Disabled (Requires BIOS/DISM)'}
            </span>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-surface-raised/60 border border-border-DEFAULT/80">
          <div className="text-text-muted font-medium">Developer Mode Policy</div>
          <div className="mt-1 font-semibold text-sm flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${status.developer_mode_enabled ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
            <span className={status.developer_mode_enabled ? 'text-white' : 'text-amber-400'}>
              {status.developer_mode_enabled ? 'Unlocked (Loose Registration OK)' : 'Locked'}
            </span>
          </div>
        </div>
      </div>

      {status.install_path && (
        <div className="p-3 rounded-xl bg-surface-raised/40 border border-border-DEFAULT/60 text-xs">
          <span className="text-text-muted block mb-0.5">Package Install Path:</span>
          <code className="text-text-secondary font-mono text-[11px] select-all break-all">{status.install_path}</code>
        </div>
      )}

      {status.vhdx_path && (
        <div className="p-3 rounded-xl bg-surface-raised/40 border border-border-DEFAULT/60 text-xs">
          <span className="text-text-muted block mb-0.5">
            Userdata VHDX Storage{status.state === 'NOT_INSTALLED' ? ' (orphaned data — no subsystem)' : ''}:
          </span>
          <code className="text-text-secondary font-mono text-[11px] select-all break-all">{status.vhdx_path}</code>
        </div>
      )}
    </>
  );
};
