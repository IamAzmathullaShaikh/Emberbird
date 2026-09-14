import type { ManagerEnvConfig } from './types';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function validateManagerEnvironment(envSource?: Record<string, string | undefined>): ManagerEnvConfig {
  const source = envSource || (typeof (import.meta as any) !== 'undefined' && (import.meta as any).env ? (import.meta as any).env : process.env);

  const github_repo = source.VITE_PUBLIC_GITHUB_REPO || 'IamAzmathullaShaikh/WSABuilds';
  const repo_url = source.VITE_PUBLIC_GITHUB_REPO_URL || `https://github.com/${github_repo}`;
  const releases_url = source.VITE_PUBLIC_RELEASES_URL || `https://github.com/${github_repo}/releases`;

  if (!github_repo || github_repo.trim().length === 0) {
    throw new Error('VITE_PUBLIC_GITHUB_REPO must be explicitly provided.');
  }

  return {
    github_repo,
    repo_url,
    releases_url
  };
}
