import React, { useEffect } from 'react';
import { Header } from './components/Header';
import { StatusCard } from './components/StatusCard';
import { ReleaseCard } from './components/ReleaseCard';
import { BackupView } from './components/BackupView';
import { RestoreView } from './components/RestoreView';
import { UpdateView } from './components/UpdateView';
import { LicensesView } from './components/LicensesView';
import { DoctorView } from './components/DoctorView';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Toast } from './components/Toast';
import { useEmberStore } from './lib/store';

export const App: React.FC = () => {
  const activeTab = useEmberStore((s) => s.activeTab);
  const refreshStatus = useEmberStore((s) => s.refreshStatus);
  const checkForUpdates = useEmberStore((s) => s.checkForUpdates);
  const notifications = useEmberStore((s) => s.notifications);
  const dismissNotification = useEmberStore((s) => s.dismissNotification);

  useEffect(() => {
    refreshStatus();
    checkForUpdates();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex flex-col h-screen bg-ember-obsidian text-text-primary font-sans selection:bg-ember-glow/30">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-accent focus:text-white focus:rounded-lg focus:text-sm focus:font-semibold"
      >
        Skip to main content
      </a>
      <Header />

      <main id="main-content" role="main" className="flex-1 overflow-y-auto p-6 max-w-6xl mx-auto w-full space-y-6">
        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
            <div className="lg:col-span-8 space-y-6">
              <ErrorBoundary label="Dashboard">
                <StatusCard />
              </ErrorBoundary>
            </div>
            <div className="lg:col-span-4 space-y-6">
              <ErrorBoundary label="Release Info">
                <ReleaseCard />
              </ErrorBoundary>
            </div>
          </div>
        )}

        {activeTab === 'updates' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            <ErrorBoundary label="Updates">
              <UpdateView />
            </ErrorBoundary>
          </div>
        )}

        {activeTab === 'backups' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            <ErrorBoundary label="Backups">
              <BackupView />
            </ErrorBoundary>
          </div>
        )}

        {activeTab === 'restore' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            <ErrorBoundary label="Restore">
              <RestoreView />
            </ErrorBoundary>
          </div>
        )}

        {activeTab === 'doctor' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            <ErrorBoundary label="Doctor">
              <DoctorView />
            </ErrorBoundary>
          </div>
        )}

        {activeTab === 'licenses' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            <ErrorBoundary label="Licenses">
              <LicensesView />
            </ErrorBoundary>
          </div>
        )}

        <footer className="p-4 rounded-2xl bg-ember-charcoal/30 border border-ember-ash/10 flex items-center justify-between text-[10px] text-ember-ash uppercase tracking-widest font-mono">
          <span>Emberbird Engine • Lifecycle Platform</span>
          <span>Obsidian Edition • Architecture v5.0</span>
        </footer>
      </main>

      <Toast notifications={notifications} onDismiss={dismissNotification} />
    </div>
  );
};

export default App;