// admin/src/components/admin/LiveQueueStats.jsx
import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { supabase } from '../../supabaseClient';

const LiveQueueStats = () => {
  const queryClient = useQueryClient();
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const { data: queueStats, isLoading } = useQuery({
    queryKey: ['queueStats'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('manual_review_queue')
        .select('status')
        .in('status', ['pending', 'assigned', 'in_progress', 'completed', 'rejected']);

      if (error) throw error;

      const stats = {
        pending: 0,
        assigned: 0,
        in_progress: 0,
        completed: 0,
        rejected: 0,
      };

      data?.forEach(item => {
        if (stats.hasOwnProperty(item.status)) {
          stats[item.status]++;
        }
      });

      stats.total = Object.values(stats).reduce((a, b) => a + b, 0);

      return stats;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // ✅ Realtime subscription for queue updates
  useEffect(() => {
    const channel = supabase.channel('queue-stats');
    
    channel.on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'manual_review_queue'
    }, () => {
      queryClient.invalidateQueries(['queueStats']);
      setLastUpdated(new Date());
    });
    
    channel.subscribe();
    
    return () => {
      channel.unsubscribe();
    };
  }, [queryClient]);

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-500',
      assigned: 'bg-blue-500',
      in_progress: 'bg-purple-500',
      completed: 'bg-green-500',
      rejected: 'bg-red-500',
    };
    return colors[status] || 'bg-gray-500';
  };

  const getStatusLabel = (status) => {
    const labels = {
      pending: 'Pending',
      assigned: 'Assigned',
      in_progress: 'In Progress',
      completed: 'Completed',
      rejected: 'Rejected',
    };
    return labels[status] || status;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
        <div className="grid grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <span className="text-green-500">●</span>
          Live Queue Stats
        </h3>
        <span className="text-xs text-gray-400">
          Updated {lastUpdated.toLocaleTimeString()}
        </span>
      </div>
      
      <div className="grid grid-cols-5 gap-4">
        {Object.entries(queueStats || {}).map(([key, value]) => {
          if (key === 'total') return null;
          return (
            <div key={key} className="text-center p-3 bg-gray-50 rounded-lg">
              <div className={`text-2xl font-bold ${getStatusColor(key).replace('bg-', 'text-')}`}>
                {value}
              </div>
              <div className="text-sm text-gray-600 capitalize mt-1">
                {getStatusLabel(key)}
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="mt-4 flex items-center gap-2 text-xs text-gray-400">
        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        {queueStats?.total || 0} total items in queue
      </div>
    </div>
  );
};

export default LiveQueueStats;