export interface AppEnvironment {
  SITE_URL: string;
  PUBLIC_GITHUB_REPO: string;
  PUBLIC_GITHUB_REPO_URL: string;
  PUBLIC_RELEASES_URL: string;
}

export const REQUIRED_ENV_VARS = [
  'SITE_URL',
  'PUBLIC_GITHUB_REPO',
  'PUBLIC_GITHUB_REPO_URL',
  'PUBLIC_RELEASES_URL'
] as const;

export function validateEnvironment(envSource?: Record<string, string | undefined>): {
  valid: boolean;
  missing: string[];
  errorMessage?: string;
} {
  const env = envSource || {
    SITE_URL: process.env.SITE_URL || (import.meta as any).env?.SITE_URL,
    PUBLIC_GITHUB_REPO: process.env.PUBLIC_GITHUB_REPO || (import.meta as any).env?.PUBLIC_GITHUB_REPO,
    PUBLIC_GITHUB_REPO_URL: process.env.PUBLIC_GITHUB_REPO_URL || (import.meta as any).env?.PUBLIC_GITHUB_REPO_URL,
    PUBLIC_RELEASES_URL: process.env.PUBLIC_RELEASES_URL || (import.meta as any).env?.PUBLIC_RELEASES_URL
  };

  const missing: string[] = [];
  for (const key of REQUIRED_ENV_VARS) {
    const val = env[key];
    if (!val || typeof val !== 'string' || val.trim().length === 0) {
      missing.push(key);
    }
  }

  if (missing.length > 0) {
    const message = [
      '==================================================================',
      'CONFIGURATION ERROR: Missing Required Environment Variables',
      '==================================================================',
      `The following required environment variables are not defined:`,
      ...missing.map((key) => `  - ${key}`),
      '',
      'Remediation:',
      '  1. Local Development: Copy website/.env.example to website/.env and configure values.',
      '  2. CI/CD Deployment: Configure repository variables or workflow env blocks.',
      '  3. Silent fallbacks are strictly prohibited by Configuration Governance.',
      '=================================================================='
    ].join('\n');

    return { valid: false, missing, errorMessage: message };
  }

  return { valid: true, missing: [] };
}

export function assertValidEnvironment(envSource?: Record<string, string | undefined>): void {
  const result = validateEnvironment(envSource);
  if (!result.valid && result.errorMessage) {
    throw new Error(result.errorMessage);
  }
}
