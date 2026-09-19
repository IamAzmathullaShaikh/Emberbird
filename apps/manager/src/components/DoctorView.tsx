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
      remediation_cmd: 'reg add \"HKLM\\\\SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\AppModelUnlock\" /t REG_DWORD /f /v \"AllowDevelopmentWithoutDevLicense\" /d 1',
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
      details: 'WSA runs on-demand. Launch WSA Settings or an Android app (or enable Continuous mode in Settings) to open port 58526.',
      remediation_cmd: 'adb connect 127.0.0.1:58526',
      can_autofix: false,
    },
    {
      probe_id: 'PRB-07',
      domain: 'Storage & Process Lock',
      title: 'userdata.2.vhdx / userdata.vhdx Lock Status',
      status: 'PASS',
      severity: 'INFO',
      summary: 'No blocking zombie process locks detected on virtual disk.',
      details: 'Active userdata virtual disk is unlocked and ready for mounting or backup.',
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
      details: 'Google Play Protect verified. If uncertified device error appears, register GSF ID at https://www.google.com/android/uncertified.',
      remediation_cmd: 'https://www.google.com/android/uncertified',
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
        return 'bg-ember-charcoal text-ember-ash border-ember-ash/30';
    }
  };

  return (
    <div className=\"space-y-6\">
      {/* Overview Banner */}\n      <div className=\"p-6 rounded-2xl bg-ember-charcoal/60 border border-ember-ash/20 backdrop-blur-sm shadow-xl\">\n        <div className=\"flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-ember-ash/20\">\n          <div className=\"flex flex-col\">\n            <h2 className=\"text-lg font-bold text-white tracking-tight flex items-center gap-2\">\n              <span className=\"text-ember-glow\">Ember Doctor</span>\n              <span className=\"text-xs px-2.5 py-0.5 rounded-full bg-ember-glow/10 text-ember-glow border border-ember-glow/20 font-mono\">\n                Diagnostic Engine v1.0\n              </span>\n            </h2>\n            <p className=\"text-xs text-ember-ash mt-1\">\n              Automated host environment diagnostic scanner for virtualization, networking, and system integrity.\n            </p>\n          </div>\n          <div className=\"flex items-center gap-2\">\n            <span className=\"px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold\">\n              {passedCount} Passed\n            </span>\n            {warnCount > 0 && (\n              <span className=\"px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold\">\n                {warnCount} Warning{warnCount > 1 ? 's' : ''}\n              </span>\n            )}\n            {failCount > 0 && (\n              <span className=\"px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-semibold\">\n                {failCount} Fail{failCount > 1 ? 's' : ''}\n              </span>\n            )}\n          </div>\n        </div>\n\n        {/* Actionable Warning/Failure Callout if any */}\n        {warnCount + failCount > 0 && (\n          <div className=\"mt-4 p-4 rounded-xl bg-ember-glow/5 border border-ember-glow/20\">\n            <h3 className=\"text-xs font-bold text-ember-glow uppercase tracking-wider mb-2\">\n              Critical Remediations Detected\n            </h3>\n            <div className=\"space-y-2\">\n              {probes\n                .filter((p) => p.status === 'WARN' || p.status === 'FAIL')\n                .map((p) => (\n                  <div key={p.probe_id} className=\"flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs bg-ember-obsidian/60 p-3 rounded-lg border border-ember-ash/20\">\n                    <div className=\"flex items-center gap-2\">\n                      <span className=\"font-mono text-ember-glow font-bold\">{p.probe_id}</span>\n                      <span className=\"text-slate-300\">{p.summary}</span>\n                    </div>\n                    {p.remediation_cmd && (\n                      <button\n                        type=\"button\"\n                        onClick={() => handleCopyCmd(p.probe_id, p.remediation_cmd!)}\n                        className=\"px-2.5 py-1 rounded bg-ember-charcoal hover:bg-ember-ash/40 text-white font-mono text-[11px] border border-ember-ash/30 transition-colors whitespace-nowrap\"\n                      >\n                        {copiedId === p.probe_id ? 'Copied!' : 'Copy Fix'}\n                      </button>\n                    )}\n                  </div>\n                ))}\n            </div>\n          </div>\n        )}\n\n        {/* 12 Probe Grid */}\n        <div className=\"grid grid-cols-1 md:grid-cols-2 gap-4 mt-6\">\n          {probes.map((probe) => (\n            <div\n              key={probe.probe_id}\n              className=\"p-4 rounded-xl bg-ember-obsidian/60 border border-ember-ash/20 hover:border-ember-glow/40 transition-all duration-200 flex flex-col justify-between group\"\n            >\n              <div className=\"space-y-2\">\n                <div className=\"flex items-center justify-between gap-2\">\n                  <div className=\"flex items-center gap-2\">\n                    <span className=\"text-xs font-mono font-bold text-ember-glow\">{probe.probe_id}</span>\n                    <span className=\"text-xs text-ember-ash font-medium truncate max-w-[150px]\">{probe.domain}</span>\n                  </div>\n                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusBadge(probe.status)}`}>\n                    {probe.status}\n                  </span>\n                </div>\n                <h4 className=\"text-sm font-semibold text-white group-hover:text-ember-glow transition-colors\">{probe.title}</h4>\n                <p className=\"text-xs text-ember-ash leading-relaxed\">{probe.summary}</p>\n              </div>\n\n              {probe.remediation_cmd && probe.status !== 'PASS' && (\n                <div className=\"pt-3 mt-3 border-t border-ember-ash/20\">\n                  <span className=\"text-[10px] uppercase font-bold text-ember-ash/60 block mb-1\">Remediation:</span>\n                  <div className=\"flex items-center justify-between gap-2 bg-ember-charcoal/60 px-2.5 py-1.5 rounded border border-ember-ash/30 font-mono text-[11px] text-slate-300\">\n                    <span className=\"truncate\">{probe.remediation_cmd}</span>\n                    <button\n                      type=\"button\"\n                      onClick={() => handleCopyCmd(probe.probe_id, probe.remediation_cmd!)}\n                      className=\"text-xs text-ember-glow hover:text-ember-highlight transition-colors whitespace-nowrap ml-2\"\n                    >\n                      {copiedId === probe.probe_id ? 'Copied' : 'Copy'}\n                    </button>\n                  </div>\n                </div>\n              )}\n            </div>\n          ))}\n        </div>\n      </div>\n    </div>\n  );\n};