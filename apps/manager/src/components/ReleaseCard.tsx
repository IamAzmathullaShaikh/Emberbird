import React, { useState } from 'react';
import { projectSubsystemStatus } from '../lib/state';
import { recommendedWsaAsset, recommendedWsaLabel, publishedWsaArchitectures } from '../lib/registry';
import { useEmberStore } from '../lib/store';

export const ReleaseCard: React.FC = () => {
  const status = useEmberStore((s) => s.wsaStatus);
  const updateStatus = useEmberStore((s) => s.updateStatus);
  const checking = useEmberStore((s) => s.checkingUpdates);
  const onCheckUpdates = useEmberStore((s) => s.checkForUpdates);
  const [selectedArch, setSelectedArch] = useState<'all' | 'x64' | 'arm64'>('all');

  // FB-1/FB-4: recommendation and architecture coverage derive from registry
  // truth. The compatibility pill shows the registry tag — no unverifiable
  // hardcoded percentage.
  const recommended = recommendedWsaAsset();
  const recommendedLabel = recommendedWsaLabel();
  const recommendedTag = recommended?.release_tag;
  const shippedArchs = publishedWsaArchitectures();
  const archOptions: Array<'all' | 'x64' | 'arm64'> = ['all', ...shippedArchs];

  const projected = projectSubsystemStatus(status);
  const installedLabel = projected.presentation.mayShowVersion
    ? (updateStatus?.current_version || projected.versionLabel)
    : projected.presentation.label;

  return (
    <div className="p-6 rounded-2xl bg-ember-charcoal/60 border border-ember-ash/20 shadow-xl backdrop-blur-sm space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-bold uppercase tracking-widest text-ember-ash">
          Release Intelligence & Updates
        </h2>
        <button
          type="button"
          onClick={onCheckUpdates}
          disabled={checking}
          className="text-xs text-ember-glow hover:text-ember-highlight transition-colors disabled:opacity-50 font-medium"
        >
          {checking ? 'Querying Registry...' : 'Check Now'}
        </button>
      </div>

      {/* Observatory Recommendation Banner */}
      <div className="p-4 rounded-xl bg-gradient-to-br from-ember-glow/10 via-ember-obsidian/40 to-ember-obsidian border border-ember-glow/30 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-ember-glow text-ember-obsidian shadow-sm">
              Observatory Recommended
            </span>
            <span className="font-bold text-xs text-text-primary">
              {recommendedLabel}
            </span>
          </div>
          <span className="text-[11px] font-mono text-status-pass bg-status-pass/10 px-2 py-0.5 rounded border border-status-pass/20">
            {recommendedTag ?? 'Registry unavailable'}
          </span>
        </div>
        <p className="text-[11px] text-ember-ash leading-relaxed">
          {`Curated release baseline: Android 13 LTS kernel, verified Play Integrity baseline, native DirectX 12 GPU acceleration, and ${
            recommended?.root_solution === 'magisk'
              ? 'Magisk root pre-installed'
              : 'an unrooted system image'
          }.`}
        </p>
      </div>

      {/* Architecture Filter & Capability Pill */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs text-ember-ash font-medium">Architecture Filter:</span>
          <div className="flex items-center gap-1 bg-ember-obsidian p-1 rounded-lg border border-ember-ash/20">
            {archOptions.map((arch) => (
              <button
                key={arch}
                type="button"
                onClick={() => setSelectedArch(arch)}
                className={`px-2.5 py-0.5 rounded text-[11px] font-mono transition-all duration-200 ${
                  selectedArch === arch
                    ? 'bg-ember-glow text-ember-obsidian font-bold shadow-sm'
                    : 'text-ember-ash hover:text-text-primary hover:bg-ember-ash/20'
                }`}
              >
                {arch === 'all' ? 'All' : arch.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {selectedArch === 'arm64' && shippedArchs.includes('arm64') && (
          <div className="p-3 rounded-lg bg-ember-glow/5 border border-ember-glow/20 text-[11px] text-ember-ash">
            <span className="font-bold text-ember-glow">Snapdragon X Elite / Copilot+ PC: </span>
            ARM64 builds execute with native ARM64 virtualization and zero x64 emulation overhead, preserving battery life and performance.
          </div>
        )}

        {selectedArch === 'x64' && shippedArchs.includes('x64') && (
          <div className="p-3 rounded-lg bg-ember-obsidian/50 border border-ember-ash/20 text-[11px] text-ember-ash">
            <span className="font-bold text-text-primary">Intel Core & AMD Ryzen: </span>
            x64 builds are compiled with AVX2 optimizations and DirectX 12 hardware acceleration.
          </div>
        )}
      </div>

      {updateStatus ? (
        <div className="space-y-3 text-xs">
          <div className="flex items-center justify-between p-4 rounded-xl bg-ember-obsidian/60 border border-ember-ash/30">
            <div className="flex flex-col">
              <div className="text-ember-ash text-[10px] uppercase tracking-wider font-medium">Current Engine Build</div>
              <div className="font-mono text-sm font-bold text-text-primary mt-0.5">
                {installedLabel}
              </div>
            </div>
            <div className="flex flex-col text-right">
              <div className="text-ember-ash text-[10px] uppercase tracking-wider font-medium">Latest Available</div>
              <div className="font-mono text-sm font-bold text-ember-glow mt-0.5">
                {updateStatus.latest_version || 'Querying...'}
              </div>
            </div>
          </div>

          {updateStatus.update_available ? (
            <div className="p-4 rounded-xl bg-ember-glow/10 border border-ember-glow/30 flex items-center justify-between">
              <div className="space-y-1">
                <span className="font-bold text-ember-glow block">New Engine Build Available!</span>
                <span className="text-[11px] text-ember-ash leading-tight">Upgrade Coordinator ready. Switch to the Updates tab to deploy with safety backup.</span>
              </div>
              <span className="px-3 py-1 rounded-lg bg-ember-glow text-ember-obsidian font-bold text-xs shadow-lg shadow-ember-glow/20">
                Update Ready
              </span>
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-ember-obsidian/40 border border-ember-ash/20 text-ember-ash text-center font-medium">
              Your engine installation matches the latest verified release tag.
            </div>
          )}
        </div>
      ) : (
        <div className="py-8 text-center text-xs text-ember-ash animate-pulse">
          Querying Release Registry...
        </div>
      )}
    </div>
  );
};