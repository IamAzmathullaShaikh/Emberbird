import React from 'react';
import type { WsaStatus } from '../lib/types';

interface HeaderProps {
  status: WsaStatus | null;
  onRefresh: () => void;
  loading: boolean;
}

export const Header: React.FC<HeaderProps> = ({ status, onRefresh, loading }) => {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
          W
        </div>
        <div>
          <h1 className="text-sm font-bold text-white leading-tight">WSABuilds Manager</h1>
          <span className="text-[11px] text-slate-400 font-mono">v0.1.0 (Core Engine)</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {status && (
          <div className="flex items-center gap-2 text-xs">
            {status.installed ? (
              <span className={`px-2.5 py-1 rounded-full border font-medium ${
                status.is_running
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-slate-800 text-slate-300 border-slate-700'
              }`}>
                {status.is_running ? 'Running' : 'Stopped'}
              </span>
            ) : (
              <span className="px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 font-medium">
                Not Installed
              </span>
            )}

            <span className={`px-2.5 py-1 rounded-full border font-medium ${
              status.developer_mode_enabled
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }`}>
              DevMode: {status.developer_mode_enabled ? 'ON' : 'OFF'}
            </span>
          </div>
        )}

        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-200 transition-colors disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
    </header>
  );
};
