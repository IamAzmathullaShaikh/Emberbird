import type {
  ReleaseProvider,
  UnifiedRelease,
  NormalizedAsset
} from './types.ts';
import { parseNormalizedAsset, formatDate, formatBytes, detectArchitecture, detectRootFlavor, detectGAppsFlavor } from './parser.ts';
import registryData from '../../../data/releases/releases.json' with { type: 'json' };

export type ReleaseChannel = 'manager' | 'wsa';

/** Classify a release by its tag: Manager releases are `v*`, WSA releases are `wsa-v*` or `Windows_*`. */
export function classifyReleaseTag(tag: string): ReleaseChannel {
  return tag.startsWith('wsa-v') || tag.startsWith('Windows_') ? 'wsa' : 'manager';
}

/**
 * Resolves the releases the website advertises from its release provider
 * (the Ember Registry by default, E3B.4), pinning each product family to its
 * newest advertised release so page content is deterministic and
 * registry-driven.
 */
export class PinnedReleaseService {
  private provider: ReleaseProvider;
  private cache = new Map<string, UnifiedRelease | null>();
  private ttlMs: number;
  private timestamps = new Map<string, number>();

  constructor(provider?: ReleaseProvider, ttlMinutes: number = 5) {
    // E3B.4: default release discovery is the Ember Registry (offline,
    // reality-validated). Legacy GitHub discovery was removed after S2 parity
    // was proven (website/tests/registry-parity.test.mjs against the oracle
    // in website/tests/lib/github-release-oracle.ts).
    this.provider = provider || new RegistryReleaseProvider();
    this.ttlMs = ttlMinutes * 60 * 1000;
  }

  /** Fulfill ReleaseProvider interface: resolve the newest WSA release. */
  async getLatestRelease(): Promise<UnifiedRelease | null> {
    return this.getLatestForChannel('wsa');
  }

  /** Resolve the newest release for a product family by listing all releases. */
  async getLatestForChannel(channel: ReleaseChannel): Promise<UnifiedRelease | null> {
    const releases = await this.listReleasesCached();
    return releases.find((r) => r.channel === channel) || null;
  }

  async getReleaseByTag(tag: string): Promise<UnifiedRelease | null> {
    return this.cached(`tag:${tag}`, () => this.provider.getReleaseByTag(tag));
  }

  async listReleases(): Promise<UnifiedRelease[]> {
    return this.listReleasesCached();
  }

  private async listReleasesCached(): Promise<UnifiedRelease[]> {
    const cached = this.cache.get('list');
    const ts = this.timestamps.get('list') || 0;
    if (cached && Date.now() - ts < this.ttlMs) {
      return cached as unknown as UnifiedRelease[];
    }
    try {
      const data = await this.provider.listReleases();
      this.cache.set('list', data as unknown as UnifiedRelease | null);
      this.timestamps.set('list', Date.now());
      return data;
    } catch (error) {
      console.error(`PinnedReleaseService failed to list releases from ${this.provider.name}:`, error);
      return cached ? (cached as unknown as UnifiedRelease[]) : [];
    }
  }

  private async cached(
    key: string,
    loader: () => Promise<UnifiedRelease | null>
  ): Promise<UnifiedRelease | null> {
    const now = Date.now();
    const hit = this.cache.get(key);
    const ts = this.timestamps.get(key) || 0;
    if (hit !== undefined && now - ts < this.ttlMs) {
      return hit;
    }
    try {
      const data = await loader();
      this.cache.set(key, data);
      this.timestamps.set(key, now);
      return data;
    } catch (error) {
      console.error(`PinnedReleaseService failed to retrieve release (${key}):`, error);
      return hit !== undefined ? hit : null;
    }
  }
}


/* -------------------------------------------------------------------------
 * E3B.2 — Registry consumer (G2): release truth from the Ember Registry
 * (`data/releases/releases.json`), the repository's single source of truth.
 *
 * This provider is ADDITIVE during the S2 parity phase: it implements the
 * same `ReleaseProvider` interface as the legacy provider (kept as the test
 * oracle in website/tests/lib/github-release-oracle.ts), so parity can
 * be demonstrated by comparing outputs for the same release set before any
 * legacy discovery is removed (E3B.4). It performs zero network I/O at
 * runtime — the registry is validated by CI's Reality Gate before any build
 * that embeds it.
 * ------------------------------------------------------------------------- */

/** Minimal structural view of the registry used by this module. */
interface RegistryAsset {
  filename: string;
  sha256: string;
  arch?: string;
  role?: string;
  source_url: string;
  size_bytes?: number;
}

interface RegistryRelease {
  release_id: string;
  tag: string;
  kind: string;
  channel: string;
  status: string;
  published_at: string;
  assets: RegistryAsset[];
}

interface RegistryFile {
  schema_version: number;
  releases: RegistryRelease[];
}

const REGISTRY = registryData as unknown as RegistryFile;

/** Registry channels we advertise. Only published releases are surfaced. */
const ADVERTISED_STATUSES = new Set(['published']);

function registryKindToChannel(kind: string): ReleaseChannel | null {
  if (kind === 'manager') return 'manager';
  if (kind === 'subsystem') return 'wsa';
  return null; // unknown kinds are not advertised
}

/**
 * Release provider backed by the Ember Registry. Build-time, offline,
 * reality-validated — no GitHub discovery.
 */
export class RegistryReleaseProvider implements ReleaseProvider {
  name = 'EmberRegistry';
  private registry: RegistryFile;

  // NOTE: no parameter properties — Node's type-stripping test loader only
  // supports erasable TypeScript syntax.
  constructor(registry: RegistryFile = REGISTRY) {
    this.registry = registry;
  }

  private all(): UnifiedRelease[] {
    // Group registry rows by tag and merge their assets. Multiple editions
    // (e.g. Standard + Banking) legitimately publish under ONE GitHub tag, so
    // GitHub shows a single release with the union of assets. Grouping here
    // keeps registry output user-equivalent to that published reality (S2).
    const groups = new Map<string, RegistryRelease[]>();
    for (const r of this.registry.releases) {
      if (!ADVERTISED_STATUSES.has(r.status) || registryKindToChannel(r.kind) === null) continue;
      const existing = groups.get(r.tag);
      if (existing) existing.push(r);
      else groups.set(r.tag, [r]);
    }
    return [...groups.values()].map((rows) => this.normalizeGroup(rows));
  }

  private normalizeGroup(rows: RegistryRelease[]): UnifiedRelease {
    rows.sort((a, b) => a.release_id.localeCompare(b.release_id));
    const merged: RegistryRelease = {
      // Primary row identity (the `name` field is display-only and consumed
      // by no page; assets and tag are the user-visible truth).
      release_id: rows[0].release_id,
      tag: rows[0].tag,
      kind: rows[0].kind,
      channel: rows[0].channel,
      status: rows[0].status,
      published_at: rows.map((r) => r.published_at).sort().at(-1) as string,
      assets: rows.flatMap((r) => r.assets)
    };
    return this.normalize(merged);
  }

  async getLatestRelease(): Promise<UnifiedRelease | null> {
    // Mirrors PinnedReleaseService semantics: newest release of the wsa channel.
    const wsa = this.all()
      .filter((r) => r.channel === 'wsa')
      .sort((a, b) => b.publishedAt.localeCompare(a.publishedAt));
    return wsa[0] ?? null;
  }

  async getReleaseByTag(tag: string): Promise<UnifiedRelease | null> {
    const found = this.all().find((r) => r.tag === tag);
    return found ?? null;
  }

  async listReleases(): Promise<UnifiedRelease[]> {
    return this.all().sort((a, b) => b.publishedAt.localeCompare(a.publishedAt));
  }

  private normalize(r: RegistryRelease): UnifiedRelease {
    // Registry assets are already curated: every row is a real package
    // (sidecars live in the vault), and every row carries its published
    // sha256 — checksums come from registry truth, not release-notes regex.
    const normalizedAssets: NormalizedAsset[] = r.assets.map((a) => ({
      assetId: 0, // registry rows have no GitHub numeric id; pages never read it
      fileName: a.filename,
      fileSizeBytes: a.size_bytes ?? 0,
      formattedSize: formatBytes(a.size_bytes ?? 0),
      downloadUrl: a.source_url,
      architecture: detectArchitecture(a.filename),
      rootFlavor: detectRootFlavor(a.filename),
      gappsFlavor: detectGAppsFlavor(a.filename),
      sha256: a.sha256
    }));

    return {
      id: 0,
      tag: r.tag,
      name: r.release_id,
      publishedAt: r.published_at,
      formattedDate: formatDate(r.published_at),
      notes: '',
      releaseUrl: '',
      assets: normalizedAssets,
      channel: registryKindToChannel(r.kind) as ReleaseChannel
    };
  }
}

/** Shared singleton for pages that want registry truth. */
export const registryReleaseProvider = new RegistryReleaseProvider();

/** Service singleton — constructed after RegistryReleaseProvider's declaration
 * (E3B.4 default) to avoid a TDZ error at module-load time. */
export const pinnedReleaseService = new PinnedReleaseService();
