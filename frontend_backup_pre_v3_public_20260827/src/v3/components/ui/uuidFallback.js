// frontend/src/v3/components/ui/uuidFallback.js
// Minimal dependency-free id generator for UI primitives. Uses crypto.randomUUID
// when available and falls back to a Math.random-based value (ids are only used
// for DOM label/control association — never as security identifiers).
let counter = 0;

export function v4() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  counter += 1;
  return `ct-${Date.now().toString(36)}-${counter.toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}
