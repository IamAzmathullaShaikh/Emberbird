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
    { id: 'doctor', label: 'Doctor' },
    { id: 'licenses', label: 'Licenses' },
  ];

  return (
    <header className="border-b border-ember-ash/20 bg-ember-obsidian/80 backdrop-blur-md px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-3 sm:py-0 sm:h-16">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-ember-glow flex items-center justify-center font-bold text-ember-obsidian shadow-lg shadow-ember-glow/30">
            E
          </div>
          <div className="flex flex-col">
            <h1 className="text-sm font-bold text-white leading-tight tracking-tight">
              Emberbird <span className="text-ember-glow">Engine</span>
            </h1>
            <span className="text-[10px] text-ember-ash font-mono uppercase tracking-widest">
              Lifecycle Manager v0.2.2
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1 bg-ember-charcoal/50 p-1 rounded-xl border border-ember-ash/20">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => onSelectTab(tab.id)}
                className={`px-3 py-1 text-xs font-medium rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-ember-glow text-ember-obsidian shadow-sm' 
                    : 'text-ember-ash hover:text-white hover:bg-ember-ash/20'
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
          const hostArch =
            typeof navigator !== 'undefined' &&
            (navigator.userAgent.toLowerCase().includes('arm64') ||
              navigator.userAgent.toLowerCase().includes('aarch64'))
              ? 'arm64'
              : 'x64';
          return (
            <div className="flex items-center gap-2 text-xs">
              <span className={`px-2.5 py-1 rounded-full font-medium ${presentation.badgeClass}`}>
                {presentation.label}
              </span>

              <span className="px-2.5 py-1 rounded-full border font-mono font-medium bg-ember-charcoal text-ember-ash border-ember-ash/30">
                {hostArch === 'arm64' ? 'ARM64' : 'x64'}
              </span>

              {projected.runningLabel && (
                <span
                  className={`px-2.5 py-1 rounded-full border font-medium ${
                    status!.is_running
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : 'bg-ember-charcoal text-ember-ash border-ember-ash/30'
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
          className="px-3 py-1.5 rounded-lg bg-ember-charcoal hover:bg-ember-ash/40 border border-ember-ash/30 text-xs text-white transition-colors disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
    </header>
  );
};