import React, { useEffect, useRef, useState } from 'react';

interface InstallErrorNoticeProps {
  error: string;
  /**
   * True only when the backend error itself named an elevation cause. The
   * elevation guidance must never appear for unrelated failures (Zero-Mock).
   */
  elevationRequired: boolean;
  /** Manifest path of the last registration attempt, when one was made. */
  manifestPath: string;
}

/**
 * Install failure panel. Renders the real backend message verbatim, and shows
 * copyable elevated-PowerShell remediation only when elevation was the cause.
 */
export const InstallErrorNotice: React.FC<InstallErrorNoticeProps> = ({
  error,
  elevationRequired,
  manifestPath,
}) => {
  const [copied, setCopied] = useState(false);
  const copiedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (copiedTimerRef.current) clearTimeout(copiedTimerRef.current);
    };
  }, []);

  const elevatedCommand = `Add-AppxPackage -Register "${manifestPath}" -ForceApplicationShutdown -ForceUpdateFromAnyVersion`;

  return (
    <div className="p-3.5 rounded-xl bg-rose-950/40 text-rose-300 border border-rose-500/30 text-xs space-y-2">
      <div className="font-semibold flex items-center gap-2 text-rose-200">
        <span>🛡️</span>
        <span>
          {elevationRequired
            ? 'Administrator Elevation Required (Windows Service Registration)'
            : 'Install Failed'}
        </span>
      </div>
      <p className="text-[11px] text-rose-300/90 leading-relaxed font-mono break-all">{error}</p>
      {elevationRequired && manifestPath && (
        <>
          <p className="text-[11px] text-rose-300/90 leading-relaxed">
            Windows requires administrator privileges to install the WSA system service (
            <code className="font-mono text-rose-200">WsaService</code>
            ). Run Emberbird Manager as Administrator, or paste this command into an elevated
            PowerShell prompt:
          </p>
          <div className="p-2 rounded bg-surface-raised/80 border border-border-DEFAULT font-mono text-[11px] text-text-primary flex items-center justify-between gap-2 break-all">
            <code>{elevatedCommand}</code>
            <button
              type="button"
              onClick={() => {
                navigator.clipboard.writeText(elevatedCommand);
                setCopied(true);
                if (copiedTimerRef.current) clearTimeout(copiedTimerRef.current);
                copiedTimerRef.current = setTimeout(() => setCopied(false), 2000);
              }}
              className="px-2 py-1 rounded bg-surface-raised hover:bg-surface-raised text-[10px] text-accent font-sans whitespace-nowrap"
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </>
      )}
    </div>
  );
};
