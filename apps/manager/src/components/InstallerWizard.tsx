import React, { useState, useEffect } from 'react';
import { useEmberStore } from '../lib/store';
import { preflightUpgrade, downloadAndStageRelease, installWsaPackage } from '../lib/ipc';
import { resolveEditionAsset, type EditionAsset } from '../lib/registry';
import { formatGB } from '../lib/formatters';
import { StageProgressBar } from './StageProgress';
import type { UpgradePreflight } from '../lib/types';

type WizardStep = 'edition' | 'preflight' | 'download' | 'install' | 'done' | 'error';

const STEP_LABELS: Record<WizardStep, string> = {
  edition:  '1. Select Edition',
  preflight: '2. System Check',
  download: '3. Download & Verify',
  install:  '4. Install',
  done:     '5. Complete',
  error:    'Error',
};

const STEPS: WizardStep[] = ['edition', 'preflight', 'download', 'install', 'done'];

interface InstallerWizardProps {
  isOpen: boolean;
  onClose: () => void;
}

export const InstallerWizard: React.FC<InstallerWizardProps> = ({ isOpen, onClose }) => {
  const stageProgress = useEmberStore((s) => s.stageProgress);
  const setStageProgress = useEmberStore((s) => s.setStageProgress);
  const refreshStatus = useEmberStore((s) => s.refreshStatus);
  const addNotification = useEmberStore((s) => s.addNotification);

  const [step, setStep] = useState<WizardStep>('edition');
  const [selectedEdition, setSelectedEdition] = useState<'standard' | 'banking'>('standard');
  const [selectedAsset, setSelectedAsset] = useState<EditionAsset | null>(null);
  const [preflight, setPreflight] = useState<UpgradePreflight | null>(null);
  const [checkingPreflight, setCheckingPreflight] = useState(false);
  const [installing, setInstalling] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [stagedManifest, setStagedManifest] = useState<string | null>(null);

  // Reset wizard state when opened
  useEffect(() => {
    if (isOpen) {
      setStep('edition');
      setSelectedEdition('standard');
      setSelectedAsset(null);
      setPreflight(null);
      setErrorMessage(null);
      setStagedManifest(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleEditionNext = () => {
    const asset = resolveEditionAsset(selectedEdition);
    if (!asset) {
      setErrorMessage(`No ${selectedEdition} edition asset found in registry.`);
      setStep('error');
      return;
    }
    setSelectedAsset(asset);
    setStep('preflight');
    runPreflight();
  };

  const runPreflight = async () => {
    setCheckingPreflight(true);
    try {
      const result = await preflightUpgrade();
      setPreflight(result);
    } catch (err) {
      setErrorMessage(`Preflight failed: ${err instanceof Error ? err.message : String(err)}`);
      setStep('error');
    } finally {
      setCheckingPreflight(false);
    }
  };

  const handleDownload = async () => {
    if (!selectedAsset) return;
    setStep('download');
    try {
      const staged = await downloadAndStageRelease(selectedAsset.release_tag, selectedEdition, setStageProgress);
      setStagedManifest(staged.manifest_path);
      setStep('install');
    } catch (err) {
      setErrorMessage(`Download failed: ${err instanceof Error ? err.message : String(err)}`);
      setStep('error');
    }
  };

  const handleInstall = async () => {
    if (!stagedManifest) return;
    setInstalling(true);
    try {
      const result = await installWsaPackage(stagedManifest);
      if (result.success) {
        setStep('done');
        await refreshStatus();
        addNotification({ type: 'success', title: 'Installation complete', message: 'WSA has been installed successfully.' });
      } else {
        setErrorMessage(result.message ?? 'Installation failed.');
        setStep('error');
      }
    } catch (err) {
      setErrorMessage(`Install failed: ${err instanceof Error ? err.message : String(err)}`);
      setStep('error');
    } finally {
      setInstalling(false);
      setStageProgress(null);
    }
  };

  const handleClose = () => {
    setStageProgress(null);
    onClose();
  };

  const preflightOk = preflight?.can_upgrade === true;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Install Wizard"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) handleClose(); }}
    >
      <div className="w-full max-w-lg bg-surface-raised border border-border-DEFAULT rounded-2xl shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
          <h2 className="text-text-primary font-bold text-lg">Install Wizard</h2>
          <button
            onClick={handleClose}
            aria-label="Close wizard"
            className="text-text-muted hover:text-text-primary transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Progress stepper */}
        <div className="flex px-6 pt-4 pb-2 gap-1">
          {STEPS.map((s, i) => (
            <div key={s} className={`flex-1 h-1 rounded-full transition-all ${
              STEPS.indexOf(step) >= i ? 'bg-accent' : 'bg-border-subtle'
            }`} />
          ))}
        </div>
        <div className="px-6 pb-3 text-[11px] text-text-muted">{STEP_LABELS[step]}</div>

        {/* Body */}
        <div className="px-6 py-4 min-h-48 flex flex-col gap-4">

          {/* Step 1: Edition */}
          {step === 'edition' && (
            <>
              <p className="text-text-secondary text-sm">Select the WSA edition to install:</p>
              {(['standard', 'banking'] as const).map((ed) => (
                <button
                  key={ed}
                  onClick={() => setSelectedEdition(ed)}
                  className={`p-4 rounded-xl border text-left transition-all ${
                    selectedEdition === ed
                      ? 'border-accent bg-accent/10 text-text-primary'
                      : 'border-border-DEFAULT bg-surface-DEFAULT text-text-secondary hover:border-accent/40'
                  }`}
                >
                  <div className="font-semibold capitalize">{ed} Edition</div>
                  <div className="text-[12px] text-text-muted mt-0.5">
                    {ed === 'standard' ? 'Full Android experience with Google Play' : 'Hardened for banking apps, additional security policies'}
                  </div>
                </button>
              ))}
            </>
          )}

          {/* Step 2: Preflight */}
          {step === 'preflight' && (
            <>
              {checkingPreflight ? (
                <div className="flex items-center gap-3 text-text-secondary text-sm">
                  <span className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                  Checking system requirements…
                </div>
              ) : preflight ? (
                <div className="flex flex-col gap-2">
                  <PreflightRow label="Windows Version" ok={preflight.windows_version_ok} />
                  <PreflightRow label="Developer Mode" ok={preflight.dev_mode_ok} />
                  <PreflightRow label="Virtualization" ok={preflight.virtualization_ok} />
                  <PreflightRow label="Disk Space" ok={preflight.disk_space_ok}
                    detail={preflight.free_disk_bytes != null ? `${formatGB(preflight.free_disk_bytes)} free` : undefined} />
                  {!preflightOk && (
                    <div className="mt-2 p-3 bg-status-fail/10 border border-status-fail/20 rounded-xl text-status-fail text-[12px]">
                      System requirements not met. Fix the failing checks before installing.
                    </div>
                  )}
                </div>
              ) : null}
            </>
          )}

          {/* Step 3: Download */}
          {step === 'download' && (
            <>
              <p className="text-text-secondary text-sm">Downloading and verifying WSA…</p>
              {stageProgress && <StageProgressBar progress={stageProgress} />}
              {!stageProgress && (
                <div className="flex items-center gap-2 text-text-muted text-sm">
                  <span className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                  Initializing download…
                </div>
              )}
            </>
          )}

          {/* Step 4: Install */}
          {step === 'install' && (
            <>
              <p className="text-text-secondary text-sm">Ready to install. Click Install to proceed.</p>
              <div className="p-3 bg-status-pass/5 border border-status-pass/20 rounded-xl text-status-pass text-[12px]">
                ✓ Download complete and SHA-256 verified
              </div>
              {installing && (
                <div className="flex items-center gap-2 text-text-secondary text-sm">
                  <span className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                  Installing WSA…
                </div>
              )}
            </>
          )}

          {/* Done */}
          {step === 'done' && (
            <div className="flex flex-col items-center gap-3 py-4">
              <div className="text-4xl">✅</div>
              <p className="text-text-primary font-bold text-lg">Installation Complete!</p>
              <p className="text-text-secondary text-sm text-center">WSA has been installed and registered. You may close this wizard.</p>
            </div>
          )}

          {/* Error */}
          {step === 'error' && (
            <div className="flex flex-col gap-3">
              <div className="p-3 bg-status-fail/10 border border-status-fail/20 rounded-xl text-status-fail text-[13px]">
                <div className="font-semibold mb-1">Installation Error</div>
                {errorMessage}
              </div>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="flex justify-between px-6 py-4 border-t border-border-subtle">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm text-text-muted hover:text-text-secondary transition-colors"
          >
            {step === 'done' ? 'Close' : 'Cancel'}
          </button>

          {step === 'edition' && (
            <button
              onClick={handleEditionNext}
              className="px-5 py-2 bg-accent hover:bg-accent-hover text-white text-sm font-semibold rounded-xl transition-all"
            >
              Next ›
            </button>
          )}

          {step === 'preflight' && !checkingPreflight && (
            <button
              onClick={handleDownload}
              disabled={!preflightOk}
              className="px-5 py-2 bg-accent hover:bg-accent-hover disabled:opacity-40 text-white text-sm font-semibold rounded-xl transition-all"
            >
              Download ›
            </button>
          )}

          {step === 'install' && !installing && (
            <button
              onClick={handleInstall}
              className="px-5 py-2 bg-accent hover:bg-accent-hover text-white text-sm font-semibold rounded-xl transition-all"
            >
              Install ›
            </button>
          )}

          {(step === 'error') && (
            <button
              onClick={() => { setStep('edition'); setErrorMessage(null); }}
              className="px-5 py-2 bg-surface-raised border border-border-DEFAULT text-text-secondary text-sm rounded-xl"
            >
              Start Over
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

const PreflightRow: React.FC<{ label: string; ok: boolean | null; detail?: string }> = ({ label, ok, detail }) => (
  <div className="flex items-center justify-between text-sm">
    <span className="text-text-secondary">{label}</span>
    <span className={`font-medium ${
      ok === null ? 'text-text-muted' : ok ? 'text-status-pass' : 'text-status-fail'
    }`}>
      {ok === null ? 'UNVERIFIED' : ok ? '✓ PASS' : '✗ FAIL'}
      {detail && <span className="text-text-muted ml-1 font-normal">({detail})</span>}
    </span>
  </div>
);
