import React from 'react';
import type { WsaStatus } from '../lib/types';

interface StatusCardProps {
  status: WsaStatus | null;
}

export const StatusCard: React.FC<StatusCardProps> = ({ status }) => {
  if (!status) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse">
        <div className="h-4 bg-slate-800 rounded w-1/4 mb-4"></div>
        <div className="h-3 bg-slate-800/60 rounded w-3/4"></div>
      </div>
    );
  }

  return (
    <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Subsystem Status & Environment
        </h2>
        <span className="text-xs font-mono text-indigo-400">
          {status.installed ? (status.package_version || 'Detected') : 'No Subsystem'}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
          <div className="text-slate-500 font-medium">Virtualization (Hyper-V / BIOS)</div>
          <div className="mt-1 font-semibold text-sm flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${status.virtualization_enabled ? 'bg-emerald-400' : 'bg-rose-500'}`}></span>
            <span className={status.virtualization_enabled ? 'text-white' : 'text-rose-400'}>
              {status.virtualization_enabled ? 'Enabled' : 'Disabled (Requires BIOS/DISM)'}
            </span>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
          <div className="text-slate-500 font-medium">Developer Mode Policy</div>
          <div className="mt-1 font-semibold text-sm flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${status.developer_mode_enabled ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
            <span className={status.developer_mode_enabled ? 'text-white' : 'text-amber-400'}>
              {status.developer_mode_enabled ? 'Unlocked (Loose Registration OK)' : 'Locked'}
            </span>
          </div>
        </div>
      </div>

      {status.install_path && (
        <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/60 text-xs">
          <span className="text-slate-500 block mb-0.5">Package Install Path:</span>
          <code className="text-slate-300 font-mono text-[11px] select-all break-all">{status.install_path}</code>
        </div>
      )}

      {status.vhdx_path && (
        <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/60 text-xs">
          <span className="text-slate-500 block mb-0.5">Userdata VHDX Storage:</span>
          <code className="text-slate-300 font-mono text-[11px] select-all break-all">{status.vhdx_path}</code>
        </div>
      )}
    </div>
  );
};
