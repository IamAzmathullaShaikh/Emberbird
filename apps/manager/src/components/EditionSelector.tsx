import React from 'react';
import { RECOMMENDED_WSA_EDITION, editionFlavors, type WsaEdition } from '../lib/registry';

interface EditionSelectorProps {
  selectedEdition: WsaEdition;
  onSelect: (edition: WsaEdition) => void;
}

/**
 * Edition selection grid. Descriptions are composed from registry truth — the
 * recommendation badge comes from the single named policy constant, never a
 * literal.
 */
export const EditionSelector: React.FC<EditionSelectorProps> = ({
  selectedEdition,
  onSelect,
}) => {
  const flavors = {
    standard: editionFlavors('standard'),
    banking: editionFlavors('banking'),
  };

  return (
  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
    <button
      type="button"
      onClick={() => onSelect('standard')}
      className={`p-3.5 rounded-xl text-left transition-all border ${
        selectedEdition === 'standard'
          ? 'bg-accent-active/30 border-accent text-white shadow-lg shadow-accent/10'
          : 'bg-surface-raised/40 border-border-DEFAULT/80 text-text-secondary hover:border-border-DEFAULT'
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="font-semibold text-xs text-accent">Standard Edition</span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-accent/20 text-accent">
          {RECOMMENDED_WSA_EDITION === 'standard' ? 'Recommended' : 'Rooted'}
        </span>
      </div>
      <p className="text-[11px] text-text-secondary mt-1 leading-snug">
        {`${flavors.standard.root} + ${flavors.standard.gapps} + Google Play Store. Ideal for productivity, power users, and modding.`}
      </p>
    </button>

    <button
      type="button"
      onClick={() => onSelect('banking')}
      className={`p-3.5 rounded-xl text-left transition-all border ${
        selectedEdition === 'banking'
          ? 'bg-emerald-950/30 border-emerald-500 text-white shadow-lg shadow-emerald-500/10'
          : 'bg-surface-raised/40 border-border-DEFAULT/80 text-text-secondary hover:border-border-DEFAULT'
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="font-semibold text-xs text-emerald-300">Banking Edition</span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
          {RECOMMENDED_WSA_EDITION === 'banking' ? 'Recommended' : 'Zero Root'}
        </span>
      </div>
      <p className="text-[11px] text-text-secondary mt-1 leading-snug">
        {`${flavors.banking.root} with ${flavors.banking.gapps}. Passes Play Integrity MEETS_BASIC without root hiding workarounds.`}
      </p>
    </button>
  </div>
  );
};
