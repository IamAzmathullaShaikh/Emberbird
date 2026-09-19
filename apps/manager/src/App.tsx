import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { StatusCard } from './components/StatusCard';
import { ReleaseCard } from './components/ReleaseCard';
import { BackupView } from './components/BackupView';
import { RestoreView } from './components/RestoreView';
import { UpdateView } from './components/UpdateView';
import { LicensesView } from './components/LicensesView';
import { DoctorView } from './components/DoctorView';
import { detectWsaStatus, checkForUpdates } from './lib/ipc';
import { normalizeStatusPayload } from './lib/state';
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
      setStatus(normalizeStatusPayload(res));
    } catch (err) {
      console.error('Failed to detect WSA status:', err);
      setStatus(normalizeStatusPayload(null));
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
    <div className="flex flex-col h-screen bg-ember-obsidian text-slate-100 font-sans selection:bg-ember-glow/30">
      <Header
        status={status}
        onRefresh={refreshStatus}
        loading={loadingStatus}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
      />

      <main className="flex-1 overflow-y-auto p-6 max-w-6xl mx-auto w-full space-y-6">
        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
            {/* Primary Status Widget - Large Span */}
            <div className="lg:col-span-8 space-y-6">
               <StatusCard status={status} onRefresh={refreshStatus} />
            </div>

            {/* Secondary Intelligence Widget - Side Span */}
            <div className="lg:col-span-4 space-y-6">
               <ReleaseCard
                 status={status}
                 updateStatus={updateStatus}
                 onCheckUpdates={handleCheckUpdates}
                 checking={checkingUpdates}
               />
            </div>
          </div>
        )}

        {activeTab === 'updates' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            <UpdateView onUpgradeSuccess={refreshStatus} />
          </div>
        )}

        {activeTab === 'backups' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            <BackupView status={status} />
          </div>
        )}

        {activeTab === 'restore' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            <RestoreView status={status} onRestoreComplete={refreshStatus} />
          </div>
        )}

        {activeTab === 'doctor' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            <DoctorView />
          </div>
        )}

        {activeTab === 'licenses' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            <LicensesView />
          </div>
        )}

        <footer className="p-4 rounded-2xl bg-ember-charcoal/30 border border-ember-ash/10 flex items-center justify-between text-[10px] text-ember-ash uppercase tracking-widest font-mono">
          <span>Emberbird Engine • Lifecycle Platform</span>
          <span>Obsidian Edition • Architecture v5.0</span>
        </footer>
      </main>
    </div>
  );
};

export default App;