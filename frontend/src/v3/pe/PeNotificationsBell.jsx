// frontend/src/v3/pe/PeNotificationsBell.jsx
// WS3 / D40 — minimal notification entry point inside the dedicated PEShell.
// Reads the canonical V3 notification API scoped to the authenticated PE user;
// list/read/read-all only. Notification links are informational — every target
// resource re-authorizes the caller independently (notifications are never an
// access-control mechanism).
import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../api';
import Icon from '../components/ui/Icon';

export default function PeNotificationsBell() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);
  const [error, setError] = useState('');
  const wrapRef = useRef(null);

  const load = async () => {
    try {
      const inbox = await listNotifications({ unreadOnly: true, limit: 1 });
      setUnread(Number(inbox?.total) || 0);
      const all = await listNotifications({ limit: 20 });
      setItems(all?.notifications || []);
      setError('');
    } catch (_e) {
      setError('Unable to load notifications.');
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!open) return undefined;
    const onDocClick = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, [open]);

  const read = async (id) => {
    try {
      await markNotificationRead(id);
      await load();
    } catch (_e) { setError('Could not update notification.'); }
  };

  const readAll = async () => {
    try {
      await markAllNotificationsRead();
      await load();
    } catch (_e) { setError('Could not update notifications.'); }
  };

  const openTarget = (link) => {
    if (link && link.startsWith('/')) navigate(link);
    setOpen(false);
  };

  return (
    <div className="pe-bell-wrap" ref={wrapRef}>
      <button
        type="button"
        className="v3-nav-icon-btn pe-bell-btn"
        aria-label="Notifications"
        aria-expanded={open}
        onClick={() => { if (!open) load(); setOpen(!open); }}
      >
        <Icon name="notifications" size={17} aria-hidden="true" />
        {unread > 0 && <span className="pe-bell-badge">{unread > 99 ? '99+' : unread}</span>}
      </button>

      {open && (
        <div className="pe-bell-panel" role="dialog" aria-label="Notifications">
          <div className="pe-bell-head">
            <strong>Notifications</strong>
            <button type="button" className="v3-nav-link" onClick={readAll}>
              Mark all read
            </button>
          </div>
          {error && <div className="pe-bell-empty">{error}</div>}
          {!error && items.length === 0 && (
            <div className="pe-bell-empty">You have no notifications.</div>
          )}
          <ul className="pe-bell-list">
            {items.map((n) => (
              <li key={n.id} className={`pe-bell-item${n.is_read ? '' : ' unread'}`}>
                <button
                  type="button"
                  className="pe-bell-item-main"
                  onClick={() => openTarget(n.link)}
                >
                  <span className="pe-bell-title">{n.title || 'Notification'}</span>
                  {n.message && <span className="pe-bell-msg">{n.message}</span>}
                </button>
                {!n.is_read && (
                  <button
                    type="button"
                    className="pe-bell-item-read"
                    aria-label="Mark read"
                    onClick={() => read(n.id)}
                  >
                    ✓
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
