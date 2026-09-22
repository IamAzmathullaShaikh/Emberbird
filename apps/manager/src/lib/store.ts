import { create } from 'zustand';
import {
  detectWsaStatus,
  checkForUpdates as fetchUpdates,
  getLifecycleReport,
  getOperationHistory,
} from './ipc';
import { normalizeStatusPayload } from './state';
import type {
  WsaStatus,
  UpdateStatus,
  StageProgress,
  NavigationTab,
  LifecycleReport,
  OperationRecord,
} from './types';

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
  /** The reconciled runtime lifecycle (PH-02 engine), or null while loading. */
  lifecycle: LifecycleReport | null;
  /** Durable staging-operation history (PH-45), or null until first load. */
  operations: OperationRecord[] | null;
  loadingOperations: boolean;

  // ── Actions ───────────────────────────────────────────────────────────────
  /** Probe the host WSA state. Surfaces errors as notifications — never swallows them. */
  refreshStatus: () => Promise<void>;
  /** Pull the reconciled runtime lifecycle report. */
  refreshLifecycle: () => Promise<void>;
  /** Pull the durable staging-operation history (PH-45). */
  refreshOperations: () => Promise<void>;
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
  lifecycle: null,
  operations: null,
  loadingOperations: false,

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
    // The lifecycle reconciliation rides the same cadence as detection: every
    // caller that refreshes install truth also refreshes lifecycle truth.
    await get().refreshLifecycle();
  },

  refreshLifecycle: async () => {
    try {
      const res = await getLifecycleReport();
      set({ lifecycle: res });
    } catch (err) {
      // The lifecycle engine refused or the IPC bridge failed: the surface
      // must not present a guessed state, so lifecycle stays null and the
      // badge keeps rendering "Checking lifecycle…" while a notification
      // carries the failure (Zero-Mock law).
      const message = err instanceof Error ? err.message : String(err);
      get().addNotification({
        type: 'error',
        title: 'Lifecycle reconciliation failed',
        message,
        durationMs: 7000,
      });
    }
  },

  refreshOperations: async () => {
    set({ loadingOperations: true });
    try {
      const res = await getOperationHistory(100);
      set({ operations: res, loadingOperations: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      set({ loadingOperations: false });
      get().addNotification({
        type: 'error',
        title: 'Operation history unavailable',
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
