/* E3B.4 parity oracle — the pre-migration GitHub discovery provider.
 *
 * Production code no longer performs GitHub release discovery (the website
 * consumes the Ember Registry). This module keeps the legacy provider ONLY as
 * the oracle that website/tests/registry-parity.test.mjs compares against the
 * registry provider, so the S2 parity guarantee remains testable. It must
 * never be imported by website/src.
 */
import type {
  ReleaseProvider,
  UnifiedRelease,
  GitHubRelease
} from '../../src/lib/types.ts';
import { parseNormalizedAsset, formatDate } from '../../src/lib/parser.ts';
import { classifyReleaseTag } from '../../src/lib/release-service.ts';

export class GitHubReleaseProvider implements ReleaseProvider {
  name = 'GitHubReleases';
  private customRepo?: string;

  constructor(repo?: string) {
    this.customRepo = repo;
  }

  async getLatestRelease(): Promise<UnifiedRelease | null> {
    const repo = this.repo();
    const endpoint = `https://api.github.com/repos/${repo}/releases?per_page=20`;
    const response = await fetch(endpoint, {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Emberbird-ReleaseService'
      }
    });

    if (!response.ok) {
      console.error(`GitHub Releases API responded with status ${response.status}`);
      return null;
    }

    const rawList = (await response.json()) as GitHubRelease[];
    if (!Array.isArray(rawList)) {
      console.error('GitHub Releases API returned an unexpected payload.');
      return null;
    }

    const wsaRaw = rawList.find(
      (r) => r.tag_name && (r.tag_name.startsWith('wsa-v') || r.tag_name.startsWith('Windows_'))
    );
    if (wsaRaw) {
      return this.normalize(wsaRaw);
    }

    return rawList.length > 0 ? this.normalize(rawList[0]) : null;
  }

  async getReleaseByTag(tag: string): Promise<UnifiedRelease | null> {
    if (!tag || !tag.trim()) {
      throw new Error('getReleaseByTag requires a non-empty release tag.');
    }
    const repo = this.repo();
    const endpoint = `https://api.github.com/repos/${repo}/releases/tags/${encodeURIComponent(tag)}`;
    const raw = await this.fetchRelease(endpoint);
    return raw ? this.normalize(raw) : null;
  }

  async listReleases(): Promise<UnifiedRelease[]> {
    const repo = this.repo();
    const endpoint = `https://api.github.com/repos/${repo}/releases?per_page=30`;
    const response = await fetch(endpoint, {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Emberbird-ReleaseService'
      }
    });

    if (!response.ok) {
      console.error(`GitHub Releases API responded with status ${response.status}`);
      return [];
    }

    const rawList = (await response.json()) as GitHubRelease[];
    if (!Array.isArray(rawList)) {
      console.error('GitHub Releases API returned an unexpected payload.');
      return [];
    }

    return rawList.map((raw) => this.normalize(raw));
  }

  private repo(): string {
    if (this.customRepo) {
      return this.customRepo;
    }
    const repo = import.meta.env.PUBLIC_GITHUB_REPO;
    if (!repo) {
      throw new Error('Configuration error: PUBLIC_GITHUB_REPO environment variable is required.');
    }
    return repo;
  }

  private async fetchRelease(endpoint: string): Promise<GitHubRelease | null> {
    const response = await fetch(endpoint, {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Emberbird-ReleaseService'
      }
    });

    if (!response.ok) {
      console.error(`GitHub Releases API responded with status ${response.status}`);
      return null;
    }

    return (await response.json()) as GitHubRelease;
  }

  private normalize(raw: GitHubRelease): UnifiedRelease {
    const checksums = this.extractChecksums(raw);
    // Metadata sidecars (hash files, checksums.txt, validation-report .json)
    // are published on the release but must never surface as download rows in
    // the main packages table — the UI links checksums separately.
    const isPackageAsset = (name: string): boolean => {
      const lower = name.toLowerCase();
      return !(lower.endsWith('.sha256') || lower.endsWith('.md5') || lower.endsWith('.json') || lower.endsWith('.txt'));
    };

    const normalizedAssets: NormalizedAsset[] = (raw.assets || [])
      .filter((asset) => isPackageAsset(asset.name))
      .map((asset) => parseNormalizedAsset(asset, checksums));

    return {
      id: raw.id,
      tag: raw.tag_name,
      name: raw.name || raw.tag_name,
      publishedAt: raw.published_at,
      formattedDate: formatDate(raw.published_at),
      notes: raw.body || '',
      releaseUrl: raw.html_url,
      assets: normalizedAssets,
      channel: classifyReleaseTag(raw.tag_name)
    };
  }

  private extractChecksums(raw: GitHubRelease): Record<string, string> {
    const map: Record<string, string> = {};
    if (!raw.body) return map;

    // Parse SHA256 lines from release notes if present
    const sha256Pattern = /([a-fA-F0-9]{64})\s+([a-zA-Z0-9_\-\.]+)/g;
    let match: RegExpExecArray | null;
    while ((match = sha256Pattern.exec(raw.body)) !== null) {
      const hash = match[1];
      const filename = match[2];
      map[filename] = hash;
    }
    return map;
  }
}
