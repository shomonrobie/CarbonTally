// frontend/src/components/StaffPresence.jsx
import React, { useState, useEffect } from 'react';
import { useRealtime } from '../context/RealtimeContext';

function StaffPresence({ organization }) {
  const { onlineStaff, isConnected } = useRealtime();
  const [staffList, setStaffList] = useState([]);

  useEffect(() => {
    fetchStaff();
  }, [organization]);

  const fetchStaff = async () => {
    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/admin/staff`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to fetch staff');
      
      const data = await response.json();
      setStaffList(data.staff || []);
      
    } catch (error) {
      console.error('Error fetching staff:', error);
    }
  };

  const getStatus = (staffId) => {
    if (!isConnected) return 'offline';
    return onlineStaff.includes(staffId) ? 'online' : 'offline';
  };

  const getStatusColor = (status) => {
    const colors = {
      'online': '#22c55e',
      'offline': '#94a3b8',
      'away': '#f59e0b',
      'busy': '#ef4444'
    };
    return colors[status] || '#94a3b8';
  };

  const getStatusLabel = (status) => {
    const labels = {
      'online': 'Online',
      'offline': 'Offline',
      'away': 'Away',
      'busy': 'Busy'
    };
    return labels[status] || status;
  };

  return (
    <div className="staff-presence-container">
      <div className="staff-presence-header">
        <h4>👥 Team Online</h4>
        <span className="online-count">
          {staffList.filter(s => getStatus(s.id) === 'online').length} / {staffList.length} online
        </span>
      </div>

      <div className="staff-list">
        {staffList.map(staff => {
          const status = getStatus(staff.id);
          return (
            <div key={staff.id} className="staff-item">
              <div className="staff-avatar">
                <span className="avatar-initial">
                  {staff.first_name?.charAt(0) || staff.email?.charAt(0) || '?'}
                </span>
                <span 
                  className="status-indicator"
                  style={{ backgroundColor: getStatusColor(status) }}
                />
              </div>
              <div className="staff-info">
                <div className="staff-name">
                  {staff.first_name} {staff.last_name}
                </div>
                <div className="staff-role">{staff.role}</div>
              </div>
              <div className="staff-status">
                <span className="status-label">{getStatusLabel(status)}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default StaffPresence;