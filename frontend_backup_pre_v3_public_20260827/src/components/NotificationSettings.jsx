// frontend/src/components/NotificationSettings.jsx
import React, { useState, useEffect } from 'react';
import { notificationService } from '../services/NotificationService';

function NotificationSettings() {
  const [pushEnabled, setPushEnabled] = useState(false);
  const [permissionStatus, setPermissionStatus] = useState('default');

  useEffect(() => {
    checkPermission();
  }, []);

  const checkPermission = () => {
    if ('Notification' in window) {
      setPermissionStatus(Notification.permission);
      setPushEnabled(Notification.permission === 'granted');
    }
  };

  const enablePush = async () => {
    const granted = await notificationService.requestPermission();
    setPushEnabled(granted);
    setPermissionStatus(Notification.permission);
    
    if (granted) {
      toast.success('🔔 Push notifications enabled!');
    } else {
      toast.error('Push notifications blocked. Please enable in browser settings.');
    }
  };

  const disablePush = () => {
    // Can't disable programmatically, user must do it in browser
    toast.info('To disable notifications, please adjust your browser settings.');
  };

  return (
    <div className="notification-settings">
      <h3>🔔 Notification Settings</h3>
      
      <div className="setting-item">
        <div className="setting-info">
          <label>Push Notifications</label>
          <p>Receive notifications even when the app is closed</p>
        </div>
        <div className="setting-control">
          {permissionStatus === 'granted' ? (
            <button 
              className="toggle-btn active"
              onClick={disablePush}
            >
              ✅ Enabled
            </button>
          ) : (
            <button 
              className="toggle-btn"
              onClick={enablePush}
              disabled={permissionStatus === 'denied'}
            >
              {permissionStatus === 'denied' ? '🚫 Blocked' : '🔕 Enable'}
            </button>
          )}
          {permissionStatus === 'denied' && (
            <span className="help-text">
              Please enable notifications in your browser settings
            </span>
          )}
        </div>
      </div>

      <div className="setting-item">
        <div className="setting-info">
          <label>In-App Notifications</label>
          <p>Show toast notifications while using the app</p>
        </div>
        <div className="setting-control">
          <label className="switch">
            <input type="checkbox" defaultChecked />
            <span className="slider" />
          </label>
        </div>
      </div>

      <div className="setting-item">
        <div className="setting-info">
          <label>Notification Sound</label>
          <p>Play sound when receiving notifications</p>
        </div>
        <div className="setting-control">
          <label className="switch">
            <input type="checkbox" defaultChecked />
            <span className="slider" />
          </label>
        </div>
      </div>

      <div className="setting-item">
        <div className="setting-info">
          <label>Notification Types</label>
          <p>Choose which notifications you want to receive</p>
        </div>
        <div className="setting-control">
          <div className="notification-types">
            <label>
              <input type="checkbox" defaultChecked />
              Document Updates
            </label>
            <label>
              <input type="checkbox" defaultChecked />
              Messages
            </label>
            <label>
              <input type="checkbox" defaultChecked />
              Reviews & Approvals
            </label>
            <label>
              <input type="checkbox" defaultChecked />
              System Alerts
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

export default NotificationSettings;