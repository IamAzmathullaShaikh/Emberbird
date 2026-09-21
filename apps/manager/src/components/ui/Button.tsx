import React from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:   'bg-accent hover:bg-accent-hover text-white shadow-md shadow-accent/20 disabled:opacity-50',
  secondary: 'bg-surface-raised hover:bg-surface-raised border border-border-DEFAULT text-text-secondary disabled:opacity-50',
  ghost:     'text-text-secondary hover:text-text-primary hover:bg-surface-raised/50 disabled:opacity-50',
  danger:    'bg-status-fail/10 hover:bg-status-fail/20 text-status-fail border border-status-fail/30 disabled:opacity-50',
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: 'px-2.5 py-1.5 text-xs font-medium rounded-lg',
  md: 'px-4 py-2 text-sm font-semibold rounded-xl',
  lg: 'px-6 py-3 text-sm font-bold rounded-xl',
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({ variant = 'primary', size = 'md', loading = false, children, className = '', disabled, ...props }) => (
  <button type="button" disabled={disabled || loading} className={`inline-flex items-center gap-2 transition-all duration-150 ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`} {...props}>
    {loading && <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" aria-hidden />}
    {children}
  </button>
);
