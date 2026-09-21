import React from 'react';

interface SpinnerProps { size?: 'sm' | 'md' | 'lg'; className?: string; label?: string; }
const SIZE_MAP = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8' };

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className = '', label }) => (
  <span role="status" aria-label={label ?? 'Loading'} className={`inline-block ${SIZE_MAP[size]} border-2 border-current border-t-transparent rounded-full animate-spin ${className}`} />
);
