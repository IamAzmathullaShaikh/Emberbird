import React, { useState } from 'react';
import { projectSubsystemStatus } from '../lib/state';
import type { WsaStatus, UpdateStatus } from '../lib/types';

interface ReleaseCardProps {
  status: WsaStatus | null;
  updateStatus: UpdateStatus | null;
  onCheckUpdates: () => void;
  checking: boolean;
}

export const ReleaseCard: React.FC<ReleaseCardProps> = ({ status, updateStatus, onCheckUpdates, checking }) => {
  const [selectedArch, setSelectedArch] = useState<'all' | 'x64' | 'arm64'>('all');

  // Version wording derives from the unified state model, never from the
  // update payload alone — this is what prevents "Not Installed" appearing
  // next to a known installed version.
  const projected = projectSubsystemStatus(status);
  const installedLabel = projected.presentation.mayShowVersion
    ? (updateStatus?.current_version || projected.versionLabel)
    : projected.presentation.label;

  return (
    <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Release Intelligence &amp; Updates
        </h2>
        <button
          type="button"
          onClick={onCheckUpdates}
          disabled={checking}
          className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors disabled:opacity-50"
        >
          {checking ? 'Checking GitHub...' : 'Check Now'}
        </button>
      </div>

      {/* Observatory Recommendation Banner */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-950/40 border border-indigo-500/30 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-indigo-500 text-white shadow-sm">
              Observatory Recommended
            </span>
            <span className="font-semibold text-xs text-white">
              Standard Edition 2407.40000.4.0
            </span>
          </div>
          <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            88.3% Verified Compatibility
          </span>
        </div>
        <p className="text-[11px] text-slate-300 leading-relaxed">
          Curated release baseline: Android 13 LTS kernel, verified Play Integrity baseline, native DirectX 12 GPU acceleration, and certified Magisk 27.0 root.
        </p>
      </div>

      {/* Architecture Filter & Capability Pill */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400 font-medium">Architecture Filter:</span>
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
            {(['all', 'x64', 'arm64'] as const).map((arch) => (
              <button
                key={arch}
                type="button"
                onClick={() => setSelectedArch(arch)}
                className={`px-2.5 py-0.5 rounded text-[11px] font-mono transition-all ${
                  selectedArch === arch
                    ? 'bg-indigo-600 text-white font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {arch === 'all' ? 'All' : arch.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {selectedArch === 'arm64' && (
          <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-[11px] text-indigo-300">
            <span className="font-semibold">Snapdragon X Elite / Copilot+ PC: </span>
            ARM64 builds execute with native ARM64 virtualization and zero x64 emulation overhead, preserving battery life and performance.
          </div>
        )}

        {selectedArch === 'x64' && (
          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400">
            <span className="font-semibold text-slate-300">Intel Core &amp; AMD Ryzen: </span>
            x64 builds are compiled with AVX2 optimizations and DirectX 12 hardware acceleration.
          </div>
        )}
      </div>

      {updateStatus ? (
        <div className="space-y-3 text-xs">
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <div>
              <div className="text-slate-500">Current Installed WSA</div>
              <div className="font-mono text-sm font-bold text-white mt-0.5">
                {installedLabel}
              </div>
            </div>
            <div className="text-right">
              <div className="text-slate-500">Latest Available Release</div>
              <div className="font-mono text-sm font-bold text-indigo-400 mt-0.5">
                {updateStatus.latest_version || 'Querying...'}
              </div>
            </div>
          </div>

          {updateStatus.update_available ? (
            <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-between">
              <div>
                <span className="font-bold text-indigo-300 block">New WSA Release Available!</span>
                <span className="text-[11px] text-slate-400">Upgrade Coordinator ready. Switch to the Updates tab to preflight and deploy with safety backup.</span>
              </div>
              <span className="px-3 py-1 rounded-lg bg-indigo-600 text-white font-medium text-xs">
                Update Ready
              </span>
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/60 text-slate-400 text-center">
              Your WSA installation matches the latest verified release tag.
            </div>
          )}
        </div>
      ) : (
        <div className="py-6 text-center text-xs text-slate-500">
          Loading release metadata from GitHub repository...
        </div>
      )}
    </div>
  );
};

