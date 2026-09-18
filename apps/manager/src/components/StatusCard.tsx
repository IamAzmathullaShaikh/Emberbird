import React, { useState } from 'react';
import { projectSubsystemStatus } from '../lib/state';
import { installWsaPackage } from '../lib/ipc';
import type { WsaStatus, InstallResult } from '../lib/types';

interface StatusCardProps {
  status: WsaStatus | null;
  onRefresh?: () => void;
}

export const StatusCard: React.FC<StatusCardProps> = ({ status, onRefresh }) => {
  const [selectedEdition, setSelectedEdition] = useState<'standard' | 'banking'>('standard');
  const [packagePath, setPackagePath] = useState('C:\\WSABuilds\\WSA_2407.40000.4.0_x64_Release-Magisk');
  const [isInstalling, setIsInstalling] = useState(false);
  const [installResult, setInstallResult] = useState<InstallResult | null>(null);
  const [installError, setInstallError] = useState<string | null>(null);

  if (!status) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse">
        <div className="h-4 bg-slate-800 rounded w-1/4 mb-4"></div>
        <div className="h-3 bg-slate-800/60 rounded w-3/4"></div>
      </div>
    );
  }

  const projected = projectSubsystemStatus(status);
  const { presentation } = projected;

  const handleSelectEdition = (edition: 'standard' | 'banking') => {
    setSelectedEdition(edition);
    if (edition === 'standard') {
      setPackagePath('C:\\WSABuilds\\WSA_2407.40000.4.0_x64_Release-Magisk');
    } else {
      setPackagePath('C:\\WSABuilds\\WSA_2407.40000.4.0_x64_Release-Vanilla');
    }
  };

  const handleQuickInstall = async () => {
    if (!packagePath.trim()) {
      setInstallError('Please specify the path to your extracted WSA package directory or AppxManifest.xml.');
      return;
    }

    setIsInstalling(true);
    setInstallError(null);
    setInstallResult(null);

    try {
      const res = await installWsaPackage(packagePath.trim());
      setInstallResult(res);
      if (res.success && onRefresh) {
        onRefresh();
      }
    } catch (err) {
      setInstallError(`Installation error: ${String(err)}`);
    } finally {
      setIsInstalling(false);
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Subsystem Status & Environment
        </h2>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${presentation.dotClass}`} />
          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${presentation.badgeClass}`}>
            {presentation.label}
          </span>
          <span className="text-xs font-mono text-indigo-400">
            {projected.versionLabel !== '—' ? projected.versionLabel : ''}
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
          <span className="text-slate-500 block mb-0.5">Userdata VHDX Storage{status.state === 'NOT_INSTALLED' ? ' (orphaned data — no subsystem)' : ''}:</span>
          <code className="text-slate-300 font-mono text-[11px] select-all break-all">{status.vhdx_path}</code>
        </div>
      )}

      {/* 1-Click Quick Install & Setup Wizard (Surfaced when Subsystem is NOT_INSTALLED) */}
      {status.state === 'NOT_INSTALLED' && (
        <div className="mt-6 pt-5 border-t border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping"></span>
                Quick Setup &amp; One-Click Installer
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Register Windows Subsystem for Android directly onto this machine with verified prerequisites.
              </p>
            </div>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Observatory Recommended
            </span>
          </div>

          {/* Edition Selection Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => handleSelectEdition('standard')}
              className={`p-3.5 rounded-xl text-left transition-all border ${
                selectedEdition === 'standard'
                  ? 'bg-indigo-950/30 border-indigo-500 text-white shadow-lg shadow-indigo-500/10'
                  : 'bg-slate-950/40 border-slate-800/80 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-xs text-indigo-300">Standard Edition</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                  Recommended
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                Pre-rooted with Magisk 27.0 + MindTheGapps + Google Play Store. Ideal for productivity, power users, and modding.
              </p>
            </button>

            <button
              type="button"
              onClick={() => handleSelectEdition('banking')}
              className={`p-3.5 rounded-xl text-left transition-all border ${
                selectedEdition === 'banking'
                  ? 'bg-emerald-950/30 border-emerald-500 text-white shadow-lg shadow-emerald-500/10'
                  : 'bg-slate-950/40 border-slate-800/80 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-xs text-emerald-300">Banking Edition</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                  Zero Root
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                Pure unrooted system with MindTheGapps. Passes Play Integrity MEETS_BASIC without root hiding workarounds.
              </p>
            </button>
          </div>

          {/* Quick Install Action Bar */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Extracted Package Folder or AppxManifest.xml Path:
              </label>
              <input
                type="text"
                value={packagePath}
                onChange={(e) => setPackagePath(e.target.value)}
                placeholder="C:\Path\To\Extracted_WSA_Folder"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
              <div className="text-[11px] text-slate-400">
                {!status.virtualization_enabled ? (
                  <span className="text-rose-400 font-medium">⚠️ Enable BIOS virtualization before launching.</span>
                ) : !status.developer_mode_enabled ? (
                  <span className="text-amber-400 font-medium">⚠️ Sideloading requires Windows Developer Mode.</span>
                ) : (
                  <span className="text-emerald-400">✓ System is preflight-ready for package deployment.</span>
                )}
              </div>

              <button
                type="button"
                onClick={handleQuickInstall}
                disabled={isInstalling || !status.developer_mode_enabled}
                className="w-full sm:w-auto px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-all whitespace-nowrap"
              >
                {isInstalling ? 'Registering Subsystem...' : '1-Click Register & Install'}
              </button>
            </div>
          </div>

          {installResult && (
            <div
              className={`p-3 rounded-lg text-xs border ${
                installResult.success
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
              }`}
            >
              {installResult.message}
            </div>
          )}

          {installError && (
            <div className="p-3 rounded-lg text-xs bg-rose-500/10 text-rose-300 border border-rose-500/30">
              {installError}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

