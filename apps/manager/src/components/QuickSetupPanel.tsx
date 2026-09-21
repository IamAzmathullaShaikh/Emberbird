import React from 'react';
import type { WsaStatus, InstallResult, StageProgress } from '../lib/types';
import type { WsaEdition, EditionAsset } from '../lib/registry';
import { formatGB } from '../lib/formatters';
import { StageProgressBar } from './StageProgress';
import { EditionSelector } from './EditionSelector';
import { AdvancedInstallFallback } from './AdvancedInstallFallback';
import { InstallErrorNotice } from './InstallErrorNotice';

interface QuickSetupPanelProps {
  status: WsaStatus;
  editionAsset: EditionAsset | null;
  selectedEdition: WsaEdition;
  onSelectEdition: (edition: WsaEdition) => void;
  isInstalling: boolean;
  stageProgress: StageProgress | null;
  installResult: InstallResult | null;
  installError: string | null;
  elevationRequired: boolean;
  lastAttemptPath: string;
  onQuickInstall: () => void;
  onOpenWizard: () => void;
  advanced: {
    show: boolean;
    onToggle: () => void;
    manualPath: string;
    onPathChange: (value: string) => void;
    onSubmit: () => void;
  };
}

/**
 * Quick Setup & One-Click Installer — rendered only while the subsystem is
 * NOT_INSTALLED. Edition cards, the resolved registry asset identity, live
 * staging progress, and honest readiness gating all live here; the install
 * lifecycle itself is owned by the parent (FB-3).
 */
export const QuickSetupPanel: React.FC<QuickSetupPanelProps> = ({
  status,
  editionAsset,
  selectedEdition,
  onSelectEdition,
  isInstalling,
  stageProgress,
  installResult,
  installError,
  elevationRequired,
  lastAttemptPath,
  onQuickInstall,
  onOpenWizard,
  advanced,
}) => {
  if (status.state !== 'NOT_INSTALLED') return null;

  return (
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

      <EditionSelector selectedEdition={selectedEdition} onSelect={onSelectEdition} />

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
              onClick={onOpenWizard}
              className="px-4 py-2 rounded-lg bg-surface-raised border border-border-DEFAULT hover:border-border-subtle text-text-secondary text-xs font-semibold shadow-md transition-all whitespace-nowrap"
            >
              Open Install Wizard
            </button>
            <button
              type="button"
              onClick={onQuickInstall}
              disabled={isInstalling || !status.developer_mode_enabled || !editionAsset}
              className="px-4 py-2 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-accent/30 transition-all whitespace-nowrap"
            >
              {isInstalling
                ? stageProgress !== null
                  ? 'Downloading & Verifying...'
                  : 'Registering Subsystem...'
                : '1-Click Download & Install'}
            </button>
          </div>
        </div>

        <AdvancedInstallFallback
          manualPath={advanced.manualPath}
          onPathChange={advanced.onPathChange}
          show={advanced.show}
          onToggle={advanced.onToggle}
          onSubmit={advanced.onSubmit}
          disabled={isInstalling || !status.developer_mode_enabled}
        />
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
        <InstallErrorNotice
          error={installError}
          elevationRequired={elevationRequired}
          manifestPath={lastAttemptPath}
        />
      )}
    </div>
  );
};
