// admin/src/components/admin/StaffOnlinePresence.jsx
import React, { useState, useEffect } from 'react';
import { useRealtime } from '../../context/RealtimeContext';
import { supabase } from '../../supabaseClient';
import { FaCircle } from 'react-icons/fa';

const StaffOnlinePresence = () => {
  const { onlineStaff } = useRealtime();
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStaff();
  }, []);

  const fetchStaff = async () => {
    try {
      const { data, error } = await supabase
        .from('staff_profiles')
        .select('id, first_name, last_name, email, role, is_active')
        .eq('is_active', true)
        .order('first_name');

      if (error) throw error;
      setStaffList(data || []);
    } catch (error) {
      console.error('Error fetching staff:', error);
    } finally {
      setLoading(false);
    }
  };

  const isOnline = (staffId) => {
    return onlineStaff.includes(staffId);
  };

  const getInitials = (staff) => {
    const first = staff.first_name?.charAt(0) || '';
    const last = staff.last_name?.charAt(0) || '';
    return (first + last).toUpperCase() || staff.email?.charAt(0)?.toUpperCase() || '?';
  };

  const getRoleColor = (role) => {
    const colors = {
      admin: 'bg-red-100 text-red-700',
      manager: 'bg-blue-100 text-blue-700',
      reviewer: 'bg-green-100 text-green-700',
      staff: 'bg-gray-100 text-gray-700',
    };
    return colors[role] || 'bg-gray-100 text-gray-700';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-40 mb-4"></div>
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-100 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  const onlineCount = staffList.filter(s => isOnline(s.id)).length;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <span>👥</span>
          Staff Online
        </h3>
        <span className="text-sm text-green-600 font-medium">
          {onlineCount} / {staffList.length} online
        </span>
      </div>
      
      <div className="space-y-2 max-h-80 overflow-y-auto">
        {staffList.map((staff) => {
          const online = isOnline(staff.id);
          return (
            <div
              key={staff.id}
              className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="relative flex-shrink-0">
                  <div className="w-9 h-9 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                    {getInitials(staff)}
                  </div>
                  <FaCircle 
                    className={`absolute -bottom-0.5 -right-0.5 text-xs ${
                      online ? 'text-green-500' : 'text-gray-300'
                    }`}
                  />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-sm truncate">
                    {staff.first_name} {staff.last_name}
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    {staff.email}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className={`px-2 py-0.5 rounded-full text-xs ${getRoleColor(staff.role)}`}>
                  {staff.role || 'staff'}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  online 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-gray-100 text-gray-500'
                }`}>
                  {online ? '🟢 Online' : '⚪ Offline'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StaffOnlinePresence;