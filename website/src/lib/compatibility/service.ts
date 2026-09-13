import type {
  CompatibilityRecord,
  CompatibilityStats,
  CompatibilityFilterOptions,
  CompatibilityStatus
} from './types';

export function calculateStats(records: CompatibilityRecord[]): CompatibilityStats {
  const stats: CompatibilityStats = {
    total: records.length,
    working: 0,
    workaround: 0,
    broken: 0,
    playIntegrityRequired: 0
  };

  for (const r of records) {
    if (r.compatibility_status === 'Working') {
      stats.working++;
    } else if (r.compatibility_status === 'Workaround Required') {
      stats.workaround++;
    } else if (r.compatibility_status === 'Broken') {
      stats.broken++;
    }

    if (r.play_integrity_required) {
      stats.playIntegrityRequired++;
    }
  }

  return stats;
}

export function getCategories(records: CompatibilityRecord[]): string[] {
  const set = new Set<string>();
  for (const r of records) {
    if (r.category) {
      set.add(r.category);
    }
  }
  return Array.from(set).sort();
}

export function filterRecords(
  records: CompatibilityRecord[],
  options: CompatibilityFilterOptions
): CompatibilityRecord[] {
  return records.filter((r) => {
    if (options.category && options.category !== 'All' && r.category !== options.category) {
      return false;
    }

    if (options.status && options.status !== 'All' && r.compatibility_status !== options.status) {
      return false;
    }

    if (options.playIntegrityOnly && !r.play_integrity_required) {
      return false;
    }

    if (options.searchQuery && options.searchQuery.trim().length > 0) {
      const q = options.searchQuery.toLowerCase().trim();
      const nameMatch = r.app_name.toLowerCase().includes(q);
      const pkgMatch = r.package_id.toLowerCase().includes(q);
      const categoryMatch = r.category.toLowerCase().includes(q);
      if (!nameMatch && !pkgMatch && !categoryMatch) {
        return false;
      }
    }

    return true;
  });
}

export function getStatusBadgeClass(status: CompatibilityStatus): {
  bg: string;
  text: string;
  border: string;
} {
  switch (status) {
    case 'Working':
      return {
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-400',
        border: 'border-emerald-500/30'
      };
    case 'Workaround Required':
      return {
        bg: 'bg-amber-500/10',
        text: 'text-amber-400',
        border: 'border-amber-500/30'
      };
    case 'Broken':
      return {
        bg: 'bg-rose-500/10',
        text: 'text-rose-400',
        border: 'border-rose-500/30'
      };
    default:
      return {
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
        border: 'border-slate-500/30'
      };
  }
}
