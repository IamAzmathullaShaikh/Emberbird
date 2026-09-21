import React from 'react';

interface AdvancedInstallFallbackProps {
  manualPath: string;
  onPathChange: (value: string) => void;
  show: boolean;
  onToggle: () => void;
  onSubmit: () => void;
  disabled: boolean;
}

/**
 * Advanced fallback: register an already-extracted local package by path.
 * Kept collapsed by default — the registry loop is the primary path, this is
 * for users who built or extracted a package themselves.
 */
export const AdvancedInstallFallback: React.FC<AdvancedInstallFallbackProps> = ({
  manualPath,
  onPathChange,
  show,
  onToggle,
  onSubmit,
  disabled,
}) => (
  <div className="pt-1">
    <button
      type="button"
      onClick={onToggle}
      className="text-[11px] text-text-muted hover:text-text-secondary transition-colors"
    >
      {show ? '▾' : '▸'} Advanced: install from a local extracted package
    </button>
    {show && (
      <div className="mt-2 space-y-2">
        <input
          type="text"
          value={manualPath}
          onChange={(e) => onPathChange(e.target.value)}
          placeholder="C:\Path\To\Extracted_WSA_Folder"
          className="w-full px-3 py-2 bg-surface-raised border border-border-DEFAULT rounded-lg text-xs font-mono text-white placeholder-text-muted focus:outline-none focus:border-accent-DEFAULT"
        />
        <button
          type="button"
          onClick={onSubmit}
          disabled={disabled}
          className="px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-surface-raised disabled:opacity-50 text-text-primary text-xs font-medium border border-border-DEFAULT transition-all"
        >
          Register Local Package
        </button>
      </div>
    )}
  </div>
);
