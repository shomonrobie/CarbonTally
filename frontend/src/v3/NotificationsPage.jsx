// frontend/src/v3/NotificationsPage.jsx
// D25 — Notifications. Reads the per-recipient /api/v3/notifications surface.
// The backend filters strictly by the caller's user id, so no user can ever
// see another user's notifications.
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listNotifications, markAllNotificationsRead, markNotificationRead } from './api';
import { ErrorState } from './components/StateViews';

const TYPE_LABELS = {
  issue: 'Issue',
  report: 'Report',
  document: 'Document',
  processing: 'Processing',
  general: 'Notification',
};

export default function NotificationsPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState(25);
  const [offset, setOffset] = useState(0);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const load = async (unread, nextLimit = limit, nextOffset = offset) => {
    try {
      const result = await listNotifications({ unreadOnly: unread, limit: nextLimit, offset: nextOffset });
      setItems(result.notifications || []);
      setTotal(typeof result.total === 'number' ? result.total : (result.notifications || []).length);
      setLimit(nextLimit);
      setOffset(nextOffset);
    } catch (e) {
      setError(e.message || 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(unreadOnly); /* eslint-disable-next-line */ }, [unreadOnly, retryCount]);

  const onMarkRead = async (notification) => {
    if (notification.is_read) return;
    try {
      await markNotificationRead(notification.id);
      setItems((prev) => prev.map((n) => (n.id === notification.id ? { ...n, is_read: true } : n)));
    } catch (e) {
      setError(e.message || 'Failed to mark notification read');
    }
  };

  const onMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setNotice('All notifications marked as read.');
    } catch (e) {
      setError(e.message || 'Failed to mark notifications read');
    }
  };

  const unreadCount = items.filter((n) => !n.is_read).length;

  if (loading) return <div className="v3-loading"><div className="spinner" />Loading notifications…</div>;

  return (
    <div className="v3-page">
      <div className="v3-page-header">
        <h1>Notifications</h1>
        <p className="v3-subtitle">
          {unreadCount > 0
            ? `${unreadCount} unread`
            : items.length === 0
              ? ''
              : 'You are all caught up'}
        </p>
      </div>

      {error && <ErrorState inline message={error} onRetry={() => setRetryCount((n) => n + 1)} />}
      {notice && <div className="v3-note">{notice}</div>}

      <div className="v3-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(e) => { setUnreadOnly(e.target.checked); setError(''); }}
            />
            Unread only
          </label>
          <button className="v3-btn v3-btn-sm" onClick={onMarkAllRead} disabled={unreadCount === 0}>
            Mark all as read
          </button>
        </div>

        {items.length === 0 ? (
          <div className="v3-empty">
            {unreadOnly ? 'No unread notifications.' : 'You have no new notifications.'}
          </div>
        ) : (
          <>
            <ul className="v3-notification-list" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {items.map((notification) => (
                <li
                  key={notification.id}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 12,
                    padding: '10px 4px',
                    borderBottom: '1px solid var(--v3-border, #e5e7eb)',
                    opacity: notification.is_read ? 0.65 : 1,
                  }}
                >
                  <span
                    aria-hidden="true"
                    style={{ width: 10, height: 10, borderRadius: '50%', marginTop: 6, flexShrink: 0, background: notification.is_read ? '#9ca3af' : '#0f766e' }}
                  />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: notification.is_read ? 400 : 600 }}>
                      {notification.title || TYPE_LABELS[notification.notification_type] || 'Notification'}
                    </div>
                    {notification.message && (
                      <div className="v3-muted" style={{ whiteSpace: 'pre-wrap' }}>{notification.message}</div>
                    )}
                    <div className="v3-muted">
                      {notification.created_at ? new Date(notification.created_at).toLocaleString() : ''}
                      {notification.notification_type ? ` · ${TYPE_LABELS[notification.notification_type] || notification.notification_type}` : ''}
                    </div>
                    {notification.link && (
                      <Link to={notification.link} className="v3-link" onClick={() => onMarkRead(notification)}>
                        Open
                      </Link>
                    )}
                  </div>
                  {!notification.is_read && (
                    <button className="v3-btn v3-btn-sm" onClick={() => onMarkRead(notification)}>Mark read</button>
                  )}
                </li>
              ))}
            </ul>

            {/* D-P2 — the notifications dataset can grow large; server-side
                pagination (limit/offset/total from the API) keeps the page
                bounded without browser-side paging of an over-broad list. */}
            {total > limit && (
              <div className="ct-table-pagination" style={{ marginTop: 12 }}>
                <span className="ct-table-pagination-count">
                  {total === 0 ? '0 notifications' : `${offset + 1}–${Math.min(total, offset + items.length)} of ${total}`}
                </span>
                <button type="button" className="v3-btn v3-btn-sm" disabled={offset <= 0} onClick={() => load(unreadOnly, limit, Math.max(0, offset - limit))}>← Prev</button>
                <span className="ct-table-pagination-count">Page {Math.floor(offset / limit) + 1} of {Math.max(1, Math.ceil(total / limit))}</span>
                <button type="button" className="v3-btn v3-btn-sm" disabled={offset + limit >= total} onClick={() => load(unreadOnly, limit, offset + limit)}>Next →</button>
                <select className="ct-table-pagination-select" aria-label="Rows per page" value={limit} onChange={(e) => load(unreadOnly, Number(e.target.value), 0)}>
                  {[10, 25, 50, 100].map((s) => <option key={s} value={s}>{s} / page</option>)}
                </select>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
