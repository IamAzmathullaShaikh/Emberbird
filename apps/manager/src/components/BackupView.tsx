import React, { useState, useEffect } from 'react';
import {
  createVhdxBackup,
  listBackupCandidates,
  pruneBackups,
} from '../lib/ipc';
import type { RestoreCandidate, WsaStatus } from '../lib/types';

interface BackupViewProps {
  status: WsaStatus | null;
}

export const BackupView: React.FC<BackupViewProps> = ({ status }) => {
  const [candidates, setCandidates] = useState<RestoreCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [note, setNote] = useState('');
  const [actionMessage, setActionMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const list = await listBackupCandidates();
      setCandidates(list);
    } catch (err) {
      console.error('Failed to load backup candidates:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, []);

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

  const formatBytes = (bytes: number) => {
    if (bytes >= 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Create Backup Card */}
      <div className="p-6 rounded-xl bg-slate-900/50 border border-slate-800 shadow-sm backdrop-blur">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-base font-semibold text-white">
              VHDX Snapshot Engine
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Creates verified cold snapshots of your Android userdata container
              with streaming SHA-256 calculation.
            </p>
          </div>
          {status?.is_running && (
            <div className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
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
            className="flex-1 w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
          <button
            type="submit"
            disabled={creating}
            className="w-full sm:w-auto px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium shadow-md shadow-indigo-600/20 transition-all whitespace-nowrap"
          >
            {creating ? 'Creating Snapshot...' : 'Create Snapshot'}
          </button>
        </form>

        {actionMessage && (
          <div
            className={`mt-4 p-3 rounded-lg text-xs border ${
              actionMessage.type === 'success'
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
            }`}
          >
            {actionMessage.text}
          </div>
        )}
      </div>

      {/* Backup Registry History */}
      <div className="p-6 rounded-xl bg-slate-900/50 border border-slate-800 shadow-sm backdrop-blur">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white">
              Backup Registry & Retention
            </h3>
            <p className="text-xs text-slate-400">
              {candidates.length} candidate snapshot(s) registered on disk.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handlePrune}
              disabled={loading || candidates.length <= 3}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 border border-slate-700 text-xs text-slate-300 transition-colors"
            >
              Prune Older (&gt;3)
            </button>
            <button
              type="button"
              onClick={fetchCandidates}
              disabled={loading}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 border border-slate-700 text-xs text-slate-300 transition-colors"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {candidates.length === 0 ? (
          <div className="text-center py-10 border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs">
            No backup snapshots registered yet. Create a snapshot above to
            protect your container data.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-mono text-[10px]">
                <tr>
                  <th className="py-2.5 px-3">Snapshot ID / Note</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">WSA Version</th>
                  <th className="py-2.5 px-3">Size</th>
                  <th className="py-2.5 px-3">SHA-256 Digest</th>
                  <th className="py-2.5 px-3">Integrity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {candidates.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-3">
                      <div className="font-mono text-slate-200 font-medium">
                        {c.id}
                      </div>
                      {c.description && (
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          {c.description}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                      {new Date(c.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-indigo-300">
                      {c.wsa_version}
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px]">
                      {formatBytes(c.file_size_bytes)}
                    </td>
                    <td className="py-3 px-3 font-mono text-[10px] text-slate-400">
                      <span title={c.sha256}>
                        {c.sha256.slice(0, 12)}...{c.sha256.slice(-6)}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      {c.is_valid ? (
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-medium">
                          Verified Valid
                        </span>
                      ) : (
                        <span
                          title={c.validation_error || 'Invalid'}
                          className="px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 text-[10px] font-medium"
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
