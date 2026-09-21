import React from 'react';

type AlertVariant = 'info' | 'success' | 'warn' | 'error';

const ALERT_STYLES: Record<AlertVariant, { container: string; label: string }> = {
  info:    { container: 'bg-accent/5 border-accent/20 text-text-secondary',         label: 'Information' },
  success: { container: 'bg-status-pass/5 border-status-pass/20 text-text-secondary', label: 'Success' },
  warn:    { container: 'bg-status-warn/5 border-status-warn/20 text-text-secondary', label: 'Warning' },
  error:   { container: 'bg-status-fail/5 border-status-fail/20 text-text-secondary', label: 'Error' },
};

interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({ variant = 'info', title, children, className = '' }) => {
  const styles = ALERT_STYLES[variant];
  return (
    <div role="alert" aria-label={styles.label} className={`p-3.5 rounded-xl border ${styles.container} ${className}`}>
      {title && <div className="font-semibold text-sm mb-1">{title}</div>}
      <div className="text-[13px] leading-relaxed">{children}</div>
    </div>
  );
};
