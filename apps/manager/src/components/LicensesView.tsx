import React from 'react';

export const LicensesView: React.FC = () => {
  const licenses = [
    {
      name: 'Emberbird Platform & Manager',
      license: 'AGPL-3.0',
      description: 'The core lifecycle platform, desktop manager, scripts, and release engine are licensed under the GNU Affero General Public License v3.0.',
      url: 'https://www.gnu.org/licenses/agpl-3.0.en.html',
    },
    {
      name: 'Magisk Dynamic Loader & Patches',
      license: 'GPL-3.0',
      description: 'Embedded Magisk binaries (libmagisk, magiskboot, magiskpolicy) are licensed under the GNU General Public License v3.0 by topjohnwu.',
      url: 'https://github.com/topjohnwu/Magisk',
    },
    {
      name: 'Documentation & Architecture Records',
      license: 'CC-BY-NC-ND-4.0',
      description: 'Official platform documentation, ADRs, research reports, and guides are licensed under Creative Commons Attribution-NonCommercial-NoDerivatives 4.0.',
      url: 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
    },
    {
      name: 'Microsoft Windows Subsystem for Android',
      license: 'Proprietary / Retail EULA',
      description: 'WSA base packages are proprietary to Microsoft Corporation. Emberbird provides non-commercial, reproducible build tooling under Windows Developer Mode.',
      url: 'https://support.microsoft.com/',
    },
    {
      name: 'OpenGApps / MindTheGapps',
      license: 'Open Source / Apache 2.0',
      description: 'Google Apps overlays packages are distributed under their respective upstream open-source licenses by the OpenGApps and LineageOS projects.',
      url: 'https://opengapps.org/',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl bg-surface-raised/60 border border-DEFAULT backdrop-blur shadow-xl">
        <div className="flex items-center justify-between pb-4 border-b border-DEFAULT">
          <div>
            <h2 className="text-lg font-bold text-text-primary tracking-tight">Legal & Open Source Licenses</h2>
            <p className="text-xs text-text-secondary mt-1">
              Complete attribution, licensing audit, and compliance boundaries for Emberbird.
            </p>
          </div>
          <span className="px-3 py-1 rounded-full bg-status-pass/10 text-status-pass border border-status-pass/20 text-xs font-semibold">
            100% Audit Compliant
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4 mt-6">
          {licenses.map((lic) => (
            <div
              key={lic.name}
              className="p-4 rounded-xl bg-surface-raised/60 border border-DEFAULT/80 hover:border-DEFAULT transition-colors"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-text-primary">{lic.name}</h3>
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-medium bg-accent/10 text-accent border border-accent/20">
                  {lic.license}
                </span>
              </div>
              <p className="text-xs text-text-secondary mt-2 leading-relaxed">{lic.description}</p>
              <div className="mt-3">
                <a
                  href={lic.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[11px] text-accent hover:text-accent transition-colors inline-flex items-center gap-1 font-medium"
                >
                  View License Terms &rarr;
                </a>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 p-4 rounded-xl bg-surface-raised/20 border border-accent/20 text-xs text-text-secondary space-y-2">
          <p className="font-semibold text-text-primary">Historical Attribution & Lineage</p>
          <p>
            Emberbird is built upon foundational innovations from the <strong>WSABuilds</strong> project (created by MustardChef)
            and the <strong>MagiskOnWSALocal</strong> lineage. Historical project names, attribution notices, and published release records
            are permanently preserved under the Emberbird Stewardship Charter.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LicensesView;
