import { create } from 'zustand';
import { detectWsaStatus, checkForUpdates as fetchUpdates } from './ipc';
import { normalizeStatusPayload } from './state';
import type { WsaStatus, UpdateStatus, StageProgress, NavigationTab } from './types';

export type NotificationType = 'success' | 'warning' | 'error' | 'info';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  /** Auto-dismiss after this many ms. Default: 5000. Set 0 to require manual dismiss. */
  durationMs?: number;
}

export interface EmberStore {
  // ── State ─────────────────────────────────────────────────────────────────
  wsaStatus: WsaStatus | null;
  updateStatus: UpdateStatus | null;
  stageProgress: StageProgress | null;
  activeTab: NavigationTab;
  loadingStatus: boolean;
  checkingUpdates: boolean;
  notifications: Notification[];

  // ── Actions ───────────────────────────────────────────────────────────────
  /** Probe the host WSA state. Surfaces errors as notifications — never swallows them. */
  refreshStatus: () => Promise<void>;
  /** Check for WSA updates from the registry. */
  checkForUpdates: () => Promise<void>;
  /** Navigate to a tab. */
  setActiveTab: (tab: NavigationTab) => void;
  /** Update download/staging progress (called by download IPC listeners). */
  setStageProgress: (progress: StageProgress | null) => void;
  /** Add a user-visible notification. */
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  /** Dismiss a notification by id. */
  dismissNotification: (id: string) => void;
}

let notifCounter = 0;

export const useEmberStore = create<EmberStore>((set, get) => ({
  // ── Initial state ──────────────────────────────────────────────────────────
  wsaStatus: null,
  updateStatus: null,
  stageProgress: null,
  activeTab: 'dashboard',
  loadingStatus: false,
  checkingUpdates: false,
  notifications: [],

  // ── Actions ───────────────────────────────────────────────────────────────
  refreshStatus: async () => {
    set({ loadingStatus: true });
    try {
      const res = await detectWsaStatus();
      set({ wsaStatus: normalizeStatusPayload(res), loadingStatus: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      set({ wsaStatus: normalizeStatusPayload(null), loadingStatus: false });
      get().addNotification({
        type: 'error',
        title: 'Status detection failed',
        message,
        durationMs: 7000,
      });
    }
  },

  checkForUpdates: async () => {
    set({ checkingUpdates: true });
    try {
      const res = await fetchUpdates();
      set({ updateStatus: res, checkingUpdates: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      set({ checkingUpdates: false });
      get().addNotification({
        type: 'warning',
        title: 'Update check failed',
        message,
      });
    }
  },

  setActiveTab: (tab) => set({ activeTab: tab }),

  setStageProgress: (progress) => set({ stageProgress: progress }),

  addNotification: (notification) => {
    const id = `notif-${++notifCounter}-${Date.now()}`;
    set((state) => ({
      notifications: [...state.notifications.slice(-3), { ...notification, id }],
    }));
  },

  dismissNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}));
