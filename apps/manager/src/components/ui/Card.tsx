import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  raised?: boolean;
  as?: React.ElementType;
}

export const Card: React.FC<CardProps> = ({ children, className = '', raised = false, as: Component = 'div' }) => (
  <Component className={`rounded-2xl border ${raised ? 'bg-surface-raised border-border-DEFAULT' : 'bg-surface-DEFAULT border-border-DEFAULT'} ${className}`}>
    {children}
  </Component>
);
