import React from 'react';
import type { UpdateStatus } from '../lib/types';

interface ReleaseCardProps {
  updateStatus: UpdateStatus | null;
  onCheckUpdates: () => void;
  checking: boolean;
}

export const ReleaseCard: React.FC<ReleaseCardProps> = ({ updateStatus, onCheckUpdates, checking }) => {
  return (
    <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Release Intelligence & Updates
        </h2>
        <button
          type="button"
          onClick={onCheckUpdates}
          disabled={checking}
          className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors disabled:opacity-50"
        >
          {checking ? 'Checking GitHub...' : 'Check Now'}
        </button>
      </div>

      {updateStatus ? (
        <div className="space-y-3 text-xs">
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <div>
              <div className="text-slate-500">Current Installed WSA</div>
              <div className="font-mono text-sm font-bold text-white mt-0.5">
                {updateStatus.current_version || 'Not Installed'}
              </div>
            </div>
            <div className="text-right">
              <div className="text-slate-500">Latest Available Release</div>
              <div className="font-mono text-sm font-bold text-indigo-400 mt-0.5">
                {updateStatus.latest_version || 'Querying...'}
              </div>
            </div>
          </div>

          {updateStatus.update_available ? (
            <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-between">
              <div>
                <span className="font-bold text-indigo-300 block">New WSA Release Available!</span>
                <span className="text-[11px] text-slate-400">Upgrade pipeline will be activated in Sprint 7.</span>
              </div>
              <span className="px-3 py-1 rounded-lg bg-indigo-600 text-white font-medium text-xs">
                Update Ready
              </span>
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/60 text-slate-400 text-center">
              Your WSA installation matches the latest verified release tag.
            </div>
          )}
        </div>
      ) : (
        <div className="py-6 text-center text-xs text-slate-500">
          Loading release metadata from GitHub repository...
        </div>
      )}
    </div>
  );
};
