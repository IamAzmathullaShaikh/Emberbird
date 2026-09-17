import React, { useState } from 'react';
import type { DoctorProbe } from '../lib/types';

export const DoctorView: React.FC = () => {
  const defaultProbes: DoctorProbe[] = [
    {
      probe_id: 'PRB-01',
      domain: 'Hardware Virtualization',
      title: 'CPU Virtualization Firmware (VT-x / AMD-V)',
      status: 'PASS',
      severity: 'CRITICAL',
      summary: 'Hardware virtualization is active in BIOS/UEFI firmware.',
      details: 'WMI VirtualizationFirmwareEnabled: True',
      can_autofix: false,
    },
    {
      probe_id: 'PRB-02',
      domain: 'Virtual Machine Platform',
      title: 'Windows Feature: VirtualMachinePlatform',
      status: 'PASS',
      severity: 'CRITICAL',
      summary: 'VirtualMachinePlatform feature is Enabled.',
      details: 'DISM reported state: Enabled',
      remediation_cmd: 'dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart',
      can_autofix: true,
    },
    {
      probe_id: 'PRB-03',
      domain: 'Hypervisor Platform',
      title: 'Windows Feature: HypervisorPlatform',
      status: 'PASS',
      severity: 'CRITICAL',
      summary: 'HypervisorPlatform feature is Enabled.',
      details: 'DISM reported state: Enabled',
      remediation_cmd: 'dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart',
      can_autofix: true,
    },
    {
      probe_id: 'PRB-04',
      domain: 'Developer Mode',
      title: 'AppModelUnlock Developer Mode',
      status: 'PASS',
      severity: 'CRITICAL',
      summary: 'Windows Developer Mode is ENABLED.',
      details: 'AllowDevelopmentWithoutDevLicense is set to 1',
      remediation_cmd: 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d 1',
      can_autofix: true,
    },
    {
      probe_id: 'PRB-05',
      domain: 'AppX Deployment',
      title: 'Windows Service: AppXSvc',
      status: 'PASS',
      severity: 'CRITICAL',
      summary: 'AppX Deployment Service (AppXSvc) is RUNNING.',
      details: 'Service is active and ready for package registration.',
      remediation_cmd: 'net start AppXSvc',
      can_autofix: true,
    },
    {
      probe_id: 'PRB-06',
      domain: 'ADB Connectivity',
      title: 'ADB Loopback Port 58526',
      status: 'WARN',
      severity: 'WARNING',
      summary: 'WSA ADB daemon is not currently listening on 127.0.0.1:58526.',
      details: 'WSA may be in sleep mode or Developer Mode is toggled off in WSA Settings.',
      remediation_cmd: 'adb connect 127.0.0.1:58526',
      can_autofix: false,
    },
    {
      probe_id: 'PRB-07',
      domain: 'Storage & Process Lock',
      title: 'userdata.vhdx Lock Status',
      status: 'PASS',
      severity: 'INFO',
      summary: 'No blocking zombie process locks detected on virtual disk.',
      details: 'userdata.vhdx is clean and ready for mounting or backup.',
      can_autofix: false,
    },
    {
      probe_id: 'PRB-08',
      domain: 'WSL & Compute Services',
      title: 'Host Compute Service & WSL Status',
      status: 'PASS',
      severity: 'CRITICAL',
      summary: 'Host Compute Service (vmcompute) is active.',
      details: 'Virtual machine compute layer is ready for microVM creation.',
      remediation_cmd: 'net start vmcompute',
      can_autofix: true,
    },
    {
      probe_id: 'PRB-09',
      domain: 'Google Play Services',
      title: 'Play Services & GApps Registration',
      status: 'PASS',
      severity: 'INFO',
      summary: 'WSA package registered with Google Play Services support.',
      details: 'GApps package manifest validated.',
      can_autofix: false,
    },
    {
      probe_id: 'PRB-10',
      domain: 'Google Account Authentication',
      title: 'Google Sign-In & Play Store Certification',
      status: 'PASS',
      severity: 'INFO',
      summary: 'Google Play Store certification and sign-in prerequisites satisfied.',
      details: 'PlayStoreEnabled is confirmed.',
      can_autofix: false,
    },
    {
      probe_id: 'PRB-11',
      domain: 'Virtual Networking',
      title: 'WSA Virtual Switch & Network Loopback',
      status: 'PASS',
      severity: 'CRITICAL',
      summary: 'Hyper-V Virtual Ethernet Adapter is Up.',
      details: 'Subsystem network virtual switch operating normally.',
      remediation_cmd: 'netsh winsock reset',
      can_autofix: true,
    },
    {
      probe_id: 'PRB-12',
      domain: 'Storage Capacity & Integrity',
      title: 'System Disk Space & userdata.vhdx Health',
      status: 'PASS',
      severity: 'CRITICAL',
      summary: 'System drive has >= 25 GB free space for subsystem updates.',
      details: 'Sufficient storage capacity confirmed.',
      can_autofix: false,
    },
  ];

  const [probes] = useState<DoctorProbe[]>(defaultProbes);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const passedCount = probes.filter((p) => p.status === 'PASS').length;
  const warnCount = probes.filter((p) => p.status === 'WARN').length;
  const failCount = probes.filter((p) => p.status === 'FAIL').length;

  const handleCopyCmd = (id: string, cmd: string) => {
    navigator.clipboard.writeText(cmd);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASS':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'WARN':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'FAIL':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview Banner */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              <span>Ember Doctor</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">
                PRB-01 to PRB-12
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Automated host environment diagnostic scanner for virtualization, networking, Play Services, and storage.
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

        {/* Actionable Warning/Failure Callout if any */}
        {warnCount + failCount > 0 && (
          <div className="mt-4 p-4 rounded-xl bg-amber-500/5 border border-amber-500/20">
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2">
              Actionable Remediations Detected
            </h3>
            <div className="space-y-2">
              {probes
                .filter((p) => p.status === 'WARN' || p.status === 'FAIL')
                .map((p) => (
                  <div key={p.probe_id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                    <div>
                      <span className="font-mono text-indigo-400 font-semibold mr-2">{p.probe_id}:</span>
                      <span className="text-slate-300">{p.summary}</span>
                    </div>
                    {p.remediation_cmd && (
                      <button
                        type="button"
                        onClick={() => handleCopyCmd(p.probe_id, p.remediation_cmd!)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-[11px] border border-slate-700 transition-colors whitespace-nowrap"
                      >
                        {copiedId === p.probe_id ? 'Copied!' : 'Copy Fix'}
                      </button>
                    )}
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* 12 Probe Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          {probes.map((probe) => (
            <div
              key={probe.probe_id}
              className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-indigo-400">{probe.probe_id}</span>
                    <span className="text-xs text-slate-400 font-medium truncate max-w-[180px]">{probe.domain}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusBadge(probe.status)}`}>
                    {probe.status}
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-white mb-1">{probe.title}</h4>
                <p className="text-xs text-slate-300 leading-relaxed mb-2">{probe.summary}</p>
              </div>

              {probe.remediation_cmd && probe.status !== 'PASS' && (
                <div className="pt-2 mt-2 border-t border-slate-800/60">
                  <span className="text-[10px] uppercase font-semibold text-slate-500 block mb-1">Remediation:</span>
                  <div className="flex items-center justify-between gap-2 bg-slate-900/80 px-2.5 py-1.5 rounded font-mono text-[11px] text-slate-300 border border-slate-800">
                    <span className="truncate">{probe.remediation_cmd}</span>
                    <button
                      type="button"
                      onClick={() => handleCopyCmd(probe.probe_id, probe.remediation_cmd!)}
                      className="text-xs text-indigo-400 hover:text-indigo-300 whitespace-nowrap ml-2"
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
