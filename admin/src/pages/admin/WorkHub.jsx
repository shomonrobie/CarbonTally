// admin/src/pages/admin/WorkHub.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useRealtime } from '../../context/RealtimeContext';
import { supabase } from '../../supabaseClient';
import { 
  FaBell, 
  FaTasks, 
  FaComments, 
  FaAt, 
  FaCheckCircle, 
  FaClock,
  FaUsers,
  FaFileAlt,
  FaExclamationTriangle,
  FaChartLine,
  FaUserCheck,
  FaThumbsUp,
  FaArrowUp,
  FaArrowDown,
  FaUserCog,
  FaShieldAlt,
  FaClipboardCheck,
  FaRobot,
  FaEye,
  FaEdit,
  FaCheckDouble,
  FaHome,
} from 'react-icons/fa';
import toast from 'react-hot-toast';

const WorkHub = () => {
  // ✅ Use your AuthContext
  const { user, isStaff, loading: authLoading } = useAuth();
  const { isConnected, onlineStaff, unreadCount } = useRealtime();
  const [loading, setLoading] = useState(true);
  const [staffProfile, setStaffProfile] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [workData, setWorkData] = useState({
    notifications: [],
    tasks: [],
    messages: [],
    approvals: [],
    processing: [],
    staffWorkload: [],
  });
  const [counts, setCounts] = useState({
    notifications: 0,
    tasks: 0,
    messages: 0,
    approvals: 0,
    processing: 0,
  });

  // ✅ Fetch staff profile on mount
  useEffect(() => {
    if (user?.email) {
      fetchStaffProfile(user.email);
    }
  }, [user]);

  // ✅ Fetch staff profile
  const fetchStaffProfile = async (email) => {
    try {
      const { data, error } = await supabase
        .from('staff_profiles')
        .select('*, roles(name, permissions)')
        .eq('email', email)
        .maybeSingle();

      if (error) throw error;
      
      if (data) {
        setStaffProfile(data);
        setUserRole(data.role);
        console.log('👤 Staff profile loaded:', data.role);
      }
    } catch (error) {
      console.error('Error fetching staff profile:', error);
    }
  };

  // ✅ Role-based permissions
  const permissions = {
    isAdmin: userRole === 'admin',
    isDataExtractor: userRole === 'data_extractor',
    isDataApprover: userRole === 'data_approver',
    isStaff: userRole === 'staff' || isStaff,
    isViewer: userRole === 'viewer',
  };

  // ✅ Role-based access control
  const canView = {
    notifications: true,
    tasks: permissions.isAdmin || permissions.isStaff || permissions.isDataExtractor,
    messages: true,
    approvals: permissions.isAdmin || permissions.isDataApprover,
    processing: permissions.isAdmin || permissions.isStaff || permissions.isDataExtractor,
    staffList: permissions.isAdmin || permissions.isStaff,
    reports: permissions.isAdmin || permissions.isDataApprover,
    settings: permissions.isAdmin,
    workload: permissions.isAdmin,
  };

  // ✅ Fetch work data
  useEffect(() => {
    if (user?.email) {
      fetchWorkData();
    }
  }, [user, userRole]);

  // ✅ Realtime subscriptions
  useEffect(() => {
    if (!user?.id) return;

    const channel = supabase.channel('work-hub');
    
    // Notifications
    channel.on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'notifications',
      filter: `user_id=eq.${user.id}`
    }, (payload) => {
      setWorkData(prev => ({
        ...prev,
        notifications: [payload.new, ...prev.notifications].slice(0, 20)
      }));
      setCounts(prev => ({
        ...prev,
        notifications: prev.notifications + 1
      }));
      showToast('🔔 New notification', payload.new.title);
    });

    // Messages
    channel.on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'messages',
      filter: `receiver_id=eq.${user.id}`
    }, (payload) => {
      setWorkData(prev => ({
        ...prev,
        messages: [payload.new, ...prev.messages].slice(0, 20)
      }));
      setCounts(prev => ({
        ...prev,
        messages: prev.messages + 1
      }));
      showToast('💬 New message', payload.new.content?.substring(0, 50) || 'New message');
    });

    // Queue updates for staff
    if (permissions.isStaff || permissions.isDataExtractor) {
      channel.on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: 'manual_review_queue',
        filter: `assigned_to=eq.${user.id}`
      }, () => {
        fetchWorkData();
      });
    }

    // Approvals for admin/approver
    if (permissions.isAdmin || permissions.isDataApprover) {
      channel.on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'customer_verifications',
        filter: `status=eq.pending`
      }, () => {
        fetchWorkData();
      });
    }

    channel.subscribe();

    return () => {
      channel.unsubscribe();
    };
  }, [user, userRole]);

  const fetchWorkData = async () => {
    try {
      setLoading(true);
      
      const userId = user?.id;
      const userEmail = user?.email;

      // ✅ Notifications
      const { data: notifications } = await supabase
        .from('notifications')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
        .limit(10);

      // ✅ Tasks (role-based)
      let tasksQuery = supabase
        .from('manual_review_queue')
        .select('*')
        .in('status', ['pending', 'assigned', 'in_progress'])
        .order('created_at', { ascending: false })
        .limit(5);

      if (permissions.isStaff || permissions.isDataExtractor) {
        tasksQuery = tasksQuery.eq('assigned_to', userId);
      }

      const { data: tasks } = await tasksQuery;

      // ✅ Messages
      const { data: messages } = await supabase
        .from('messages')
        .select('*, sender:sender_id(email, first_name, last_name)')
        .or(`sender_id.eq.${userId},receiver_id.eq.${userId}`)
        .order('created_at', { ascending: false })
        .limit(5);

      // ✅ Approvals (Admin & Data Approver only)
      let approvals = [];
      if (permissions.isAdmin || permissions.isDataApprover) {
        const { data: approvalsData } = await supabase
          .from('customer_verifications')
          .select('*, customer_documents(file_name)')
          .eq('status', 'pending')
          .order('created_at', { ascending: false })
          .limit(5);
        approvals = approvalsData || [];
      }

      // ✅ Processing (Admin, Staff, Data Extractor)
      let processing = [];
      if (permissions.isAdmin || permissions.isStaff || permissions.isDataExtractor) {
        const { data: processingData } = await supabase
          .from('customer_documents')
          .select('*')
          .in('status', ['uploaded', 'processing', 'extracted'])
          .order('upload_date', { ascending: false })
          .limit(10);
        processing = processingData || [];
      }

      // ✅ Staff workload (Admin only)
      let staffWorkload = [];
      if (permissions.isAdmin) {
        const { data: workload } = await supabase
          .from('staff_workload')
          .select('*, staff_profiles(first_name, last_name, email, role)')
          .order('date', { ascending: false })
          .limit(5);
        staffWorkload = workload || [];
      }

      setWorkData({
        notifications: notifications || [],
        tasks: tasks || [],
        messages: messages || [],
        approvals: approvals,
        processing: processing,
        staffWorkload: staffWorkload,
      });

      setCounts({
        notifications: notifications?.filter(n => !n.is_read)?.length || 0,
        tasks: tasks?.length || 0,
        messages: messages?.filter(m => !m.is_read)?.length || 0,
        approvals: approvals?.length || 0,
        processing: processing?.length || 0,
      });

    } catch (error) {
      console.error('Error fetching work data:', error);
      toast.error('Failed to load work hub');
    } finally {
      setLoading(false);
    }
  };

  const showToast = (title, message) => {
    toast.custom((t) => (
      <div 
        className={`work-hub-toast ${t.visible ? 'animate-slide-in' : ''}`}
        onClick={() => toast.dismiss(t.id)}
      >
        <div className="toast-header">
          <span className="toast-icon">🔔</span>
          <span className="toast-title">{title}</span>
        </div>
        <div className="toast-body">{message}</div>
      </div>
    ), { duration: 5000 });
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': '#f59e0b',
      'assigned': '#3b82f6',
      'in_progress': '#8b5cf6',
      'processing': '#06b6d4',
      'extracted': '#10b981',
      'uploaded': '#f59e0b',
      'completed': '#22c55e',
      'rejected': '#ef4444',
    };
    return colors[status] || '#94a3b8';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'pending': '⏳',
      'assigned': '📌',
      'in_progress': '⚙️',
      'processing': '⚙️',
      'extracted': '📋',
      'uploaded': '📤',
      'completed': '✅',
      'rejected': '❌',
    };
    return icons[status] || '📄';
  };

  const getRoleDisplay = (role) => {
    const roleMap = {
      'admin': 'Administrator',
      'data_extractor': 'Data Extractor',
      'data_approver': 'Data Approver',
      'staff': 'Staff',
      'viewer': 'Viewer',
    };
    return roleMap[role] || role;
  };

  const getRoleIcon = (role) => {
    const icons = {
      'admin': <FaShieldAlt className="text-red-500" />,
      'data_extractor': <FaRobot className="text-blue-500" />,
      'data_approver': <FaCheckDouble className="text-green-500" />,
      'staff': <FaUserCog className="text-purple-500" />,
      'viewer': <FaEye className="text-gray-500" />,
    };
    return icons[role] || <FaUserCog />;
  };

  const getRoleColor = (role) => {
    const colors = {
      'admin': 'bg-red-100 text-red-700',
      'data_extractor': 'bg-blue-100 text-blue-700',
      'data_approver': 'bg-green-100 text-green-700',
      'staff': 'bg-purple-100 text-purple-700',
      'viewer': 'bg-gray-100 text-gray-700',
    };
    return colors[role] || 'bg-gray-100 text-gray-700';
  };

  if (authLoading || loading) {
    return (
      <div className="work-hub-loading">
        <div className="loading-spinner"></div>
        <p>Loading Work Hub...</p>
      </div>
    );
  }

  return (
    <div className="work-hub">
      {/* Header with Role Badge */}
      <div className="work-hub-header">
        <div>
          <h1>🏢 Work Hub</h1>
          <div className="header-subtitle">
            <span className={`user-role-badge ${getRoleColor(userRole)}`}>
              {getRoleIcon(userRole)} {getRoleDisplay(userRole)}
            </span>
            <span className="user-name-badge">
              👤 {staffProfile?.first_name || user?.email?.split('@')[0] || 'User'}
            </span>
          </div>
        </div>
        <div className="work-hub-status">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
          <span>{isConnected ? '🟢 Live' : '🔴 Offline'}</span>
          <span className="staff-count">👥 {onlineStaff.length} online</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="work-hub-stats">
        {canView.notifications && (
          <div className="stat-card" style={{ borderColor: '#3b82f6' }}>
            <div className="stat-icon" style={{ background: '#eff6ff' }}>
              <FaBell className="text-blue-500" />
            </div>
            <div className="stat-info">
              <div className="stat-value">{counts.notifications}</div>
              <div className="stat-label">Notifications</div>
            </div>
            {counts.notifications > 0 && (
              <div className="stat-badge new">New</div>
            )}
          </div>
        )}

        {canView.tasks && (
          <div className="stat-card" style={{ borderColor: '#f59e0b' }}>
            <div className="stat-icon" style={{ background: '#fef3c7' }}>
              <FaTasks className="text-yellow-500" />
            </div>
            <div className="stat-info">
              <div className="stat-value">{counts.tasks}</div>
              <div className="stat-label">Tasks</div>
            </div>
            {counts.tasks > 0 && (
              <div className="stat-badge pending">Pending</div>
            )}
          </div>
        )}

        {canView.messages && (
          <div className="stat-card" style={{ borderColor: '#8b5cf6' }}>
            <div className="stat-icon" style={{ background: '#ede9fe' }}>
              <FaComments className="text-purple-500" />
            </div>
            <div className="stat-info">
              <div className="stat-value">{counts.messages}</div>
              <div className="stat-label">Messages</div>
            </div>
            {counts.messages > 0 && (
              <div className="stat-badge new">New</div>
            )}
          </div>
        )}

        {canView.approvals && (
          <div className="stat-card" style={{ borderColor: '#10b981' }}>
            <div className="stat-icon" style={{ background: '#d1fae5' }}>
              <FaCheckCircle className="text-green-500" />
            </div>
            <div className="stat-info">
              <div className="stat-value">{counts.approvals}</div>
              <div className="stat-label">Approvals</div>
            </div>
            {counts.approvals > 0 && (
              <div className="stat-badge pending">Pending</div>
            )}
          </div>
        )}

        {canView.processing && (
          <div className="stat-card" style={{ borderColor: '#06b6d4' }}>
            <div className="stat-icon" style={{ background: '#cffafe' }}>
              <FaClock className="text-cyan-500" />
            </div>
            <div className="stat-info">
              <div className="stat-value">{counts.processing}</div>
              <div className="stat-label">Processing</div>
            </div>
            <div className="stat-badge active">Active</div>
          </div>
        )}
      </div>

      {/* Main Content Grid */}
      <div className="work-hub-grid">
        {/* Activity Feed */}
        <div className="work-hub-panel activity-feed">
          <div className="panel-header">
            <h3>📋 Recent Activity</h3>
            <span className="panel-badge">Live</span>
          </div>
          <div className="panel-content">
            {workData.processing.slice(0, 5).map((item) => (
              <div key={item.id} className="activity-item">
                <div 
                  className="activity-icon"
                  style={{ backgroundColor: getStatusColor(item.status) }}
                >
                  {getStatusIcon(item.status)}
                </div>
                <div className="activity-content">
                  <div className="activity-text">
                    <span className="activity-file">{item.file_name}</span>
                    <span className="activity-status">{item.status}</span>
                  </div>
                  <div className="activity-time">
                    {new Date(item.upload_date).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {workData.processing.length === 0 && (
              <div className="empty-state">No recent activity</div>
            )}
          </div>
        </div>

        {/* Tasks */}
        {canView.tasks && (
          <div className="work-hub-panel tasks-panel">
            <div className="panel-header">
              <h3>📌 My Tasks</h3>
              <span className="panel-badge">{counts.tasks} pending</span>
            </div>
            <div className="panel-content">
              {workData.tasks.slice(0, 5).map((task) => (
                <div key={task.id} className="task-item">
                  <div className="task-info">
                    <div className="task-name">{task.file_name}</div>
                    <div className="task-meta">
                      <span className={`task-status ${task.status}`}>
                        {task.status}
                      </span>
                      {task.priority > 1 && (
                        <span className="task-priority high">🔴 High</span>
                      )}
                    </div>
                  </div>
                  <div className="task-actions">
                    {task.status === 'assigned' && (
                      <button className="btn-sm btn-primary">Start</button>
                    )}
                    {task.status === 'in_progress' && (
                      <button className="btn-sm btn-success">Complete</button>
                    )}
                  </div>
                </div>
              ))}
              {workData.tasks.length === 0 && (
                <div className="empty-state">No pending tasks</div>
              )}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="work-hub-panel messages-panel">
          <div className="panel-header">
            <h3>💬 Messages</h3>
            <span className="panel-badge">{counts.messages} new</span>
          </div>
          <div className="panel-content">
            {workData.messages.slice(0, 5).map((msg) => (
              <div key={msg.id} className="message-item">
                <div className="message-avatar">
                  {msg.sender?.first_name?.[0] || 'U'}
                </div>
                <div className="message-content">
                  <div className="message-sender">
                    {msg.sender?.first_name || 'Unknown'}
                  </div>
                  <div className="message-text">{msg.content}</div>
                </div>
                {!msg.is_read && (
                  <div className="message-unread">●</div>
                )}
              </div>
            ))}
            {workData.messages.length === 0 && (
              <div className="empty-state">No messages</div>
            )}
          </div>
        </div>

        {/* Approvals */}
        {canView.approvals && (
          <div className="work-hub-panel approvals-panel">
            <div className="panel-header">
              <h3>✓ Pending Approvals</h3>
              <span className="panel-badge">{counts.approvals} pending</span>
            </div>
            <div className="panel-content">
              {workData.approvals.slice(0, 5).map((approval) => (
                <div key={approval.id} className="approval-item">
                  <div className="approval-info">
                    <div className="approval-file">
                      {approval.customer_documents?.file_name || 'Unknown'}
                    </div>
                    <div className="approval-meta">
                      <span className="approval-status pending">⏳ Pending</span>
                    </div>
                  </div>
                  <div className="approval-actions">
                    <button className="btn-sm btn-success">Approve</button>
                    <button className="btn-sm btn-danger">Reject</button>
                  </div>
                </div>
              ))}
              {workData.approvals.length === 0 && (
                <div className="empty-state">No pending approvals</div>
              )}
            </div>
          </div>
        )}

        {/* Staff Online */}
        {canView.staffList && (
          <div className="work-hub-panel staff-panel">
            <div className="panel-header">
              <h3>👥 Online Staff</h3>
              <span className="panel-badge">{onlineStaff.length} online</span>
            </div>
            <div className="panel-content staff-list">
              {onlineStaff.slice(0, 10).map((staffId, index) => (
                <div key={index} className="staff-item">
                  <div className="staff-avatar">
                    <span className="avatar-letter">S</span>
                    <span className="online-dot" />
                  </div>
                  <div className="staff-name">Staff {index + 1}</div>
                  <div className="staff-status">🟢 Online</div>
                </div>
              ))}
              {onlineStaff.length === 0 && (
                <div className="empty-state">No staff online</div>
              )}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="work-hub-panel quick-actions">
          <div className="panel-header">
            <h3>⚡ Quick Actions</h3>
          </div>
          <div className="panel-content action-grid">
            {(permissions.isAdmin || permissions.isStaff || permissions.isDataExtractor) && (
              <button className="action-btn" onClick={() => window.location.href = '/admin/reviews'}>
                <FaTasks /> New Review
              </button>
            )}
            {permissions.isAdmin && (
              <>
                <button className="action-btn" onClick={() => window.location.href = '/admin/assignments'}>
                  <FaUserCheck /> Assign Task
                </button>
                <button className="action-btn" onClick={() => window.location.href = '/admin/analytics'}>
                  <FaChartLine /> View Reports
                </button>
                <button className="action-btn" onClick={() => window.location.href = '/admin/settings'}>
                  <FaCog /> Settings
                </button>
              </>
            )}
            {(permissions.isDataApprover || permissions.isAdmin) && (
              <button className="action-btn" onClick={() => window.location.href = '/admin/defra'}>
                <FaClipboardCheck /> Review Data
              </button>
            )}
            {permissions.isDataExtractor && (
              <button className="action-btn" onClick={() => window.location.href = '/admin/extraction'}>
                <FaRobot /> Start Extraction
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkHub;