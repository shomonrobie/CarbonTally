import React, { useState, useEffect } from 'react';
import { FaCheckCircle, FaClipboardList, FaUserPlus, FaExclamationTriangle } from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import { formatDistanceToNow } from 'date-fns';

const RecentActivity = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecentActivity();
  }, []);

  const fetchRecentActivity = async () => {
    try {
      // Fetch recent reviews
      const { data: reviews, error: reviewsError } = await supabase
        .from('manual_review_queue')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(10);

      if (reviews) {
        const formattedActivities = reviews.map(review => ({
          id: review.id,
          type: 'review',
          icon: review.status === 'completed' ? FaCheckCircle : FaClipboardList,
          iconColor: review.status === 'completed' ? 'text-green-600' : 'text-yellow-600',
          title: `${review.status === 'completed' ? '✅' : '📋'} Review #${review.id.slice(0, 6)} ${review.status === 'completed' ? 'completed' : 'queued'}`,
          description: `${review.file_name || 'Document'} - ${review.data_type || 'Unknown type'}`,
          time: formatDistanceToNow(new Date(review.created_at), { addSuffix: true }),
          status: review.status,
        }));

        setActivities(formattedActivities.slice(0, 5));
      }
    } catch (error) {
      console.error('Error fetching activities:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="font-semibold text-gray-900">🔄 Recent Activity</h3>
        </div>
        <div className="card-body">
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">🔄 Recent Activity</h3>
          <p className="text-sm text-gray-500">Latest updates from the system</p>
        </div>
        <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
          View All →
        </button>
      </div>
      <div className="card-body">
        {activities.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No recent activity</p>
        ) : (
          <div className="space-y-4">
            {activities.map((activity) => (
              <div key={activity.id} className="flex items-start gap-3 pb-4 border-b border-gray-100 last:border-0 last:pb-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  activity.status === 'completed' ? 'bg-green-50' : 'bg-yellow-50'
                }`}>
                  <activity.icon className={`${activity.iconColor} text-sm`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                  <p className="text-sm text-gray-600 truncate">{activity.description}</p>
                  <p className="text-xs text-gray-400 mt-1">{activity.time}</p>
                </div>
                <span className={`badge ${
                  activity.status === 'completed' ? 'badge-success' :
                  activity.status === 'in_progress' ? 'badge-info' :
                  'badge-warning'
                }`}>
                  {activity.status || 'Pending'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RecentActivity;