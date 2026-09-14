import React, { useState, useEffect } from 'react';
import { listBackupCandidates, restoreVhdxBackup } from '../lib/ipc';
import type { RestoreCandidate, WsaStatus } from '../lib/types';

interface RestoreViewProps {
  status: WsaStatus | null;
  onRestoreComplete?: () => void;
}

export const RestoreView: React.FC<RestoreViewProps> = ({ status, onRestoreComplete }) => {
  const [candidates, setCandidates] = useState<RestoreCandidate[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [, setLoading] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [resultMessage, setResultMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const list = await listBackupCandidates();
      const valid = list.filter((c) => c.is_valid);
      setCandidates(valid);
      if (valid.length > 0 && !selectedId) {
        setSelectedId(valid[0].id);
      }
    } catch (err) {
      console.error('Failed to load restore candidates:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, []);

  const selectedCandidate = candidates.find((c) => c.id === selectedId);

  const handleExecuteRestore = async () => {
    if (!selectedCandidate) return;
    setShowConfirmModal(false);
    setRestoring(true);
    setResultMessage(null);

    try {
      const res = await restoreVhdxBackup(selectedCandidate.id);
      if (res.success) {
        setResultMessage({
          type: 'success',
          text: `Snapshot '${res.candidate_id}' restored successfully. Integrity verified (${res.restored_sha256.slice(0, 12)}...).`,
        });
        if (onRestoreComplete) onRestoreComplete();
      } else {
        setResultMessage({
          type: 'error',
          text: res.message || 'Restore failed.',
        });
      }
    } catch (err) {
      setResultMessage({
        type: 'error',
        text: `Restore execution error: ${String(err)}`,
      });
    } finally {
      setRestoring(false);
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
      {/* Restore Engine Card */}
      <div className="p-6 rounded-xl bg-slate-900/50 border border-slate-800 shadow-sm backdrop-blur">
        <div className="mb-4">
          <h2 className="text-base font-semibold text-white">
            Container Restore & Rollback Engine
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Restore a previous container state from verified backup snapshots with automatic rollback protection.
          </p>
        </div>

        {/* Safety Warnings */}
        <div className="space-y-2 mb-6">
          {status?.is_running ? (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between">
              <span>WSA is currently running. You must shut down WSA before executing a restore operation.</span>
              <span className="font-semibold px-2 py-0.5 bg-rose-500/20 rounded">Action Required</span>
            </div>
          ) : (
            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>Container is offline. Ready for atomic restore operation.</span>
            </div>
          )}

          <div className="p-3 rounded-lg bg-indigo-950/40 border border-indigo-800/40 text-indigo-300 text-xs flex items-start gap-2">
            <span className="font-bold">Rollback Guarantee:</span>
            <span className="text-slate-300">
              The existing userdata.vhdx is copied to .pre_restore.bak prior to writing. If checksum verification fails, the engine automatically rolls back to your original container.
            </span>
          </div>
        </div>

        {/* Candidate Selector */}
        {candidates.length === 0 ? (
          <div className="text-center py-8 border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs">
            No valid restore candidates available. Create a backup in the Backups tab first.
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Select Restore Candidate:
              </label>
              <select
                value={selectedId}
                onChange={(e) => setSelectedId(e.target.value)}
                disabled={restoring}
                className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3.5 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 transition-colors font-mono"
              >
                {candidates.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.id} • {c.wsa_version} • {formatBytes(c.file_size_bytes)} ({new Date(c.timestamp).toLocaleDateString()})
                  </option>
                ))}
              </select>
            </div>

            {selectedCandidate && (
              <div className="p-4 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2 text-xs">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px]">
                  <div>
                    <span className="text-slate-500 block">Candidate ID:</span>
                    <span className="font-mono text-slate-200">{selectedCandidate.id}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">WSA Version:</span>
                    <span className="font-mono text-indigo-300">{selectedCandidate.wsa_version}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Container Size:</span>
                    <span className="font-mono text-slate-200">{formatBytes(selectedCandidate.file_size_bytes)}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">SHA-256 Digest:</span>
                    <span className="font-mono text-slate-400" title={selectedCandidate.sha256}>
                      {selectedCandidate.sha256.slice(0, 10)}...{selectedCandidate.sha256.slice(-4)}
                    </span>
                  </div>
                </div>
                {selectedCandidate.description && (
                  <div className="text-slate-400 pt-1 border-t border-slate-800/80">
                    <span className="text-slate-500">Note: </span>
                    {selectedCandidate.description}
                  </div>
                )}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowConfirmModal(true)}
                disabled={restoring || status?.is_running || !selectedCandidate}
                className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:opacity-40 text-white text-xs font-medium shadow-md shadow-rose-600/20 transition-all"
              >
                {restoring ? 'Restoring Container...' : 'Restore Selected Snapshot'}
              </button>
            </div>
          </div>
        )}

        {resultMessage && (
          <div
            className={`mt-4 p-3 rounded-lg text-xs border ${
              resultMessage.type === 'success'
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
            }`}
          >
            {resultMessage.text}
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && selectedCandidate && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-rose-400 flex items-center gap-2">
              Confirm Container Restore
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to restore snapshot{' '}
              <span className="font-mono text-indigo-300 font-semibold">{selectedCandidate.id}</span>?
            </p>
            <p className="text-xs text-amber-400/90 bg-amber-500/10 border border-amber-500/30 p-2.5 rounded-lg">
              This will overwrite your existing Android apps, accounts, and internal storage with the state from {new Date(selectedCandidate.timestamp).toLocaleString()}.
            </p>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteRestore}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium transition-colors shadow-md shadow-rose-600/20"
              >
                Confirm &amp; Restore
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
