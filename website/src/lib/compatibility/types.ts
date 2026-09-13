export type CompatibilityStatus = 'Working' | 'Workaround Required' | 'Broken';
export type VerificationStatus = 'verified' | 'unverified' | 'community_submitted';

export interface CompatibilityRecord {
  id?: string;
  app_name: string;
  package_id: string;
  category: string;
  compatibility_status: CompatibilityStatus;
  play_integrity_required: boolean;
  tested_wsa_version: string;
  tested_root_flavor: string;
  last_tested_date?: string;
  workaround_steps?: string[];
  known_issues?: string;
  verification_status?: VerificationStatus;
}

export interface CompatibilityStats {
  total: number;
  working: number;
  workaround: number;
  broken: number;
  playIntegrityRequired: number;
}

export interface CompatibilityFilterOptions {
  category?: string;
  status?: CompatibilityStatus | 'All';
  searchQuery?: string;
  playIntegrityOnly?: boolean;
}
