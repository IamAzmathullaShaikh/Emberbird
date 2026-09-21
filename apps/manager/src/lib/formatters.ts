/**
 * Single-source formatting utilities.
 * All views must import from here — never implement inline.
 * Rule 15 (Anti-Staleness): duplicate implementations have been removed.
 */

/** Format bytes into a human-readable string (e.g. "2.3 GB", "512 MB"). */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

/** Format bytes as gigabytes with 1 decimal place (e.g. "25.0 GB"). */
export function formatGB(bytes: number): string {
  return `${(bytes / (1024 ** 3)).toFixed(1)} GB`;
}

/** Format an ISO 8601 timestamp into a human-readable local date/time string. */
export function formatDate(isoString: string): string {
  try {
    return new Date(isoString).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  } catch {
    return isoString;
  }
}
