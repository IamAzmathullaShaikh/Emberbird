import React, { useState, useEffect, useCallback } from 'react';
import { formatBytes } from '../lib/formatters';
import { listBackupCandidates, restoreVhdxBackup } from '../lib/ipc';
import type { RestoreCandidate } from '../lib/types';
import { useEmberStore } from '../lib/store';

export const RestoreView: React.FC = () => {
  const status = useEmberStore((s) => s.wsaStatus);
  const onRestoreComplete = useEmberStore((s) => s.refreshStatus);
  const addNotification = useEmberStore((s) => s.addNotification);
  const [candidates, setCandidates] = useState<RestoreCandidate[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [, setLoading] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [resultMessage, setResultMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const fetchCandidates = useCallback(async () => {
    setLoading(true);
    try {
      const list = await listBackupCandidates();
      const valid = list.filter((c) => c.is_valid);
      setCandidates(valid);
      if (valid.length > 0 && !selectedId) {
        setSelectedId(valid[0].id);
      }
    } catch (err) {
      addNotification({
        type: 'error',
        title: 'Failed to load restore candidates',
        message: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoading(false);
    }
  }, [addNotification, selectedId]);

  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

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


  return (
    <div className="space-y-6">
      {/* Emergency Rollback Hero Card */}
      {candidates.length > 0 && (
        <div className="p-5 rounded-xl bg-gradient-to-r from-rose-950/40 via-purple-950/20 to-slate-900/50 border border-status-fail/40 shadow-lg shadow-status-fail/20 backdrop-blur space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-status-fail text-text-primary">
                  Emergency Rollback
                </span>
                <h2 className="text-sm font-bold text-text-primary">
                  Revert to Last Known Good State
                </h2>
              </div>
              <p className="text-xs text-text-secondary mt-1">
                Instantly restore snapshot <span className="font-mono text-accent font-semibold">{candidates[0].id}</span> ({new Date(candidates[0].timestamp).toLocaleString()} • {formatBytes(candidates[0].file_size_bytes)}).
              </p>
            </div>

            <button
              type="button"
              onClick={() => {
                setSelectedId(candidates[0].id);
                setShowConfirmModal(true);
              }}
              disabled={restoring || status?.is_running}
              className="px-4 py-2 rounded-lg bg-status-fail hover:bg-status-fail disabled:opacity-40 text-text-primary text-xs font-semibold shadow-md shadow-status-fail/30 transition-all whitespace-nowrap"
            >
              1-Click Emergency Rollback
            </button>
          </div>
        </div>
      )}

      {/* Restore Engine Card */}
      <div className="p-6 rounded-xl bg-surface-raised/50 border border-DEFAULT shadow-sm backdrop-blur">
        <div className="mb-4">
          <h2 className="text-base font-semibold text-text-primary">
            Container Restore & Rollback Engine
          </h2>
          <p className="text-xs text-text-secondary mt-0.5">
            Restore a previous container state from verified backup snapshots with automatic rollback protection.
          </p>
        </div>

        {/* Safety Warnings */}
        <div className="space-y-2 mb-6">
          {status?.is_running ? (
            <div className="p-3 rounded-lg bg-status-fail/10 border border-status-fail/30 text-status-fail text-xs flex items-center justify-between">
              <span>WSA is currently running. You must shut down WSA before executing a restore operation.</span>
              <span className="font-semibold px-2 py-0.5 bg-status-fail/20 rounded">Action Required</span>
            </div>
          ) : (
            <div className="p-3 rounded-lg bg-status-pass/10 border border-status-pass/30 text-status-pass text-xs flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>Container is offline. Ready for atomic restore operation.</span>
            </div>
          )}

          <div className="p-3 rounded-lg bg-surface-raised/40 border border-accent/40 text-accent text-xs flex items-start gap-2">
            <span className="font-bold">Rollback Guarantee:</span>
            <span className="text-text-secondary">
              The existing userdata.vhdx is copied to .pre_restore.bak prior to writing. If checksum verification fails, the engine automatically rolls back to your original container.
            </span>
          </div>
        </div>

        {/* Candidate Selector */}
        {candidates.length === 0 ? (
          <div className="text-center py-8 border border-dashed border-DEFAULT rounded-lg text-text-muted text-xs">
            No valid restore candidates available. Create a backup in the Backups tab first.
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">
                Select Restore Candidate:
              </label>
              <select
                value={selectedId}
                onChange={(e) => setSelectedId(e.target.value)}
                disabled={restoring}
                className="w-full bg-surface-raised border border-DEFAULT/80 rounded-lg px-3.5 py-2.5 text-xs text-text-primary focus:outline-none focus:border-accent transition-colors font-mono"
              >
                {candidates.map((c, idx) => (
                  <option key={c.id} value={c.id}>
                    {idx === 0 ? '★ [Last Known Good] ' : ''}{c.id} • {c.wsa_version} • {formatBytes(c.file_size_bytes)} ({new Date(c.timestamp).toLocaleDateString()})
                  </option>
                ))}
              </select>
            </div>

            {selectedCandidate && (
              <div className="p-4 rounded-lg bg-surface-raised/70 border border-DEFAULT space-y-3 text-xs">
                <div className="flex items-center justify-between border-b border-DEFAULT/80 pb-2">
                  <span className="font-semibold text-text-secondary">Snapshot Integrity &amp; Details</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-status-pass/20 text-status-pass border border-status-pass/30">
                    {selectedCandidate.is_valid ? 'VERIFIED HEALTHY' : 'INVALID'}
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px]">
                  <div>
                    <span className="text-text-muted block">Candidate ID:</span>
                    <span className="font-mono text-text-primary">{selectedCandidate.id}</span>
                  </div>
                  <div>
                    <span className="text-text-muted block">WSA Version:</span>
                    <span className="font-mono text-accent">{selectedCandidate.wsa_version}</span>
                  </div>
                  <div>
                    <span className="text-text-muted block">Container Size:</span>
                    <span className="font-mono text-text-primary">{formatBytes(selectedCandidate.file_size_bytes)}</span>
                  </div>
                  <div>
                    <span className="text-text-muted block">Created On:</span>
                    <span className="font-mono text-text-secondary">{new Date(selectedCandidate.timestamp).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="pt-2 border-t border-DEFAULT/80">
                  <span className="text-text-muted block mb-1">Full SHA-256 Fingerprint:</span>
                  <code className="text-text-secondary font-mono text-[10px] bg-surface-raised p-1.5 rounded block select-all break-all">
                    {selectedCandidate.sha256}
                  </code>
                </div>
                {selectedCandidate.description && (
                  <div className="text-text-secondary pt-1 border-t border-DEFAULT/80">
                    <span className="text-text-muted">Note: </span>
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
                className="px-4 py-2 rounded-lg bg-status-fail hover:bg-status-fail disabled:opacity-40 text-text-primary text-xs font-medium shadow-md shadow-status-fail/20 transition-all"
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
                ? 'bg-status-pass/10 text-status-pass border-status-pass/30'
                : 'bg-status-fail/10 text-status-fail border-status-fail/30'
            }`}
          >
            {resultMessage.text}
          </div>
        )}
      </div>

      {/* Storage Relocation Guide */}
      <div className="p-6 rounded-xl bg-surface-raised/50 border border-DEFAULT shadow-sm backdrop-blur space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-text-primary">
            Storage Relocation &amp; Multi-Drive Management
          </h3>
          <span className="text-[10px] px-2 py-0.5 rounded bg-accent/10 text-accent border border-accent/20 font-mono">
            Save Drive C: Space
          </span>
        </div>
        <p className="text-xs text-text-secondary leading-relaxed">
          WSA stores all apps and downloaded media inside <code className="font-mono text-accent">userdata.vhdx</code>. As your container grows (up to 64 GB), you can relocate it to a secondary SSD (e.g. <code className="font-mono text-status-pass">D:\WSA_Storage</code>) without reinstalling using an NTFS directory junction:
        </p>
        <div className="p-3 bg-surface-raised rounded-lg border border-DEFAULT font-mono text-[11px] text-text-secondary space-y-1 select-all overflow-x-auto">
          <div className="text-text-muted"># 1. Terminate running WSA processes</div>
          <div>Stop-Process -Name &quot;WsaClient&quot; -Force -ErrorAction SilentlyContinue</div>
          <div className="text-text-muted mt-2"># 2. Move LocalCache folder to your target secondary drive</div>
          <div>Move-Item &quot;$env:LOCALAPPDATA\Packages\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\LocalCache&quot; &quot;D:\WSA_Storage&quot;</div>
          <div className="text-text-muted mt-2"># 3. Create NTFS Directory Junction pointing back to original path</div>
          <div>New-Item -ItemType Junction -Path &quot;$env:LOCALAPPDATA\Packages\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\LocalCache&quot; -Target &quot;D:\WSA_Storage&quot;</div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && selectedCandidate && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-surface-raised border border-DEFAULT rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-status-fail flex items-center gap-2">
              Confirm Container Restore
            </h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Are you sure you want to restore snapshot{' '}
              <span className="font-mono text-accent font-semibold">{selectedCandidate.id}</span>?
            </p>
            <p className="text-xs text-status-warn/90 bg-status-warn/10 border border-status-warn/30 p-2.5 rounded-lg">
              This will overwrite your existing Android apps, accounts, and internal storage with the state from {new Date(selectedCandidate.timestamp).toLocaleString()}.
            </p>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                className="px-3.5 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-raised text-xs text-text-secondary transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteRestore}
                className="px-4 py-1.5 rounded-lg bg-status-fail hover:bg-status-fail text-text-primary text-xs font-medium transition-colors shadow-md shadow-status-fail/20"
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
