import React from 'react';
import { projectSubsystemStatus } from '../lib/state';
import type { WsaStatus, NavigationTab } from '../lib/types';

interface HeaderProps {
  status: WsaStatus | null;
  onRefresh: () => void;
  loading: boolean;
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  onRefresh,
  loading,
  activeTab,
  onSelectTab,
}) => {
  const tabs: { id: NavigationTab; label: string }[] = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'updates', label: 'Updates' },
    { id: 'backups', label: 'Backups' },
    { id: 'restore', label: 'Restore' },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-3 sm:py-0 sm:h-16">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
            W
          </div>
          <div>
            <h1 className="text-sm font-bold text-white leading-tight">
              WSABuilds Manager
            </h1>
            <span className="text-[11px] text-slate-400 font-mono">
              v0.2.0 (Lifecycle Engine)
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-950/50 p-1 rounded-lg border border-slate-800/80">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => onSelectTab(tab.id)}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center gap-3">
        {(() => {
          const projected = projectSubsystemStatus(status);
          const { presentation } = projected;
          return (
            <div className="flex items-center gap-2 text-xs">
              <span className={`px-2.5 py-1 rounded-full font-medium ${presentation.badgeClass}`}>
                {presentation.label}
              </span>

              {projected.runningLabel && (
                <span
                  className={`px-2.5 py-1 rounded-full border font-medium ${
                    status!.is_running
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : 'bg-slate-800 text-slate-300 border-slate-700'
                  }`}
                >
                  {projected.runningLabel}
                </span>
              )}

              <span
                className={`px-2.5 py-1 rounded-full border font-medium ${
                  status!.developer_mode_enabled
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                }`}
              >
                DevMode: {status!.developer_mode_enabled ? 'ON' : 'OFF'}
              </span>
            </div>
          );
        })()}

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
