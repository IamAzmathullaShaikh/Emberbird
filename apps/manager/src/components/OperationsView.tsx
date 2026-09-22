import React, { useEffect } from 'react';
import { useEmberStore } from '../lib/store';
import type { OperationRecord } from '../lib/types';

/** `STAGE-<yyyymmdd>-<hhmmss>-<8 hex>` → `STAGE 2026-09-22 14:03:01 · a1b2c3d4` */
export function formatOperationId(operationId: string): string {
  const match = /^STAGE-(\d{4})(\d{2})(\d{2})-(\d{6})-([0-9a-f]{8})$/.exec(operationId);
  if (!match) return operationId;
  const [, y, mo, d, hms, hex] = match;
  return `STAGE ${y}-${mo}-${d} ${hms.replace(/(..)(..)(..)/, '$1:$2:$3')} · ${hex}`;
}

function formatBytes(bytes: number | null): string {
  if (bytes === null) return '—';
  const units = ['B', 'KiB', 'MiB', 'GiB'];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value < 10 && unit > 0 ? value.toFixed(1) : Math.round(value)} ${units[unit]}`;
}

function formatDuration(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(ms >= 10_000 ? 0 : 1)}s`;
  return `${ms}ms`;
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString();
}

const RESULT_STYLES: Record<string, string> = {
  success: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  failed: 'bg-red-500/15 text-red-300 border-red-500/30',
};

function ResultBadge({ result }: { result: string }) {
  const style = RESULT_STYLES[result] ?? 'bg-amber-500/15 text-amber-300 border-amber-500/30';
  return (
    <span className={`px-2 py-0.5 rounded-full border text-xs font-semibold ${style}`} data-testid={`operation-result-${result}`}>
      {result}
    </span>
  );
}

function OperationRow({ record }: { record: OperationRecord }) {
  const [expanded, setExpanded] = React.useState(false);
  return (
    <li className="p-4 rounded-xl bg-surface-raised/60 border border-DEFAULT">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        aria-expanded={expanded}
        className="w-full text-left flex flex-wrap items-center gap-x-3 gap-y-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded-lg"
      >
        <ResultBadge result={record.result} />
        <span className="font-mono text-sm text-text-primary">{formatOperationId(record.operation_id)}</span>
        <span className="text-sm text-text-secondary truncate max-w-[16rem]" title={record.asset}>
          {record.asset}
        </span>
        <span className="ml-auto text-xs text-text-secondary">
          {formatTimestamp(record.started_at)} · {formatDuration(record.duration_ms)}
        </span>
      </button>
      {expanded && (
        <div className="mt-3 pt-3 border-t border-DEFAULT space-y-2 text-sm">
          {record.error && (
            <p className="text-red-300" role="alert">
              {record.error}
            </p>
          )}
          {record.stages.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {record.stages.map((stage) => (
                <span
                  key={`${record.operation_id}-${stage.stage}-${stage.started_at}`}
                  className="px-2 py-0.5 rounded-md bg-surface-base/80 border border-DEFAULT text-xs font-mono"
                >
                  {stage.stage}: {formatDuration(stage.duration_ms)}
                </span>
              ))}
            </div>
          )}
          <p className="text-text-secondary text-xs font-mono break-all">
            sha256: {record.sha256 ?? '—'} · {formatBytes(record.size_bytes)}
          </p>
        </div>
      )}
    </li>
  );
}

/**
 * PH-45: the durable staging-operation log. Every download/verify/extract the
 * manager runs is recorded with an id, per-stage durations and its outcome;
 * this surface renders that history read-only.
 */
export const OperationsView: React.FC = () => {
  const operations = useEmberStore((s) => s.operations);
  const loadingOperations = useEmberStore((s) => s.loadingOperations);
  const refreshOperations = useEmberStore((s) => s.refreshOperations);

  useEffect(() => {
    refreshOperations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const records = operations ?? [];
  const failed = records.filter((record) => record.result !== 'success').length;

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl bg-surface-raised/60 border border-DEFAULT backdrop-blur shadow-xl">
        <div className="flex items-center justify-between pb-4 border-b border-DEFAULT">
          <div>
            <h2 className="text-lg font-bold text-text-primary">Operations</h2>
            <p className="text-sm text-text-secondary mt-1">
              Durable log of download, verification and extraction runs
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-text-secondary" data-testid="operations-summary">
              {records.length} recorded · {failed} failed
            </span>
            <button
              type="button"
              onClick={refreshOperations}
              disabled={loadingOperations}
              className="px-3 py-1.5 rounded-lg bg-accent/20 border border-accent/40 text-sm font-semibold text-accent hover:bg-accent/30 disabled:opacity-50"
            >
              {loadingOperations ? 'Refreshing…' : 'Refresh'}
            </button>
          </div>
        </div>
        {records.length === 0 ? (
          <p className="pt-4 text-sm text-text-secondary" data-testid="operations-empty">
            {loadingOperations
              ? 'Loading operation history…'
              : 'No operations recorded yet. Downloads and extractions will appear here.'}
          </p>
        ) : (
          <ul className="pt-4 space-y-2" data-testid="operations-list">
            {records.map((record) => (
              <OperationRow key={record.operation_id} record={record} />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
