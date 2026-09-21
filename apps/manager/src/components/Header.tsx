import React, { useEffect, useState, useRef } from 'react';
import { getVersion } from '@tauri-apps/api/app';
import { getHostArch } from '../lib/ipc';
import { projectSubsystemStatus } from '../lib/state';
import { useEmberStore } from '../lib/store';
import type { WsaStatus, NavigationTab } from '../lib/types';

const TABS: { id: NavigationTab; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'updates',   label: 'Updates' },
  { id: 'backups',   label: 'Backups' },
  { id: 'restore',   label: 'Restore' },
  { id: 'doctor',    label: 'Doctor' },
  { id: 'licenses',  label: 'Licenses' },
];

interface StatusBadgesProps {
  status: WsaStatus | null;
  hostArch: string;
}

const StatusBadges: React.FC<StatusBadgesProps> = ({ status, hostArch }) => {
  const projected = projectSubsystemStatus(status);
  const { presentation } = projected;
  const isArm64 = hostArch === 'aarch64' || hostArch === 'arm64';
  const isRunning = status?.is_running ?? false;
  const devMode = status?.developer_mode_enabled ?? false;

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className={`px-2.5 py-1 rounded-full font-medium ${presentation.badgeClass}`}>
        {presentation.label}
      </span>
      <span className="px-2.5 py-1 rounded-full border font-mono font-medium bg-ember-charcoal text-ember-ash border-ember-ash/30">
        {isArm64 ? 'ARM64 (Snapdragon Native)' : 'x64 Native'}
      </span>
      {projected.runningLabel && (
        <span
          className={`px-2.5 py-1 rounded-full border font-medium ${
            isRunning
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-ember-charcoal text-ember-ash border-ember-ash/30'
          }`}
        >
          {projected.runningLabel}
        </span>
      )}
      <span
        className={`px-2.5 py-1 rounded-full border font-medium ${
          devMode
            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
        }`}
      >
        DevMode: {devMode ? 'ON' : 'OFF'}
      </span>
    </div>
  );
};

export const Header: React.FC = () => {
  const wsaStatus = useEmberStore((s) => s.wsaStatus);
  const loadingStatus = useEmberStore((s) => s.loadingStatus);
  const refreshStatus = useEmberStore((s) => s.refreshStatus);
  const activeTab = useEmberStore((s) => s.activeTab);
  const setActiveTab = useEmberStore((s) => s.setActiveTab);

  const [managerVersion, setManagerVersion] = useState<string | null>(null);
  const [hostArch, setHostArch] = useState<string>('x86_64');
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getVersion()
      .then(setManagerVersion)
      .catch(() => setManagerVersion(null));
  }, []);

  useEffect(() => {
    getHostArch()
      .then(setHostArch)
      .catch(() => setHostArch('x86_64')); // fallback to x64 if probe fails
  }, []);

  // Close the mobile menu when clicking outside
  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [menuOpen]);

  return (
    <header className="border-b border-ember-ash/20 bg-ember-obsidian/80 backdrop-blur-md px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-3 sm:py-0 sm:h-16 relative">
      <div className="flex items-center gap-4">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-ember-glow flex items-center justify-center font-bold text-ember-obsidian shadow-lg shadow-ember-glow/30">
            E
          </div>
          <div className="flex flex-col">
            <h1 className="text-sm font-bold text-white leading-tight tracking-tight">
              Emberbird <span className="text-ember-glow">Engine</span>
            </h1>
            <span className="text-[10px] text-ember-ash font-mono uppercase tracking-widest">
              Lifecycle Manager{managerVersion ? ` v${managerVersion}` : ''}
            </span>
          </div>
        </div>

        {/* Desktop nav — hidden below md */}
        <nav className="hidden md:flex items-center gap-1 bg-ember-charcoal/50 p-1 rounded-xl border border-ember-ash/20">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              onClick={() => { setActiveTab(tab.id); setMenuOpen(false); }}
              className={`px-3 py-1 text-xs font-medium rounded-lg transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-ember-glow text-ember-obsidian shadow-sm'
                  : 'text-ember-ash hover:text-white hover:bg-ember-ash/20'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex items-center gap-3">
        <StatusBadges status={wsaStatus} hostArch={hostArch} />

        <button
          type="button"
          onClick={() => refreshStatus()}
          disabled={loadingStatus}
          className="px-3 py-1.5 rounded-lg bg-ember-charcoal hover:bg-ember-ash/40 border border-ember-ash/30 text-xs text-white transition-colors disabled:opacity-50"
        >
          {loadingStatus ? 'Refreshing...' : 'Refresh'}
        </button>

        {/* Hamburger — visible below md only */}
        <button
          type="button"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="Navigation menu"
          aria-expanded={menuOpen}
          className="md:hidden flex flex-col gap-1 p-2 rounded-lg bg-ember-charcoal border border-ember-ash/30"
        >
          <span className="w-4 h-0.5 bg-ember-ash block" />
          <span className="w-4 h-0.5 bg-ember-ash block" />
          <span className="w-4 h-0.5 bg-ember-ash block" />
        </button>
      </div>

      {/* Mobile dropdown menu */}
      {menuOpen && (
        <div
          ref={menuRef}
          className="md:hidden absolute top-full right-0 mt-1 mr-2 z-50 bg-ember-charcoal border border-ember-ash/30 rounded-xl shadow-xl p-2 flex flex-col gap-1 min-w-[140px]"
        >
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => { setActiveTab(tab.id); setMenuOpen(false); }}
              className={`px-3 py-2 text-xs font-medium rounded-lg text-left transition-all ${
                activeTab === tab.id
                  ? 'bg-ember-glow text-ember-obsidian'
                  : 'text-ember-ash hover:text-white hover:bg-ember-ash/20'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}
    </header>
  );
};