import type {
  ReleaseProvider,
  UnifiedRelease,
  NormalizedAsset,
  GitHubRelease,
  ReleaseAsset
} from './types';
import { parseNormalizedAsset, formatDate } from './parser';

export class GitHubReleaseProvider implements ReleaseProvider {
  name = 'GitHubReleases';

  async getLatestRelease(): Promise<UnifiedRelease | null> {
    const repo = import.meta.env.PUBLIC_GITHUB_REPO;
    if (!repo) {
      throw new Error('Configuration error: PUBLIC_GITHUB_REPO environment variable is required.');
    }

    const endpoint = `https://api.github.com/repos/${repo}/releases/latest`;
    const response = await fetch(endpoint, {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'WSABuilds-ReleaseService'
      }
    });

    if (!response.ok) {
      console.error(`GitHub Releases API responded with status ${response.status}`);
      return null;
    }

    const raw: GitHubRelease = await response.json();
    return this.normalize(raw);
  }

  private normalize(raw: GitHubRelease): UnifiedRelease {
    const checksums = this.extractChecksums(raw);
    const normalizedAssets: NormalizedAsset[] = (raw.assets || [])
      .filter((asset) => !asset.name.endsWith('.sha256') && !asset.name.endsWith('.md5'))
      .map((asset) => parseNormalizedAsset(asset, checksums));

    return {
      id: raw.id,
      tag: raw.tag_name,
      name: raw.name || raw.tag_name,
      publishedAt: raw.published_at,
      formattedDate: formatDate(raw.published_at),
      notes: raw.body || '',
      releaseUrl: raw.html_url,
      assets: normalizedAssets
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

export class ReleaseService {
  private provider: ReleaseProvider;
  private cache: { data: UnifiedRelease | null; timestamp: number } | null = null;
  private ttlMs: number;

  constructor(provider?: ReleaseProvider, ttlMinutes: number = 5) {
    this.provider = provider || new GitHubReleaseProvider();
    this.ttlMs = ttlMinutes * 60 * 1000;
  }

  async getLatestRelease(): Promise<UnifiedRelease | null> {
    const now = Date.now();
    if (this.cache && now - this.cache.timestamp < this.ttlMs) {
      return this.cache.data;
    }

    try {
      const data = await this.provider.getLatestRelease();
      this.cache = { data, timestamp: now };
      return data;
    } catch (error) {
      console.error(`ReleaseService failed to retrieve release from ${this.provider.name}:`, error);
      // If error occurs and stale cache exists, return stale cache as fallback
      if (this.cache) {
        return this.cache.data;
      }
      return null;
    }
  }
}

export const defaultReleaseService = new ReleaseService();
