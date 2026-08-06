// frontend/src/components/ActivityFeed.jsx
import React, { useState, useEffect } from 'react';
import { useRealtime } from '../context/RealtimeContext';
import { supabase } from '../supabaseClient';
import toast from 'react-hot-toast';

function ActivityFeed({ organization }) {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const { isConnected } = useRealtime();

  useEffect(() => {
    fetchActivities();
    
    // Subscribe to new activities via Realtime
    const channel = supabase.channel(`org:${organization?.id}`);
    
    channel.on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'activity_feed',
      filter: `organization_id=eq.${organization?.id}`
    }, (payload) => {
      setActivities(prev => [payload.new, ...prev]);
    });
    
    channel.subscribe();
    
    return () => {
      channel.unsubscribe();
    };
  }, [organization]);

  const fetchActivities = async () => {
    if (!organization) return;
    
    try {
      setLoading(true);
      
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/activity-feed?organization_id=${organization.id}&limit=50`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to fetch activities');
      
      const data = await response.json();
      setActivities(data.activities || []);
      
    } catch (error) {
      console.error('Error fetching activities:', error);
      toast.error('Failed to load activity feed');
    } finally {
      setLoading(false);
    }
  };

  const getActivityIcon = (type) => {
    const icons = {
      'document_uploaded': '📤',
      'document_processed': '⚙️',
      'document_extracted': '📋',
      'document_approved': '✅',
      'document_rejected': '❌',
      'document_verified': '🔍',
      'message_sent': '💬',
      'review_assigned': '📌',
      'review_completed': '✔️',
      'emissions_logged': '📊',
      'report_generated': '📄',
      'staff_joined': '👤',
      'staff_left': '👋'
    };
    return icons[type] || '📌';
  };

  const getActivityColor = (type) => {
    const colors = {
      'document_uploaded': '#3b82f6',
      'document_processed': '#8b5cf6',
      'document_extracted': '#06b6d4',
      'document_approved': '#22c55e',
      'document_rejected': '#ef4444',
      'document_verified': '#f59e0b',
      'message_sent': '#3b82f6',
      'review_assigned': '#f59e0b',
      'review_completed': '#22c55e',
      'emissions_logged': '#10b981',
      'report_generated': '#8b5cf6'
    };
    return colors[type] || '#94a3b8';
  };

  const getActivityText = (activity) => {
    const { event_type, event_data } = activity;
    
    switch (event_type) {
      case 'document_uploaded':
        return `${event_data.user_name} uploaded "${event_data.file_name}"`;
      case 'document_processed':
        return `"${event_data.file_name}" processing started`;
      case 'document_extracted':
        return `"${event_data.file_name}" extraction completed`;
      case 'document_approved':
        return `${event_data.user_name} approved "${event_data.file_name}"`;
      case 'document_rejected':
        return `${event_data.user_name} rejected "${event_data.file_name}"`;
      case 'document_verified':
        return `${event_data.user_name} verified "${event_data.file_name}"`;
      case 'message_sent':
        return `${event_data.user_name} sent a message`;
      case 'review_assigned':
        return `Review assigned to ${event_data.assigned_to}`;
      case 'review_completed':
        return `Review completed by ${event_data.user_name}`;
      case 'emissions_logged':
        return `${event_data.user_name} logged ${event_data.kg_co2e} kgCO2e`;
      case 'report_generated':
        return `${event_data.user_name} generated ${event_data.report_type} report`;
      default:
        return `${event_type}: ${JSON.stringify(event_data)}`;
    }
  };

  const formatTime = (timestamp) => {
    const now = new Date();
    const then = new Date(timestamp);
    const diff = now - then;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;
    return then.toLocaleDateString();
  };

  if (loading) {
    return <div className="loading-state">Loading activity...</div>;
  }

  return (
    <div className="activity-feed-container">
      <div className="activity-feed-header">
        <h3>📋 Activity Feed</h3>
        <div className="realtime-badge">
          <span className={`live-dot ${isConnected ? 'active' : ''}`} />
          {isConnected ? 'Live' : 'Offline'}
        </div>
      </div>

      <div className="activity-list">
        {activities.length === 0 ? (
          <div className="empty-state">No recent activity</div>
        ) : (
          activities.map((activity, index) => (
            <div key={activity.id || index} className="activity-item">
              <div 
                className="activity-icon"
                style={{ backgroundColor: getActivityColor(activity.event_type) }}
              >
                {getActivityIcon(activity.event_type)}
              </div>
              <div className="activity-content">
                <div className="activity-text">
                  {getActivityText(activity)}
                </div>
                <div className="activity-time">
                  {formatTime(activity.created_at)}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default ActivityFeed;