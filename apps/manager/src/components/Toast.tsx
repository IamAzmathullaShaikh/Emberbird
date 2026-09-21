import React, { useEffect, useRef } from 'react';

export type NotificationType = 'success' | 'warning' | 'error' | 'info';

export interface ToastNotification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  durationMs?: number;
}

interface ToastProps {
  notifications: ToastNotification[];
  onDismiss: (id: string) => void;
}

const TYPE_STYLES: Record<NotificationType, { border: string; icon: string; iconColor: string }> = {
  success: { border: 'border-status-pass/40', icon: '✓', iconColor: 'text-status-pass' },
  warning: { border: 'border-status-warn/40', icon: '⚠', iconColor: 'text-status-warn' },
  error:   { border: 'border-status-fail/40', icon: '✕', iconColor: 'text-status-fail' },
  info:    { border: 'border-border-focus/40', icon: 'i', iconColor: 'text-accent' },
};

const ToastItem: React.FC<{ notification: ToastNotification; onDismiss: (id: string) => void }> = ({
  notification,
  onDismiss,
}) => {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const duration = notification.durationMs ?? 5000;

  useEffect(() => {
    if (duration > 0) {
      timerRef.current = setTimeout(() => onDismiss(notification.id), duration);
    }
    return () => {
      if (timerRef.current !== null) clearTimeout(timerRef.current);
    };
  }, [notification.id, duration, onDismiss]);

  const styles = TYPE_STYLES[notification.type];

  return (
    <div
      role={notification.type === 'error' || notification.type === 'warning' ? 'alert' : 'status'}
      className={`flex items-start gap-3 rounded-xl border ${
        styles.border
      } bg-surface-raised/95 backdrop-blur-sm px-4 py-3 shadow-lg min-w-[280px] max-w-[380px] animate-in slide-in-from-right-4 fade-in duration-200`}
    >
      <span className={`text-sm font-bold flex-shrink-0 mt-0.5 ${styles.iconColor}`}>
        {styles.icon}
      </span>
      <div className="flex flex-col gap-0.5 flex-1 min-w-0">
        <p className="text-xs font-semibold text-text-primary truncate">{notification.title}</p>
        {notification.message && (
          <p className="text-xs text-text-secondary line-clamp-2">{notification.message}</p>
        )}
      </div>
      <button
        type="button"
        onClick={() => onDismiss(notification.id)}
        className="text-text-muted hover:text-text-primary transition-colors flex-shrink-0 text-xs leading-none"
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  );
};

export const Toast: React.FC<ToastProps> = ({ notifications, onDismiss }) => {
  if (notifications.length === 0) return null;

  return (
    <div
      role="region"
      className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 items-end"
      aria-label="Notifications"
    >
      {notifications.slice(-4).map((n) => (
        <ToastItem key={n.id} notification={n} onDismiss={onDismiss} />
      ))}
    </div>
  );
};
