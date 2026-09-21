import React from 'react';

type BadgeVariant = 'pass' | 'warn' | 'fail' | 'unknown' | 'accent' | 'default';

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  pass:    'bg-status-pass/10 text-status-pass border border-status-pass/20',
  warn:    'bg-status-warn/10 text-status-warn border border-status-warn/20',
  fail:    'bg-status-fail/10 text-status-fail border border-status-fail/20',
  unknown: 'bg-surface-raised text-text-muted border border-border-DEFAULT',
  accent:  'bg-accent/10 text-accent border border-accent/20',
  default: 'bg-surface-raised text-text-secondary border border-border-DEFAULT',
};

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  className?: string;
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'default', size = 'sm', className = '', dot = false }) => (
  <span className={`inline-flex items-center gap-1.5 rounded-md font-medium ${size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs'} ${VARIANT_CLASSES[variant]} ${className}`}>
    {dot && <span className={`w-1.5 h-1.5 rounded-full ${variant === 'pass' ? 'bg-status-pass' : variant === 'warn' ? 'bg-status-warn' : variant === 'fail' ? 'bg-status-fail' : variant === 'accent' ? 'bg-accent' : 'bg-text-muted'}`} />}
    {children}
  </span>
);
