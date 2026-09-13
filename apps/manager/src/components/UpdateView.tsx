import React, { useState, useEffect } from 'react';
import { preflightUpgrade, executeUpgrade } from '../lib/ipc';
import type { UpgradePreflight, UpgradeResult } from '../lib/types';

interface UpdateViewProps {
  onUpgradeSuccess?: () => void;
}

export const UpdateView: React.FC<UpdateViewProps> = ({ onUpgradeSuccess }) => {
  const [preflight, setPreflight] = useState<UpgradePreflight | null>(null);
  const [loadingPreflight, setLoadingPreflight] = useState(false);
  const [packagePath, setPackagePath] = useState('');
  const [createBackup, setCreateBackup] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [activeStep, setActiveStep] = useState<string>('idle');
  const [upgradeResult, setUpgradeResult] = useState<UpgradeResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const checkPreflight = async (path?: string) => {
    setLoadingPreflight(true);
    setErrorMessage(null);
    try {
      const res = await preflightUpgrade(path || undefined);
      setPreflight(res);
    } catch (err) {
      console.error('Failed to run preflight check:', err);
      setErrorMessage(`Preflight error: ${String(err)}`);
    } finally {
      setLoadingPreflight(false);
    }
  };

  useEffect(() => {
    checkPreflight();
  }, []);

  const handlePackagePathChange = (val: string) => {
    setPackagePath(val);
    if (val.trim()) {
      checkPreflight(val.trim());
    } else {
      checkPreflight();
    }
  };

  const handleExecuteUpgrade = async () => {
    if (!packagePath.trim()) {
      setErrorMessage('Please provide a path to the extracted WSA package or AppxManifest.xml.');
      return;
    }

    setUpgrading(true);
    setErrorMessage(null);
    setUpgradeResult(null);

    try {
      setActiveStep(createBackup ? 'Creating safety container backup...' : 'Registering package...');
      const res = await executeUpgrade({
        package_path: packagePath.trim(),
        create_backup: createBackup,
        backup_note: 'Automated pre-upgrade backup snapshot',
      });

      setUpgradeResult(res);
      if (res.success) {
        setActiveStep('Upgrade completed successfully.');
        if (onUpgradeSuccess) onUpgradeSuccess();
      } else {
        setErrorMessage(res.message || 'Upgrade orchestration failed.');
      }
    } catch (err) {
      setErrorMessage(`Upgrade execution error: ${String(err)}`);
    } finally {
      setUpgrading(false);
    }
  };

  const formatGB = (bytes: number) => {
    return (bytes / (1024 * 1024 * 1024)).toFixed(1);
  };

  return (
    <div className="space-y-6">
      {/* Upgrade Preflight Card */}
      <div className="p-6 rounded-xl bg-slate-900/50 border border-slate-800 shadow-sm backdrop-blur">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-white">
              Upgrade Coordinator &amp; Preflight Verification
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Automated system compatibility gating and atomic package deployment.
            </p>
          </div>
          <button
            type="button"
            onClick={() => checkPreflight(packagePath.trim() || undefined)}
            disabled={loadingPreflight}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-300 transition-colors disabled:opacity-50"
          >
            {loadingPreflight ? 'Checking...' : 'Re-check Preflight'}
          </button>
        </div>

        {preflight && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            {/* Windows Build */}
            <div className={`p-3.5 rounded-lg border text-xs ${
              preflight.windows_version_ok
                ? 'bg-slate-950/70 border-emerald-500/30'
                : 'bg-rose-500/10 border-rose-500/30'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-medium">Windows OS Build</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  preflight.windows_version_ok ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                }`}>
                  {preflight.windows_version_ok ? 'PASS' : 'FAIL'}
                </span>
              </div>
              <div className="mt-2 font-mono text-slate-200">
                Build {preflight.windows_build} (Req: 19045+)
              </div>
            </div>

            {/* Developer Mode */}
            <div className={`p-3.5 rounded-lg border text-xs ${
              preflight.dev_mode_ok
                ? 'bg-slate-950/70 border-emerald-500/30'
                : 'bg-rose-500/10 border-rose-500/30'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-medium">Developer Mode</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  preflight.dev_mode_ok ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                }`}>
                  {preflight.dev_mode_ok ? 'ACTIVE' : 'OFF'}
                </span>
              </div>
              <div className="mt-2 text-slate-300 text-[11px]">
                {preflight.dev_mode_ok ? 'AppModelUnlock Enabled' : 'Required for AppX Sideload'}
              </div>
            </div>

            {/* Virtualization */}
            <div className={`p-3.5 rounded-lg border text-xs ${
              preflight.virtualization_ok
                ? 'bg-slate-950/70 border-emerald-500/30'
                : 'bg-rose-500/10 border-rose-500/30'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-medium">Virtualization</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  preflight.virtualization_ok ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                }`}>
                  {preflight.virtualization_ok ? 'PASS' : 'FAIL'}
                </span>
              </div>
              <div className="mt-2 text-slate-300 text-[11px]">
                Hyper-V / Platform OK
              </div>
            </div>

            {/* Disk Space */}
            <div className={`p-3.5 rounded-lg border text-xs ${
              preflight.disk_space_ok
                ? 'bg-slate-950/70 border-emerald-500/30'
                : 'bg-amber-500/10 border-amber-500/30'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-medium">Disk Space</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  preflight.disk_space_ok ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
                }`}>
                  {preflight.disk_space_ok ? 'SUFFICIENT' : 'LOW'}
                </span>
              </div>
              <div className="mt-2 font-mono text-slate-200">
                {formatGB(preflight.free_disk_bytes)} GB free (Req: 25 GB)
              </div>
            </div>
          </div>
        )}

        {/* Warnings or Errors from Preflight */}
        {preflight && preflight.warnings.length > 0 && (
          <div className="p-3 mb-4 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs space-y-1">
            {preflight.warnings.map((w, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <span>⚠</span>
                <span>{w}</span>
              </div>
            ))}
          </div>
        )}

        {preflight && preflight.errors.length > 0 && (
          <div className="p-3 mb-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs space-y-1">
            {preflight.errors.map((err, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <span>✖</span>
                <span>{err}</span>
              </div>
            ))}
          </div>
        )}

        {/* Upgrade Execution Form */}
        <div className="space-y-4 pt-2 border-t border-slate-800">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Extracted Package Directory or AppxManifest.xml Path:
            </label>
            <input
              type="text"
              value={packagePath}
              onChange={(e) => handlePackagePathChange(e.target.value)}
              placeholder="e.g. C:\Downloads\WSA-Package-2311-x64 or extracted folder..."
              className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors font-mono"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="create_backup"
              checked={createBackup}
              onChange={(e) => setCreateBackup(e.target.checked)}
              className="w-4 h-4 rounded bg-slate-950 border-slate-700 text-indigo-600 focus:ring-0 focus:ring-offset-0"
            />
            <label htmlFor="create_backup" className="text-xs text-slate-300 select-none cursor-pointer">
              Create verified safety snapshot of <span className="font-mono text-indigo-300">userdata.vhdx</span> before installing
            </label>
          </div>

          {upgrading && (
            <div className="p-3.5 rounded-lg bg-slate-950/80 border border-indigo-500/30 flex items-center gap-3">
              <span className="w-3 h-3 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
              <span className="text-xs text-indigo-200">{activeStep}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={handleExecuteUpgrade}
              disabled={upgrading || !preflight?.can_upgrade || !packagePath.trim()}
              className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all"
            >
              {upgrading ? 'Executing Upgrade...' : 'Start Upgrade'}
            </button>
          </div>
        </div>

        {errorMessage && (
          <div className="mt-4 p-3 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/30 text-xs">
            {errorMessage}
          </div>
        )}

        {upgradeResult && upgradeResult.success && (
          <div className="mt-4 p-4 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 text-xs space-y-2">
            <div className="font-semibold text-sm text-emerald-200">
              Upgrade Completed Successfully!
            </div>
            {upgradeResult.installed_manifest && (
              <div className="font-mono text-[11px] text-slate-300">
                Registered: {upgradeResult.installed_manifest}
              </div>
            )}
            {upgradeResult.backup_metadata && (
              <div className="text-[11px] text-emerald-300/80">
                Pre-upgrade safety snapshot: {upgradeResult.backup_metadata.id}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
