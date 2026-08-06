// admin/src/pages/admin/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { 
  FaClipboardList, 
  FaCheckCircle, 
  FaClock, 
  FaStar,
  FaFileAlt,
  FaUsers,
  FaBuilding,
  FaChartLine,
  FaBell,
  FaCircle
} from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import { useRealtime } from '../../context/RealtimeContext';
import StatCard from '../../components/admin/StatCard';
import ActivityChart from '../../components/admin/ActivityChart';
import RecentActivity from '../../components/admin/RecentActivity';
import ReviewStatusChart from '../../components/admin/ReviewStatusChart';

const Dashboard = () => {
  const queryClient = useQueryClient();
  const { isConnected, unreadCount, onlineStaff } = useRealtime();
  const [stats, setStats] = useState({
    pending: 0,
    completed: 0,
    inProgress: 0,
    accuracy: 0,
    totalFiles: 0,
    activeUsers: 0,
    organizations: 0,
    reportsGenerated: 0,
  });

  // Fetch dashboard stats
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: async () => {
      // Get review counts
      const { count: pendingCount } = await supabase
        .from('manual_review_queue')
        .select('*', { count: 'exact', head: true })
        .eq('status', 'pending');

      const { count: completedCount } = await supabase
        .from('manual_review_queue')
        .select('*', { count: 'exact', head: true })
        .eq('status', 'completed');

      const { count: inProgressCount } = await supabase
        .from('manual_review_queue')
        .select('*', { count: 'exact', head: true })
        .eq('status', 'in_progress');

      // Get total files processed (emissions logs)
      const { count: totalFiles } = await supabase
        .from('emissions_logs')
        .select('*', { count: 'exact', head: true });

      // Get active users
      const { count: activeUsers } = await supabase
        .from('organization_members')
        .select('*', { count: 'exact', head: true });

      // Get organizations
      const { count: organizations } = await supabase
        .from('organizations')
        .select('*', { count: 'exact', head: true });

      // Get reports generated (emissions logs grouped by year)
      const { data: reportsData } = await supabase
        .from('emissions_logs')
        .select('start_date')
        .not('start_date', 'is', null);

      const years = new Set();
      reportsData?.forEach(row => {
        if (row.start_date) {
          years.add(row.start_date.substring(0, 4));
        }
      });

      // Calculate accuracy (mock for now)
      const accuracy = 94.7;

      return {
        pending: pendingCount || 0,
        completed: completedCount || 0,
        inProgress: inProgressCount || 0,
        accuracy,
        totalFiles: totalFiles || 0,
        activeUsers: activeUsers || 0,
        organizations: organizations || 0,
        reportsGenerated: years.size || 0,
      };
    },
    refetchInterval: 30000, // Refresh every 30 seconds as fallback
  });

  // ✅ Realtime subscription for queue updates
  useEffect(() => {
    const handleQueueUpdate = (event) => {
      // Refetch stats when queue changes
      queryClient.invalidateQueries(['dashboardStats']);
    };

    // Listen for queue updates via Realtime
    window.addEventListener('queue-updated', handleQueueUpdate);
    window.addEventListener('document-updated', handleQueueUpdate);

    return () => {
      window.removeEventListener('queue-updated', handleQueueUpdate);
      window.removeEventListener('document-updated', handleQueueUpdate);
    };
  }, [queryClient]);

  useEffect(() => {
    if (statsData) {
      setStats(statsData);
    }
  }, [statsData]);

  const statCards = [
    {
      title: 'Pending Reviews',
      value: stats.pending,
      change: '+12%',
      icon: FaClipboardList,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
    {
      title: 'Completed Reviews',
      value: stats.completed,
      change: '+8%',
      icon: FaCheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'In Progress',
      value: stats.inProgress,
      change: '-3%',
      icon: FaClock,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Accuracy Rate',
      value: `${stats.accuracy}%`,
      change: '+2.1%',
      icon: FaStar,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      title: 'Total Files Processed',
      value: stats.totalFiles.toLocaleString(),
      change: '+15.2%',
      icon: FaFileAlt,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
    },
    {
      title: 'Active Users',
      value: stats.activeUsers,
      change: '+5.4%',
      icon: FaUsers,
      color: 'text-pink-600',
      bgColor: 'bg-pink-50',
    },
    {
      title: 'Organizations',
      value: stats.organizations,
      change: '+12',
      icon: FaBuilding,
      color: 'text-teal-600',
      bgColor: 'bg-teal-50',
    },
    {
      title: 'Reports Generated',
      value: stats.reportsGenerated,
      change: '+23%',
      icon: FaChartLine,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
  ];

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header with Realtime Status */}
      <div className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600">Welcome back! Here's what's happening with your carbon management platform.</p>
          </div>
          
          {/* Realtime Status Badge */}
          <div className="flex items-center gap-4">
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              isConnected ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
            }`}>
              <FaCircle className={`text-xs ${isConnected ? 'text-green-500 animate-pulse' : 'text-yellow-500'}`} />
              <span>{isConnected ? 'Live' : 'Connecting...'}</span>
            </div>
            
            {unreadCount > 0 && (
              <div className="flex items-center gap-2 px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
                <FaBell className="text-xs" />
                <span>{unreadCount} new notification{unreadCount > 1 ? 's' : ''}</span>
              </div>
            )}
            
            {onlineStaff.length > 0 && (
              <div className="flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                <FaUsers className="text-xs" />
                <span>{onlineStaff.length} online</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ActivityChart />
        <ReviewStatusChart stats={stats} />
      </div>

      {/* Recent Activity */}
      <RecentActivity />
    </div>
  );
};

export default Dashboard;