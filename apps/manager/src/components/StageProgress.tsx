import React from 'react';
import type { StageProgress } from '../lib/types';

interface StageProgressBarProps {
  progress: StageProgress;
}

const PHASE_LABELS: Record<string, string> = {
  downloading: 'Downloading',
  verifying: 'Verifying SHA-256',
  extracting: 'Extracting archive',
  done: 'Complete',
};

const PHASE_ICON: Record<string, string> = {
  downloading: '↓',
  verifying: '✓',
  extracting: '⊙',
  done: '●',
};

export const StageProgressBar: React.FC<StageProgressBarProps> = ({ progress }) => {
  const percent =
    progress.total_bytes > 0
      ? Math.min(100, Math.round((progress.received_bytes / progress.total_bytes) * 100))
      : 0;

  const phaseLabel = PHASE_LABELS[progress.phase] ?? progress.phase;
  const phaseIcon = PHASE_ICON[progress.phase] ?? '·';
  const isDone = progress.phase === 'done';

  return (
    <div className="flex flex-col gap-2 w-full">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-text-secondary">
          <span
            className={`font-mono ${
              isDone ? 'text-status-pass' : 'text-accent animate-pulse'
            }`}
          >
            {phaseIcon}
          </span>
          <span className="font-medium">{phaseLabel}</span>
          {progress.message && (
            <span className="text-text-muted truncate max-w-[180px]">{progress.message}</span>
          )}
        </div>
        <span className="font-mono text-text-primary tabular-nums">{percent}%</span>
      </div>
      <div className="w-full h-1.5 bg-surface-raised rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            isDone ? 'bg-status-pass' : 'bg-accent'
          }`}
          style={{ width: `${percent}%` }}
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
};
