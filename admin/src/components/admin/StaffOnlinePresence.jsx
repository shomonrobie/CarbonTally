// admin/src/components/admin/StaffOnlinePresence.jsx
import React, { useState, useEffect } from 'react';
import { useRealtime } from '../../context/RealtimeContext';

function StaffOnlinePresence() {
  const { onlineStaff } = useRealtime();
  const [staffList, setStaffList] = useState([]);

  useEffect(() => {
    fetchStaff();
  }, []);

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

  const isOnline = (staffId) => {
    return onlineStaff.includes(staffId);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">👥 Staff Online</h3>
        <span className="text-sm text-green-600">
          {onlineStaff.length} online
        </span>
      </div>
      
      <div className="space-y-2 max-h-60 overflow-y-auto">
        {staffList.map((staff) => (
          <div
            key={staff.id}
            className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50"
          >
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  {staff.first_name?.[0] || staff.email?.[0] || '?'}
                </div>
                <span
                  className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white ${
                    isOnline(staff.id) ? 'bg-green-500' : 'bg-gray-300'
                  }`}
                />
              </div>
              <div>
                <div className="font-medium text-sm">
                  {staff.first_name} {staff.last_name}
                </div>
                <div className="text-xs text-gray-500">{staff.role}</div>
              </div>
            </div>
            <span
              className={`text-xs px-2 py-1 rounded-full ${
                isOnline(staff.id)
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              {isOnline(staff.id) ? '🟢 Online' : '⚪ Offline'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default StaffOnlinePresence;