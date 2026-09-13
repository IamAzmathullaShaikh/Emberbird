import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { StatusCard } from './components/StatusCard';
import { ReleaseCard } from './components/ReleaseCard';
import { BackupView } from './components/BackupView';
import { RestoreView } from './components/RestoreView';
import { UpdateView } from './components/UpdateView';
import { detectWsaStatus, checkForUpdates } from './lib/ipc';
import type { WsaStatus, UpdateStatus, NavigationTab } from './lib/types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>('dashboard');
  const [status, setStatus] = useState<WsaStatus | null>(null);
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [checkingUpdates, setCheckingUpdates] = useState(false);

  const refreshStatus = async () => {
    setLoadingStatus(true);
    try {
      const res = await detectWsaStatus();
      setStatus(res);
    } catch (err) {
      console.error('Failed to detect WSA status:', err);
    } finally {
      setLoadingStatus(false);
    }
  };

  const handleCheckUpdates = async () => {
    setCheckingUpdates(true);
    try {
      const res = await checkForUpdates();
      setUpdateStatus(res);
    } catch (err) {
      console.error('Failed to check updates:', err);
    } finally {
      setCheckingUpdates(false);
    }
  };

  useEffect(() => {
    refreshStatus();
    handleCheckUpdates();
  }, []);

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500/30">
      <Header
        status={status}
        onRefresh={refreshStatus}
        loading={loadingStatus}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
      />

      <main className="flex-1 overflow-y-auto p-6 max-w-5xl mx-auto w-full space-y-6">
        {activeTab === 'dashboard' && (
          <>
            <StatusCard status={status} />
            <ReleaseCard
              updateStatus={updateStatus}
              onCheckUpdates={handleCheckUpdates}
              checking={checkingUpdates}
            />
          </>
        )}

        {activeTab === 'updates' && (
          <UpdateView onUpgradeSuccess={refreshStatus} />
        )}

        {activeTab === 'backups' && (
          <BackupView status={status} />
        )}

        {activeTab === 'restore' && (
          <RestoreView status={status} onRestoreComplete={refreshStatus} />
        )}

        <div className="p-4 rounded-xl bg-slate-900/30 border border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
          <span>WSABuilds Desktop Subsystem Lifecycle Engine</span>
          <span>Sprint 7 Deliverable • Architecture v5.0</span>
        </div>
      </main>
    </div>
  );
};

export default App;
