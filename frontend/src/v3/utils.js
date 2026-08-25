// frontend/src/v3/utils.js
// Small shared helpers for the V3 surface.

/**
 * Human-readable byte size, e.g. `0 B`, `512 B`, `1.2 KB`, `1.5 MB`.
 * Null/undefined/non-numeric inputs render as `—`.
 */
export function formatBytes(bytes) {
  if (bytes === null || bytes === undefined || Number.isNaN(Number(bytes))) {
    return '—';
  }
  const n = Number(bytes);
  if (!n || n < 0) return '0 B';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}
