// admin/src/components/admin/LiveQueueStats.jsx
import React, { useState, useEffect } from 'react';
import { supabase } from '../../supabaseClient';

function LiveQueueStats() {
  const [stats, setStats] = useState({
    pending: 0,
    assigned: 0,
    in_progress: 0,
    completed: 0,
    rejected: 0,
  });
  const [lastUpdated, setLastUpdated] = useState(new Date());

  useEffect(() => {
    fetchStats();
    
    // Listen for queue updates via Realtime
    const handleQueueUpdate = (event) => {
      fetchStats();
    };
    
    window.addEventListener('queue-updated', handleQueueUpdate);
    
    // Poll every 30 seconds as fallback
    const interval = setInterval(fetchStats, 30000);
    
    return () => {
      window.removeEventListener('queue-updated', handleQueueUpdate);
      clearInterval(interval);
    };
  }, []);

  const fetchStats = async () => {
    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/admin/queue/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to fetch queue stats');
      
      const data = await response.json();
      setStats(data.stats || {});
      setLastUpdated(new Date());
      
    } catch (error) {
      console.error('Error fetching queue stats:', error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': '#f59e0b',
      'assigned': '#3b82f6',
      'in_progress': '#8b5cf6',
      'completed': '#22c55e',
      'rejected': '#ef4444',
    };
    return colors[status] || '#94a3b8';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">📊 Live Queue Stats</h3>
        <span className="text-xs text-gray-400">
          Updated {lastUpdated.toLocaleTimeString()}
        </span>
      </div>
      
      <div className="grid grid-cols-5 gap-4">
        {Object.entries(stats).map(([key, value]) => (
          <div key={key} className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold" style={{ color: getStatusColor(key) }}>
              {value}
            </div>
            <div className="text-sm text-gray-600 capitalize mt-1">
              {key.replace('_', ' ')}
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 flex items-center gap-2 text-xs text-gray-400">
        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        Live updates enabled
      </div>
    </div>
  );
}

export default LiveQueueStats;