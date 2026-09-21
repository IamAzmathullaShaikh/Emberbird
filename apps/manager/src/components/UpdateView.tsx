import React, { useState, useEffect, useCallback } from 'react';
import { preflightUpgrade, executeUpgrade, downloadAndStageRelease } from '../lib/ipc';
import { releasesFromRegistry, recommendedWsaAsset, resolveEditionAsset } from '../lib/registry';
import { useEmberStore } from '../lib/store';
import { StageProgressBar } from './StageProgress';
import { formatGB } from '../lib/formatters';
import type { UpgradePreflight, UpgradeResult } from '../lib/types';

/** Tri-state verdict rendering (Zero-Mock law): `null` means the probe could
 * not observe the host, so the chip reads UNVERIFIED — never a green pass. */
type Verdict = boolean | null;

const VERDICT_STYLES: Record<'ok' | 'fail' | 'unknown', { card: string; badge: string }> = {
  ok: { card: 'bg-surface-raised/70 border-emerald-500/30', badge: 'bg-emerald-500/20 text-emerald-300' },
  fail: { card: 'bg-rose-500/10 border-rose-500/30', badge: 'bg-rose-500/20 text-rose-300' },
  unknown: { card: 'bg-surface-raised/70 border-border-DEFAULT/40', badge: 'bg-surface-raised/20 text-text-secondary' },
};

function verdict(ok: Verdict): 'ok' | 'fail' | 'unknown' {
  if (ok === null) return 'unknown';
  return ok ? 'ok' : 'fail';
}

function verdictLabel(ok: Verdict, okText: string, failText: string): string {
  if (ok === null) return 'UNVERIFIED';
  return ok ? okText : failText;
}

export const UpdateView: React.FC = () => {
  const stageProgress = useEmberStore((s) => s.stageProgress);
  const setStageProgress = useEmberStore((s) => s.setStageProgress);
  const refreshStatus = useEmberStore((s) => s.refreshStatus);
  const addNotification = useEmberStore((s) => s.addNotification);

  const [preflight, setPreflight] = useState<UpgradePreflight | null>(null);
  const [loadingPreflight, setLoadingPreflight] = useState(false);
  const [packagePath, setPackagePath] = useState('');
  const [createBackup, setCreateBackup] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [activeStep, setActiveStep] = useState<string>('idle');
  const [upgradeResult, setUpgradeResult] = useState<UpgradeResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [stagingTag, setStagingTag] = useState<string | null>(null);

  const prefetchTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (prefetchTimerRef.current) clearTimeout(prefetchTimerRef.current);
    };
  }, []);

  const availableReleases = releasesFromRegistry().filter((r) => r.channel === 'wsa');
  // FB-1: the recommended target is the policy edition's newest published
  // registry asset — never the alphabetically-first row of a merged tag.
  const recommendedWsa = recommendedWsaAsset();

  const checkPreflight = useCallback(async (path?: string) => {
    setLoadingPreflight(true);
    setErrorMessage(null);
    try {
      const res = await preflightUpgrade(path || undefined);
      setPreflight(res);
    } catch (err) {
      setErrorMessage(`Preflight error: ${String(err)}`);
      addNotification({
        type: 'error',
        title: 'Preflight check failed',
        message: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoadingPreflight(false);
    }
  }, [addNotification]);

  useEffect(() => {
    checkPreflight();
  }, [checkPreflight]);

  const handlePackagePathChange = (val: string) => {
    setPackagePath(val);
    if (prefetchTimerRef.current) clearTimeout(prefetchTimerRef.current);
    prefetchTimerRef.current = setTimeout(() => {
      if (val.trim()) {
        checkPreflight(val.trim());
      } else {
        checkPreflight();
      }
    }, 300);
  };

  /**
   * FB-3 — Download the published registry asset for an edition, verify its
   * SHA-256 against the registry, extract, and prefill the staged manifest
   * path for the upgrade coordinator. No fabricated paths.
   */
  const handleDownloadAndStage = async (releaseTag: string, edition: string) => {
    setStagingTag(releaseTag);
    setStageProgress(null);
    setErrorMessage(null);
    try {
      const staged = await downloadAndStageRelease(releaseTag, edition, setStageProgress);
      setPackagePath(staged.manifest_path);
      await checkPreflight(staged.manifest_path);
    } catch (err) {
      setErrorMessage(`Download & stage failed: ${String(err)}`);
    } finally {
      setStagingTag(null);
      setStageProgress(null);
    }
  };

  const handleUpgradeToRecommended = () => {
    const recommended = recommendedWsaAsset();
    if (!recommended) {
      setErrorMessage('No recommended WSA release is published in the registry.');
      return;
    }
    handleDownloadAndStage(recommended.release_tag, recommended.edition);
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
        refreshStatus();
      } else {
        setErrorMessage(res.message || 'Upgrade orchestration failed.');
      }
    } catch (err) {
      setErrorMessage(`Upgrade execution error: ${String(err)}`);
    } finally {
      setUpgrading(false);
    }
  };

  // formatGB is now imported

  return (
    <div className="space-y-6">
      {/* 1-Click Upgrade to Observatory Recommended Release Hero */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-accent-active/50 via-purple-950/30 to-surface-raised/50 border border-accent/40 shadow-lg shadow-accent-active/20 backdrop-blur space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-accent-hover text-white">
                Observatory Recommended
              </span>
              <h2 className="text-base font-bold text-white">
                Automated 1-Click Upgrade
              </h2>
            </div>
            <p className="text-xs text-text-secondary mt-1">
              Target:{' '}
              <span className="font-mono text-accent font-semibold">
                {recommendedWsa
                  ? `${recommendedWsa.edition === 'banking' ? 'Banking' : 'Standard'} Edition · ${recommendedWsa.filename}`
                  : '—'}
              </span>{' '}
              (Tag {recommendedWsa?.release_tag ?? '—'})
            </p>
          </div>

          <button
            type="button"
            onClick={handleUpgradeToRecommended}
            disabled={!recommendedWsa}
            className="px-4 py-2 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-accent/30 transition-all whitespace-nowrap"
          >
            Select Recommended Build
          </button>
        </div>
      </div>

      {/* Upgrade Preflight Card */}
      <div className="p-6 rounded-xl bg-surface-raised/50 border border-border-DEFAULT shadow-sm backdrop-blur">

        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-white">
              Upgrade Coordinator &amp; Preflight Verification
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Automated system compatibility gating and atomic package deployment.
            </p>
          </div>
          <button
            type="button"
            onClick={() => checkPreflight(packagePath.trim() || undefined)}
            disabled={loadingPreflight}
            className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-raised border border-border-DEFAULT text-xs text-text-secondary transition-colors disabled:opacity-50"
          >
            {loadingPreflight ? 'Checking...' : 'Re-check Preflight'}
          </button>
        </div>

        {preflight && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            {/* Windows Build */}
            <div className={`p-3.5 rounded-lg border text-xs ${VERDICT_STYLES[verdict(preflight.windows_version_ok)].card}`}>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary font-medium">Windows OS Build</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${VERDICT_STYLES[verdict(preflight.windows_version_ok)].badge}`}>
                  {verdictLabel(preflight.windows_version_ok, 'PASS', 'FAIL')}
                </span>
              </div>
              <div className="mt-2 font-mono text-text-primary">
                {preflight.windows_build === null
                  ? 'Build not readable'
                  : `Build ${preflight.windows_build}`}{' '}
                (Req: {preflight.required_windows_build}+)
              </div>
            </div>

            {/* Developer Mode */}
            <div className={`p-3.5 rounded-lg border text-xs ${
              preflight.dev_mode_ok
                ? 'bg-surface-raised/70 border-emerald-500/30'
                : 'bg-rose-500/10 border-rose-500/30'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary font-medium">Developer Mode</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  preflight.dev_mode_ok ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                }`}>
                  {preflight.dev_mode_ok ? 'ACTIVE' : 'OFF'}
                </span>
              </div>
              <div className="mt-2 text-text-secondary text-[11px]">
                {preflight.dev_mode_ok ? 'AppModelUnlock Enabled' : 'Required for AppX Sideload'}
              </div>
            </div>

            {/* Virtualization */}
            <div className={`p-3.5 rounded-lg border text-xs ${
              preflight.virtualization_ok
                ? 'bg-surface-raised/70 border-emerald-500/30'
                : 'bg-rose-500/10 border-rose-500/30'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary font-medium">Virtualization</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  preflight.virtualization_ok ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                }`}>
                  {preflight.virtualization_ok ? 'PASS' : 'FAIL'}
                </span>
              </div>
              <div className="mt-2 text-text-secondary text-[11px]">
                Hyper-V / Platform OK
              </div>
            </div>

            {/* Disk Space */}
            <div className={`p-3.5 rounded-lg border text-xs ${
              preflight.disk_space_ok === null
                ? VERDICT_STYLES.unknown.card
                : preflight.disk_space_ok
                  ? VERDICT_STYLES.ok.card
                  : 'bg-amber-500/10 border-amber-500/30'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary font-medium">Disk Space</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  preflight.disk_space_ok === null
                    ? VERDICT_STYLES.unknown.badge
                    : preflight.disk_space_ok
                      ? VERDICT_STYLES.ok.badge
                      : 'bg-amber-500/20 text-amber-300'
                }`}>
                  {preflight.disk_space_ok === null ? 'UNVERIFIED' : preflight.disk_space_ok ? 'SUFFICIENT' : 'LOW'}
                </span>
              </div>
              <div className="mt-2 font-mono text-text-primary">
                {preflight.free_disk_bytes === null
                  ? 'Free space not measurable'
                  : `${formatGB(preflight.free_disk_bytes)} GB free`}{' '}
                (Req: {formatGB(preflight.required_disk_bytes)} GB)
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
        <div className="space-y-4 pt-2 border-t border-border-DEFAULT">
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">
              Extracted Package Directory or AppxManifest.xml Path:
            </label>
            <input
              type="text"
              value={packagePath}
              onChange={(e) => handlePackagePathChange(e.target.value)}
              placeholder="e.g. C:\Downloads\WSA-Package-2311-x64 or extracted folder..."
              className="w-full bg-surface-raised border border-border-DEFAULT/80 rounded-lg px-3.5 py-2.5 text-xs text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-DEFAULT transition-colors font-mono"
            />
            <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[11px]">
              <span className="text-text-muted">Download &amp; Stage from Registry:</span>
              {(['standard', 'banking'] as const).map((edition) => {
                const asset = resolveEditionAsset(edition);
                const busy = stagingTag === asset?.release_tag;
                return asset ? (
                  <button
                    key={edition}
                    type="button"
                    onClick={() => handleDownloadAndStage(asset.release_tag, edition)}
                    disabled={stagingTag !== null}
                    className={`px-2 py-0.5 rounded font-mono text-[10px] transition-colors disabled:opacity-50 ${
                      edition === 'standard'
                        ? 'bg-surface-raised hover:bg-surface-raised text-accent'
                        : 'bg-surface-raised hover:bg-surface-raised text-emerald-300'
                    }`}
                  >
                    {busy
                      ? 'Staging...'
                      : `${edition === 'standard' ? 'Standard' : 'Banking'} · ${asset.filename}`}
                  </button>
                ) : null;
              })}
            </div>

            {stagingTag && stageProgress && (
              <div className="mt-3 p-3 rounded-lg bg-accent/5 border border-accent/30 text-xs">
                <StageProgressBar progress={stageProgress} />
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="create_backup"
              checked={createBackup}
              onChange={(e) => setCreateBackup(e.target.checked)}
              className="w-4 h-4 rounded bg-surface-raised border-border-DEFAULT text-accent focus:ring-0 focus:ring-offset-0"
            />
            <label htmlFor="create_backup" className="text-xs text-text-secondary select-none cursor-pointer">
              Create verified safety snapshot of <span className="font-mono text-accent">userdata.vhdx</span> before installing
            </label>
          </div>

          {upgrading && (
            <div className="p-3.5 rounded-lg bg-surface-raised/80 border border-accent/30 flex items-center gap-3">
              <span className="w-3 h-3 rounded-full border-2 border-accent border-t-transparent animate-spin" />
              <span className="text-xs text-accent">{activeStep}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={handleExecuteUpgrade}
              disabled={upgrading || !preflight?.can_upgrade || !packagePath.trim()}
              className="px-5 py-2.5 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-40 text-white text-xs font-semibold shadow-lg shadow-accent/30 transition-all"
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
              <div className="font-mono text-[11px] text-text-secondary">
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

      {/* Available Releases Catalog from Registry */}
      <div className="p-6 rounded-xl bg-surface-raised/50 border border-border-DEFAULT shadow-sm backdrop-blur space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-white">
            Available Subsystem Releases (Registry Truth)
          </h3>
          <p className="text-xs text-text-secondary mt-0.5">
            Verified releases published in the Emberbird Release Registry.
          </p>
        </div>

        <div className="space-y-2">
          {availableReleases.map((r) => (
            <div
              key={r.tag_name}
              className="p-3 rounded-lg bg-surface-raised/60 border border-border-DEFAULT flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
            >
              <div>
                <span className="font-mono font-bold text-white mr-2">{r.tag_name}</span>
                <span className="text-text-muted text-[11px]">{r.published_at.slice(0, 10)}</span>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {r.assets.map((asset) => {
                  const edition = asset.edition;
                  if (!edition) {
                    return (
                      <span key={asset.name} className="text-[11px] text-text-muted font-mono break-all">
                        {asset.name}
                      </span>
                    );
                  }
                  return (
                    <button
                      key={`${edition}-${asset.name}`}
                      type="button"
                      onClick={() => handleDownloadAndStage(r.tag_name, edition)}
                      disabled={stagingTag !== null}
                      className={`px-2.5 py-1 rounded bg-surface-raised hover:bg-surface-raised disabled:opacity-50 text-[11px] font-medium transition-colors ${
                        edition === 'standard' ? 'text-accent' : 'text-emerald-300'
                      }`}
                    >
                      {stagingTag === r.tag_name
                        ? 'Staging...'
                        : `${edition === 'standard' ? 'Standard' : 'Banking'} · ${asset.name}`}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
