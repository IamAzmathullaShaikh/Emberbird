import React, { useState } from 'react';
import { projectSubsystemStatus } from '../lib/state';
import { installWsaPackage, launchWsa, shutdownWsa, downloadAndStageRelease } from '../lib/ipc';
import { resolveEditionAsset, RECOMMENDED_WSA_EDITION } from '../lib/registry';
import { useEmberStore } from '../lib/store';
import { StageProgressBar } from './StageProgress';
import { formatGB } from '../lib/formatters';
import type { InstallResult, StagedAsset } from '../lib/types';
import { InstallerWizard } from './InstallerWizard';

/**
 * Root/GApps copy derived from the registry row for each edition — never a
 * hardcoded flavor claim (FB-4). Deliberately explicit about missing truth.
 */
function editionFlavors(edition: 'standard' | 'banking') {
  const asset = resolveEditionAsset(edition);
  const root =
    asset?.root_solution === 'magisk'
      ? 'Pre-rooted with Magisk'
      : asset?.root_solution === 'kernelsu'
        ? 'Pre-rooted with KernelSU'
        : asset?.root_solution === 'none'
          ? 'Unrooted system'
          : 'Root flavor per registry';
  const gapps =
    asset?.gapps_variant === 'pico'
      ? 'OpenGApps Pico'
      : asset?.gapps_variant === 'mindthegapps'
        ? 'MindTheGapps'
        : asset?.gapps_variant === 'none'
          ? 'no Google Apps'
          : 'Google services';
  return { root, gapps };
}

export const StatusCard: React.FC = () => {
  const status = useEmberStore((s) => s.wsaStatus);
  const refreshStatus = useEmberStore((s) => s.refreshStatus);
  const stageProgress = useEmberStore((s) => s.stageProgress);
  const setStageProgress = useEmberStore((s) => s.setStageProgress);

  const [selectedEdition, setSelectedEdition] = useState<'standard' | 'banking'>(
    RECOMMENDED_WSA_EDITION
  );
  const [manualPath, setManualPath] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [copiedCmd, setCopiedCmd] = useState(false);
  const [installResult, setInstallResult] = useState<InstallResult | null>(null);
  const [installError, setInstallError] = useState<string | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);

  const refreshTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const copiedTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastAttemptPathRef = React.useRef<string>('');

  React.useEffect(() => {
    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
      if (copiedTimerRef.current) clearTimeout(copiedTimerRef.current);
    };
  }, []);

  // Registry truth: the asset this machine would download for the selected
  // edition. `null` = the registry publishes no such edition — rendered
  // honestly, never guessed.
  const editionAsset = resolveEditionAsset(selectedEdition);
  const flavors = {
    standard: editionFlavors('standard'),
    banking: editionFlavors('banking'),
  };
  // Only claim a cause the backend actually reported — the elevation guidance
  // must never be shown for unrelated failures (Zero-Mock law).
  const elevationRequired = /0x80073D28|administrator privileges|elevation/i.test(
    installError ?? ''
  );

  if (!status) {
    return (
      <div className="p-6 rounded-2xl bg-surface-raised/40 border border-border-subtle animate-pulse">
        <div className="h-4 bg-surface-raised rounded w-1/4 mb-4"></div>
        <div className="h-3 bg-surface-raised/60 rounded w-3/4"></div>
      </div>
    );
  }

  const projected = projectSubsystemStatus(status);
  const { presentation } = projected;

  const handleSelectEdition = (edition: 'standard' | 'banking') => {
    setSelectedEdition(edition);
    setInstallError(null);
    setInstallResult(null);
    setStageProgress(null);
  };

  const registerStaged = async (manifestPath: string) => {
    lastAttemptPathRef.current = manifestPath;
    const res = await installWsaPackage(manifestPath);
    setInstallResult(res);
    if (res.success) refreshStatus();
    return res;
  };

  /**
   * FB-3 — the real one-click loop: download the published registry asset
   * for the selected edition, verify SHA-256 against the registry hash,
   * extract, then register the staged AppxManifest. No fabricated paths.
   */
  const handleQuickInstall = async () => {
    if (!editionAsset) {
      setInstallError(
        `The registry publishes no ${selectedEdition} edition package to install. Nothing was downloaded.`
      );
      return;
    }

    setIsInstalling(true);
    setInstallError(null);
    setInstallResult(null);
    setStageProgress(null);

    try {
      const staged: StagedAsset = await downloadAndStageRelease(
        editionAsset.release_tag,
        editionAsset.edition,
        setStageProgress
      );
      setStageProgress(null);
      await registerStaged(staged.manifest_path);
    } catch (err) {
      setInstallError(String(err));
    } finally {
      setIsInstalling(false);
    }
  };

  /** Advanced fallback: register an already-extracted package by path. */
  const handleManualInstall = async () => {
    if (!manualPath.trim()) {
      setInstallError('Please specify the path to your extracted WSA package directory or AppxManifest.xml.');
      return;
    }
    setIsInstalling(true);
    setInstallError(null);
    setInstallResult(null);
    try {
      await registerStaged(manualPath.trim());
    } catch (err) {
      setInstallError(`Installation error: ${String(err)}`);
    } finally {
      setIsInstalling(false);
    }
  };

  const handleLaunch = async (target?: string) => {
    setActionBusy(true);
    setActionFeedback(null);
    try {
      await launchWsa(target);
      setActionFeedback(`Launched ${target || 'WSA Settings'}`);
      refreshStatus();
    } catch (err) {
      setActionFeedback(`Launch failed: ${String(err)}`);
    } finally {
      setActionBusy(false);
    }
  };

  const handleShutdown = async () => {
    setActionBusy(true);
    setActionFeedback(null);
    try {
      await shutdownWsa();
      setActionFeedback('Shutdown signal sent to WSA.');
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = setTimeout(() => refreshStatus(), 1500);
    } catch (err) {
      setActionFeedback(`Shutdown failed: ${String(err)}`);
    } finally {
      setActionBusy(false);
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-surface-raised/50 border border-border-DEFAULT space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
          Subsystem Status & Environment
        </h2>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${presentation.dotClass}`} />
          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${presentation.badgeClass}`}>
            {presentation.label}
          </span>
          <span className="text-xs font-mono text-accent">
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
          <span className="text-text-muted block mb-0.5">Userdata VHDX Storage{status.state === 'NOT_INSTALLED' ? ' (orphaned data — no subsystem)' : ''}:</span>
          <code className="text-text-secondary font-mono text-[11px] select-all break-all">{status.vhdx_path}</code>
        </div>
      )}

      {/* Quick Launch & Control Panel (Surfaced when Subsystem is Registered / Installed) */}
      {status.state !== 'NOT_INSTALLED' && status.state !== 'UNKNOWN' && (
        <div className="mt-4 pt-4 border-t border-border-DEFAULT/80 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-text-secondary">Subsystem Controls</span>
            {actionFeedback && (
              <span className="text-[11px] text-accent">{actionFeedback}</span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => handleLaunch('wsa://settings')}
              disabled={actionBusy}
              className="px-3 py-1.5 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-xs font-semibold shadow transition-all flex items-center gap-1.5"
            >
              <span>⚙️</span> Open Settings
            </button>
            <button
              type="button"
              onClick={() => handleLaunch('wsa://com.android.vending')}
              disabled={actionBusy}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold shadow transition-all flex items-center gap-1.5"
            >
              <span>🛍️</span> Open Play Store
            </button>
            <button
              type="button"
              onClick={handleShutdown}
              disabled={actionBusy}
              className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-raised disabled:opacity-50 text-text-secondary text-xs font-medium border border-border-DEFAULT transition-all flex items-center gap-1.5"
            >
              <span>⏹️</span> Shut Down WSA
            </button>
          </div>
        </div>
      )}

      {/* 1-Click Quick Install & Setup Wizard (Surfaced when Subsystem is NOT_INSTALLED) */}
      {status.state === 'NOT_INSTALLED' && (
        <div className="mt-6 pt-5 border-t border-border-DEFAULT/80 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent-hover animate-ping"></span>
                Quick Setup &amp; One-Click Installer
              </h3>
              <p className="text-[11px] text-text-secondary mt-0.5">
                Register Windows Subsystem for Android directly onto this machine with verified prerequisites.
              </p>
            </div>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-accent/10 text-accent border border-accent/20">
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
                  ? 'bg-accent-active/30 border-accent text-white shadow-lg shadow-accent/10'
                  : 'bg-surface-raised/40 border-border-DEFAULT/80 text-text-secondary hover:border-border-DEFAULT'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-xs text-accent">Standard Edition</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-accent/20 text-accent">
                  {RECOMMENDED_WSA_EDITION === 'standard' ? 'Recommended' : 'Rooted'}
                </span>
              </div>
              <p className="text-[11px] text-text-secondary mt-1 leading-snug">
                {`${flavors.standard.root} + ${flavors.standard.gapps} + Google Play Store. Ideal for productivity, power users, and modding.`}
              </p>
            </button>

            <button
              type="button"
              onClick={() => handleSelectEdition('banking')}
              className={`p-3.5 rounded-xl text-left transition-all border ${
                selectedEdition === 'banking'
                  ? 'bg-emerald-950/30 border-emerald-500 text-white shadow-lg shadow-emerald-500/10'
                  : 'bg-surface-raised/40 border-border-DEFAULT/80 text-text-secondary hover:border-border-DEFAULT'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-xs text-emerald-300">Banking Edition</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                  {RECOMMENDED_WSA_EDITION === 'banking' ? 'Recommended' : 'Zero Root'}
                </span>
              </div>
              <p className="text-[11px] text-text-secondary mt-1 leading-snug">
                {`${flavors.banking.root} with ${flavors.banking.gapps}. Passes Play Integrity MEETS_BASIC without root hiding workarounds.`}
              </p>
            </button>
          </div>

          {/* FB-3 — Registry-asset install: download → verify → extract → register */}
          <div className="p-3.5 rounded-xl bg-surface-raised/60 border border-border-DEFAULT space-y-3">
            {editionAsset ? (
              <div className="p-3 rounded-lg bg-surface-raised/80 border border-border-DEFAULT text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-text-secondary">Registry asset ({selectedEdition} edition):</span>
                  <span className="font-mono text-accent">{editionAsset.release_tag}</span>
                </div>
                <div className="font-mono text-[11px] text-text-primary break-all">{editionAsset.filename}</div>
                <div className="text-[11px] text-text-secondary">
                  {formatGB(editionAsset.size_bytes)} GB · SHA-256 verified against the registry before install
                </div>
              </div>
            ) : (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300">
                The registry publishes no {selectedEdition}-edition package. One-click install is unavailable for this edition.
              </div>
            )}

            {stageProgress && isInstalling && (
              <div className="p-3 rounded-lg bg-accent/5 border border-accent/30 text-xs">
                <StageProgressBar progress={stageProgress} />
              </div>
            )}

            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="text-[11px] text-text-secondary">
                {!status.virtualization_enabled ? (
                  <span className="text-rose-400 font-medium">⚠️ Enable BIOS virtualization before launching.</span>
                ) : !status.developer_mode_enabled ? (
                  <span className="text-amber-400 font-medium">⚠️ Sideloading requires Windows Developer Mode.</span>
                ) : (
                  <span className="text-emerald-400">✓ System is preflight-ready for package deployment.</span>
                )}
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto">
                <button
                  type="button"
                  onClick={() => setWizardOpen(true)}
                  className="px-4 py-2 rounded-lg bg-surface-raised border border-border-DEFAULT hover:border-border-subtle text-text-secondary text-xs font-semibold shadow-md transition-all whitespace-nowrap"
                >
                  Open Install Wizard
                </button>
                <button
                  type="button"
                  onClick={handleQuickInstall}
                  disabled={isInstalling || !status.developer_mode_enabled || !editionAsset}
                  className="px-4 py-2 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-accent/30 transition-all whitespace-nowrap"
                >
                  {isInstalling ? (stageProgress !== null ? 'Downloading & Verifying...' : 'Registering Subsystem...') : '1-Click Download & Install'}
                </button>
              </div>
            </div>

            {/* Advanced fallback: register an already-extracted local package */}
            <div className="pt-1">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-[11px] text-text-muted hover:text-text-secondary transition-colors"
              >
                {showAdvanced ? '▾' : '▸'} Advanced: install from a local extracted package
              </button>
              {showAdvanced && (
                <div className="mt-2 space-y-2">
                  <input
                    type="text"
                    value={manualPath}
                    onChange={(e) => setManualPath(e.target.value)}
                    placeholder="C:\Path\To\Extracted_WSA_Folder"
                    className="w-full px-3 py-2 bg-surface-raised border border-border-DEFAULT rounded-lg text-xs font-mono text-white placeholder-text-muted focus:outline-none focus:border-accent-DEFAULT"
                  />
                  <button
                    type="button"
                    onClick={handleManualInstall}
                    disabled={isInstalling || !status.developer_mode_enabled}
                    className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-raised disabled:opacity-50 text-text-primary text-xs font-medium border border-border-DEFAULT transition-all"
                  >
                    Register Local Package
                  </button>
                </div>
              )}
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
            <div className="p-3.5 rounded-xl bg-rose-950/40 text-rose-300 border border-rose-500/30 text-xs space-y-2">
              <div className="font-semibold flex items-center gap-2 text-rose-200">
                <span>🛡️</span>
                <span>
                  {elevationRequired
                    ? 'Administrator Elevation Required (Windows Service Registration)'
                    : 'Install Failed'}
                </span>
              </div>
              <p className="text-[11px] text-rose-300/90 leading-relaxed font-mono break-all">
                {installError}
              </p>
              {elevationRequired && lastAttemptPathRef.current && (
                <>
                  <p className="text-[11px] text-rose-300/90 leading-relaxed">
                    Windows requires administrator privileges to install the WSA system service (<code className="font-mono text-rose-200">WsaService</code>).
                    Run Emberbird Manager as Administrator, or paste this command into an elevated PowerShell prompt:
                  </p>
                  <div className="p-2 rounded bg-surface-raised/80 border border-border-DEFAULT font-mono text-[11px] text-text-primary flex items-center justify-between gap-2 break-all">
                    <code>Add-AppxPackage -Register &quot;{lastAttemptPathRef.current}&quot; -ForceApplicationShutdown -ForceUpdateFromAnyVersion</code>
                    <button
                      type="button"
                      onClick={() => {
                        navigator.clipboard.writeText(`Add-AppxPackage -Register "${lastAttemptPathRef.current}" -ForceApplicationShutdown -ForceUpdateFromAnyVersion`);
                        setCopiedCmd(true);
                        if (copiedTimerRef.current) clearTimeout(copiedTimerRef.current);
                        copiedTimerRef.current = setTimeout(() => setCopiedCmd(false), 2000);
                      }}
                      className="px-2 py-1 rounded bg-surface-raised hover:bg-surface-raised text-[10px] text-accent font-sans whitespace-nowrap"
                    >
                      {copiedCmd ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}
      <InstallerWizard isOpen={wizardOpen} onClose={() => setWizardOpen(false)} />
    </div>
  );
};

