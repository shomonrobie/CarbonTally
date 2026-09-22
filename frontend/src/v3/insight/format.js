// frontend/src/v3/insight/format.js
// CarbonTally Insight I6 — small display helpers (no business logic).

/** Local date/time for an ISO timestamp; `null` for a missing/invalid value. */
export function formatTimestamp(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString();
}

/** The title a conversation is listed under (never an empty label). */
export function conversationTitle(conversation) {
  const title = conversation && conversation.title;
  if (title && String(title).trim()) return String(title).trim();
  return 'Untitled conversation';
}
