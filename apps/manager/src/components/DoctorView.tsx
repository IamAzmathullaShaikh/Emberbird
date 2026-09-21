import React, { useCallback, useEffect, useState } from 'react';
import { runDoctorScan } from '../lib/ipc';
import type { DoctorProbe } from '../lib/types';

export const DoctorView: React.FC = () => {
  const [probes, setProbes] = useState<DoctorProbe[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [scanError, setScanError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const runScan = useCallback(async () => {
    setIsLoading(true);
    setScanError(null);
    try {
      setProbes(await runDoctorScan());
    } catch (err) {
      // Zero-Mock law: a failed scan is rendered as a failure, never as an
      // empty board that could be mistaken for "no problems found".
      setProbes([]);
      setScanError(String(err));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    runScan();
  }, [runScan]);

  const passedCount = probes.filter((p) => p.status === 'PASS').length;
  const warnCount = probes.filter((p) => p.status === 'WARN').length;
  const failCount = probes.filter((p) => p.status === 'FAIL').length;

  const copyTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleCopyCmd = (id: string, cmd: string) => {
    navigator.clipboard.writeText(cmd);
    setCopiedId(id);
    if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
    copyTimerRef.current = setTimeout(() => setCopiedId(null), 2000);
  };

  useEffect(() => {
    return () => {
      if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
    };
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASS':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'WARN':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'FAIL':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      default:
        return 'bg-ember-charcoal text-ember-ash border-ember-ash/30';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-ember-glow border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-ember-ash font-medium animate-pulse">Running system diagnostics...</p>
        </div>
      </div>
    );
  }

  if (scanError) {
    return (
      <div className="p-6 rounded-2xl bg-ember-charcoal/60 border border-rose-500/30 backdrop-blur-sm shadow-xl space-y-3">
        <h2 className="text-lg font-bold text-white tracking-tight">
          <span className="text-ember-glow">Ember Doctor</span>
        </h2>
        <p className="text-sm text-rose-300">
          Diagnostic scan failed — no probe results were produced. This is a
          scan failure, not a clean bill of health.
        </p>
        <div className="p-3 rounded-lg bg-ember-obsidian/60 border border-ember-ash/20 font-mono text-[11px] text-rose-200 break-all">
          {scanError}
        </div>
        <button
          type="button"
          onClick={runScan}
          className="px-3 py-1.5 rounded-lg bg-ember-charcoal hover:bg-ember-ash/40 text-white text-xs font-medium border border-ember-ash/30 transition-colors"
        >
          Retry Scan
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl bg-ember-charcoal/60 border border-ember-ash/20 backdrop-blur-sm shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-ember-ash/20">
          <div className="flex flex-col">
            <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              <span className="text-ember-glow">Ember Doctor</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-ember-glow/10 text-ember-glow border border-ember-glow/20 font-mono">
                Diagnostic Engine v1.0
              </span>
            </h2>
            <p className="text-xs text-ember-ash mt-1">
              Automated host environment diagnostic scanner for virtualization, networking, and system integrity.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold">
              {passedCount} Passed
            </span>
            {warnCount > 0 && (
              <span className="px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold">
                {warnCount} Warning{warnCount > 1 ? 's' : ''}
              </span>
            )}
            {failCount > 0 && (
              <span className="px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-semibold">
                {failCount} Fail{failCount > 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>

        {warnCount + failCount > 0 && (
          <div className="mt-4 p-4 rounded-xl bg-ember-glow/5 border border-ember-glow/20">
            <h3 className="text-xs font-bold text-ember-glow uppercase tracking-wider mb-2">
              Actionable Remediations
            </h3>
            <div className="space-y-2">
              {probes
                .filter((p) => p.status === 'WARN' || p.status === 'FAIL')
                .map((p) => (
                  <div key={p.probe_id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs bg-ember-obsidian/60 p-3 rounded-lg border border-ember-ash/20">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-ember-glow font-bold">{p.probe_id}</span>
                      <span className="text-text-secondary">{p.summary}</span>
                    </div>
                    {p.remediation_cmd && (
                      <button
                        type="button"
                        onClick={() => handleCopyCmd(p.probe_id, p.remediation_cmd!)}
                        className="px-2.5 py-1 rounded bg-ember-charcoal hover:bg-ember-ash/40 text-white font-mono text-[11px] border border-ember-ash/30 transition-colors whitespace-nowrap"
                      >
                        {copiedId === p.probe_id ? 'Copied!' : 'Copy Fix'}
                      </button>
                    )}
                  </div>
                ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          {probes.map((probe) => (
            <div
              key={probe.probe_id}
              className="p-4 rounded-xl bg-ember-obsidian/60 border border-ember-ash/20 hover:border-ember-glow/40 transition-all duration-200 flex flex-col justify-between group"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-ember-glow">{probe.probe_id}</span>
                    <span className="text-xs text-ember-ash font-medium truncate max-w-[150px]">{probe.domain}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusBadge(probe.status)}`}>
                    {probe.status}
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-white group-hover:text-ember-glow transition-colors">{probe.title}</h4>
                <p className="text-xs text-ember-ash leading-relaxed">{probe.summary}</p>
              </div>

              {probe.remediation_cmd && probe.status !== 'PASS' && (
                <div className="pt-3 mt-3 border-t border-ember-ash/20">
                  <span className="text-[10px] uppercase font-bold text-ember-ash/60 block mb-1">Remediation:</span>
                  <div className="flex items-center justify-between gap-2 bg-ember-charcoal/60 px-2.5 py-1.5 rounded border border-ember-ash/30 font-mono text-[11px] text-text-secondary">
                    <span className="truncate">{probe.remediation_cmd}</span>
                    <button
                      type="button"
                      onClick={() => handleCopyCmd(probe.probe_id, probe.remediation_cmd!)}
                      className="text-xs text-ember-glow hover:text-ember-highlight transition-colors whitespace-nowrap ml-2"
                    >
                      {copiedId === probe.probe_id ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
