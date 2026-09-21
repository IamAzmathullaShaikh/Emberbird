import React, { useState, useEffect, useCallback } from 'react';
import { formatBytes } from '../lib/formatters';
import {
  createVhdxBackup,
  listBackupCandidates,
  pruneBackups,
} from '../lib/ipc';
import type { RestoreCandidate } from '../lib/types';
import { useEmberStore } from '../lib/store';

export const BackupView: React.FC = () => {
  const status = useEmberStore((s) => s.wsaStatus);
  const addNotification = useEmberStore((s) => s.addNotification);
  const [candidates, setCandidates] = useState<RestoreCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [note, setNote] = useState('');
  const [actionMessage, setActionMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const fetchCandidates = useCallback(async () => {
    setLoading(true);
    try {
      const list = await listBackupCandidates();
      setCandidates(list);
    } catch (err) {
      addNotification({
        type: 'error',
        title: 'Failed to load backup candidates',
        message: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoading(false);
    }
  }, [addNotification]);

  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  const handleCreateBackup = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setActionMessage(null);
    try {
      const res = await createVhdxBackup(note.trim() || undefined);
      if (res.success && res.metadata) {
        setActionMessage({
          type: 'success',
          text: `Backup snapshot '${res.metadata.id}' completed successfully (${(
            res.metadata.file_size_bytes /
            (1024 * 1024 * 1024)
          ).toFixed(2)} GB).`,
        });
        setNote('');
        await fetchCandidates();
      } else {
        setActionMessage({
          type: 'error',
          text: res.error || 'Backup failed.',
        });
      }
    } catch (err) {
      setActionMessage({
        type: 'error',
        text: String(err),
      });
    } finally {
      setCreating(false);
    }
  };

  const handlePrune = async () => {
    if (
      !window.confirm(
        'Retain the 3 most recent backups and delete older snapshots?'
      )
    ) {
      return;
    }
    setLoading(true);
    setActionMessage(null);
    try {
      const pruned = await pruneBackups(3);
      setActionMessage({
        type: 'success',
        text: `Pruned ${pruned.length} older backup snapshot(s).`,
      });
      await fetchCandidates();
    } catch (err) {
      setActionMessage({
        type: 'error',
        text: `Prune failed: ${String(err)}`,
      });
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="space-y-6">
      {/* Create Backup Card */}
      <div className="p-6 rounded-xl bg-surface-raised/50 border border-DEFAULT shadow-sm backdrop-blur">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-base font-semibold text-text-primary">
              VHDX Snapshot Engine
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Creates verified cold snapshots of your Android userdata container
              with streaming SHA-256 calculation.
            </p>
          </div>
          {status?.is_running && (
            <div className="px-3 py-1.5 rounded-lg bg-status-warn/10 border border-status-warn/30 text-status-warn text-xs flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-status-warn animate-pulse" />
              <span>WSA running: will be gracefully shut down for snapshot</span>
            </div>
          )}
        </div>

        <form
          onSubmit={handleCreateBackup}
          className="flex flex-col sm:flex-row items-center gap-3"
        >
          <input
            type="text"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Optional snapshot description (e.g. Prior to Magisk upgrade)..."
            className="flex-1 w-full bg-surface-raised border border-DEFAULT/80 rounded-lg px-3.5 py-2 text-xs text-text-primary placeholder-text-muted focus:outline-none focus:border-accent transition-colors"
          />
          <button
            type="submit"
            disabled={creating}
            className="w-full sm:w-auto px-4 py-2 rounded-lg bg-accent hover:bg-accent disabled:opacity-50 text-text-primary text-xs font-medium shadow-md shadow-accent/20 transition-all whitespace-nowrap"
          >
            {creating ? 'Creating Snapshot...' : 'Create Snapshot'}
          </button>
        </form>

        {actionMessage && (
          <div
            className={`mt-4 p-3 rounded-lg text-xs border ${
              actionMessage.type === 'success'
                ? 'bg-status-pass/10 text-status-pass border-status-pass/30'
                : 'bg-status-fail/10 text-status-fail border-status-fail/30'
            }`}
          >
            {actionMessage.text}
          </div>
        )}
      </div>

      {/* Backup Registry History */}
      <div className="p-6 rounded-xl bg-surface-raised/50 border border-DEFAULT shadow-sm backdrop-blur">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-text-primary">
              Backup Registry & Retention
            </h3>
            <p className="text-xs text-text-secondary">
              {candidates.length} candidate snapshot(s) registered on disk.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handlePrune}
              disabled={loading || candidates.length <= 3}
              className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-raised disabled:opacity-40 border border-DEFAULT text-xs text-text-secondary transition-colors"
            >
              Prune Older (&gt;3)
            </button>
            <button
              type="button"
              onClick={fetchCandidates}
              disabled={loading}
              className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-raised disabled:opacity-50 border border-DEFAULT text-xs text-text-secondary transition-colors"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {candidates.length === 0 ? (
          <div className="text-center py-10 border border-dashed border-DEFAULT rounded-lg text-text-muted text-xs">
            No backup snapshots registered yet. Create a snapshot above to
            protect your container data.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-text-secondary">
              <thead className="bg-surface-raised/60 text-text-secondary border-b border-DEFAULT uppercase tracking-wider font-mono text-[10px]">
                <tr>
                  <th className="py-2.5 px-3">Snapshot ID / Note</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">WSA Version</th>
                  <th className="py-2.5 px-3">Size</th>
                  <th className="py-2.5 px-3">SHA-256 Digest</th>
                  <th className="py-2.5 px-3">Integrity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-DEFAULT/60">
                {candidates.map((c) => (
                  <tr key={c.id} className="hover:bg-surface-raised/30 transition-colors">
                    <td className="py-3 px-3">
                      <div className="font-mono text-text-primary font-medium">
                        {c.id}
                      </div>
                      {c.description && (
                        <div className="text-[11px] text-text-secondary mt-0.5">
                          {c.description}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-3 text-text-secondary font-mono text-[11px]">
                      {new Date(c.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-accent">
                      {c.wsa_version}
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px]">
                      {formatBytes(c.file_size_bytes)}
                    </td>
                    <td className="py-3 px-3 font-mono text-[10px] text-text-secondary">
                      <span title={c.sha256}>
                        {c.sha256.slice(0, 12)}...{c.sha256.slice(-6)}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      {c.is_valid ? (
                        <span className="px-2 py-0.5 rounded-full bg-status-pass/10 text-status-pass border border-status-pass/30 text-[10px] font-medium">
                          Verified Valid
                        </span>
                      ) : (
                        <span
                          title={c.validation_error || 'Invalid'}
                          className="px-2 py-0.5 rounded-full bg-status-fail/10 text-status-fail border border-status-fail/30 text-[10px] font-medium"
                        >
                          Corrupted
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
