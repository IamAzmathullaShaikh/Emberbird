import React, { useState } from 'react';
import { installWsaPackage, launchWsa, shutdownWsa, downloadAndStageRelease } from '../lib/ipc';
import { resolveEditionAsset, RECOMMENDED_WSA_EDITION, type WsaEdition } from '../lib/registry';
import { useEmberStore } from '../lib/store';
import type { InstallResult, StagedAsset } from '../lib/types';
import { StatusOverview } from './StatusOverview';
import { SubsystemControls } from './SubsystemControls';
import { QuickSetupPanel } from './QuickSetupPanel';
import { InstallerWizard } from './InstallerWizard';

/**
 * Subsystem dashboard orchestrator.
 *
 * Owns the install lifecycle and local UI state; presentation is delegated to
 * `StatusOverview`, `SubsystemControls`, and `QuickSetupPanel`. Every claim
 * those children render traces back to the store's real probe payload or to
 * registry truth — nothing here fabricates machine state (Zero-Mock law).
 */
export const StatusCard: React.FC = () => {
  const status = useEmberStore((s) => s.wsaStatus);
  const refreshStatus = useEmberStore((s) => s.refreshStatus);
  const stageProgress = useEmberStore((s) => s.stageProgress);
  const setStageProgress = useEmberStore((s) => s.setStageProgress);

  const [selectedEdition, setSelectedEdition] = useState<WsaEdition>(RECOMMENDED_WSA_EDITION);
  const [manualPath, setManualPath] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [installResult, setInstallResult] = useState<InstallResult | null>(null);
  const [installError, setInstallError] = useState<string | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);

  const refreshTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastAttemptPathRef = React.useRef<string>('');

  React.useEffect(() => {
    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, []);

  // Registry truth: the asset this machine would download for the selected
  // edition. `null` = the registry publishes no such edition — rendered
  // honestly by QuickSetupPanel, never guessed.
  const editionAsset = resolveEditionAsset(selectedEdition);
  // Only claim a cause the backend actually reported (Zero-Mock law).
  const elevationRequired = /0x80073D28|administrator privileges|elevation/i.test(installError ?? '');

  if (!status) {
    return (
      <div className="p-6 rounded-2xl bg-surface-raised/40 border border-border-subtle animate-pulse">
        <div className="h-4 bg-surface-raised rounded w-1/4 mb-4"></div>
        <div className="h-3 bg-surface-raised/60 rounded w-3/4"></div>
      </div>
    );
  }

  const handleSelectEdition = (edition: WsaEdition) => {
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
   * FB-3 — the real one-click loop: download the published registry asset for
   * the selected edition, verify SHA-256 against the registry hash, extract,
   * then register the staged AppxManifest. No fabricated paths.
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
      <StatusOverview status={status} />

      <SubsystemControls
        status={status}
        busy={actionBusy}
        feedback={actionFeedback}
        onLaunch={handleLaunch}
        onShutdown={handleShutdown}
      />

      <QuickSetupPanel
        status={status}
        editionAsset={editionAsset}
        selectedEdition={selectedEdition}
        onSelectEdition={handleSelectEdition}
        isInstalling={isInstalling}
        stageProgress={stageProgress}
        installResult={installResult}
        installError={installError}
        elevationRequired={elevationRequired}
        lastAttemptPath={lastAttemptPathRef.current}
        onQuickInstall={handleQuickInstall}
        onOpenWizard={() => setWizardOpen(true)}
        advanced={{
          show: showAdvanced,
          onToggle: () => setShowAdvanced(!showAdvanced),
          manualPath,
          onPathChange: setManualPath,
          onSubmit: handleManualInstall,
        }}
      />

      <InstallerWizard isOpen={wizardOpen} onClose={() => setWizardOpen(false)} />
    </div>
  );
};
