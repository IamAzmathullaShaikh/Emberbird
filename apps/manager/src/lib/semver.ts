export function cleanVersionString(ver: string): string {
  if (!ver) return '0.0.0.0';
  return ver.replace(/^[vV]/, '').trim();
}

export function compareVersions(v1: string, v2: string): number {
  const clean1 = cleanVersionString(v1);
  const clean2 = cleanVersionString(v2);

  const parts1 = clean1.split('.').map((p) => parseInt(p, 10) || 0);
  const parts2 = clean2.split('.').map((p) => parseInt(p, 10) || 0);

  const maxLen = Math.max(parts1.length, parts2.length);

  for (let i = 0; i < maxLen; i++) {
    const num1 = parts1[i] || 0;
    const num2 = parts2[i] || 0;
    if (num1 > num2) return 1;
    if (num1 < num2) return -1;
  }

  return 0;
}

export function isNewerVersion(current: string, latest: string): boolean {
  return compareVersions(latest, current) > 0;
}
