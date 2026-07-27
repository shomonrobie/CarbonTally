// admin/src/components/LogViewer.jsx
import React, { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';
import toast from 'react-hot-toast';
import {
  FaSearch,
  FaFilter,
  FaDownload,
  FaSync,  // ✅ Changed from FaRefresh to FaSync
  FaEye,
  FaFilePdf,
  FaImage,
  FaUpload,
  FaCheck,
  FaTimes,
  FaExclamationTriangle,
  FaInfoCircle,
  FaUser,
  FaCalendarAlt,
  FaClock,
  FaChartBar,
  FaTable,
  FaRedo  // ✅ Added FaRedo as alternative
} from 'react-icons/fa';
import '../css/LogViewer.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const LogViewer = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [selectedLog, setSelectedLog] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [filters, setFilters] = useState({
    action: '',
    resource_type: '',
    date_from: '',
    date_to: '',
    search: ''
  });
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'chart'
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [limit] = useState(50);

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  // Fetch logs
  const fetchLogs = async () => {
    setLoading(true);
    const token = await getToken();

    try {
      // Build query params
      const params = new URLSearchParams({
        limit: limit,
        offset: (currentPage - 1) * limit
      });
      
      if (filters.action) params.append('action', filters.action);
      if (filters.resource_type) params.append('resource_type', filters.resource_type);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      if (filters.search) params.append('search', filters.search);

      const response = await fetch(`${API_URL}/api/logs?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
        setTotalPages(Math.ceil(data.total / limit) || 1);
      } else {
        toast.error('Failed to fetch logs');
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
      toast.error('Failed to fetch logs');
    } finally {
      setLoading(false);
    }
  };

  // Fetch stats
  const fetchStats = async () => {
    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/logs/analytics/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data.stats);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  // Fetch errors
  const fetchErrors = async () => {
    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/logs/analytics/errors`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        // Handle errors separately
        console.log('Errors:', data.errors);
      }
    } catch (error) {
      console.error('Error fetching errors:', error);
    }
  };

  useEffect(() => {
    fetchLogs();
    fetchStats();
    fetchErrors();
  }, [currentPage, filters.action, filters.resource_type]);

  // Get action icon
  const getActionIcon = (action) => {
    const icons = {
      'document_upload': <FaUpload />,
      'document_approved': <FaCheck className="text-green-500" />,
      'document_rejected': <FaTimes className="text-red-500" />,
      'extraction_success': <FaCheck className="text-green-500" />,
      'extraction_failure': <FaExclamationTriangle className="text-yellow-500" />,
      'error_occurred': <FaExclamationTriangle className="text-red-500" />,
      'manual_entry': <FaEye />,
      'user_login': <FaUser />,
      'user_logout': <FaUser />,
      'staff_review': <FaEye />
    };
    return icons[action] || <FaInfoCircle />;
  };

  // Get action color class
  const getActionColor = (action) => {
    if (action.includes('success') || action.includes('approved')) return 'action-success';
    if (action.includes('failure') || action.includes('error') || action.includes('rejected')) return 'action-error';
    if (action.includes('upload') || action.includes('entry')) return 'action-info';
    return 'action-default';
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Format relative time
  const formatRelativeTime = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  // Render stats cards
  const renderStats = () => {
    if (!stats) return null;

    const statItems = [
      { key: 'total_logs', label: 'Total Logs', icon: <FaTable /> },
      { key: 'pending_reviews', label: 'Pending Reviews', icon: <FaEye /> },
      { key: 'total_uploads', label: 'Total Uploads', icon: <FaUpload /> },
      { key: 'error_count', label: 'Errors', icon: <FaExclamationTriangle /> }
    ];

    return (
      <div className="log-stats">
        {statItems.map(item => (
          <div key={item.key} className="stat-card">
            <div className="stat-icon">{item.icon}</div>
            <div className="stat-info">
              <div className="stat-value">{stats[item.key] || 0}</div>
              <div className="stat-label">{item.label}</div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Render logs table
  const renderLogsTable = () => {
    if (loading) {
      return (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading logs...</p>
        </div>
      );
    }

    if (logs.length === 0) {
      return (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h3>No logs found</h3>
          <p>No activity logs match your filters</p>
        </div>
      );
    }

    return (
      <div className="logs-table-container">
        <table className="logs-table">
          <thead>
            <tr>
              <th>Action</th>
              <th>Resource</th>
              <th>User</th>
              <th>Time</th>
              <th>Details</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} className="log-row">
                <td>
                  <span className={`action-badge ${getActionColor(log.action)}`}>
                    {getActionIcon(log.action)}
                    {log.action?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </td>
                <td>
                  <span className="resource-text">
                    {log.resource_type?.toUpperCase()}
                    {log.resource_id && (
                      <span className="resource-id">#{log.resource_id.slice(0, 8)}</span>
                    )}
                  </span>
                </td>
                <td>
                  <span className="user-email">
                    {log.metadata?.user_email || 'System'}
                  </span>
                </td>
                <td>
                  <div className="time-info">
                    <span className="time-full">{formatDate(log.created_at)}</span>
                    <span className="time-relative">{formatRelativeTime(log.created_at)}</span>
                  </div>
                </td>
                <td>
                  <span className="details-preview">
                    {log.details ? Object.keys(log.details).slice(0, 2).map(key => (
                      <span key={key} className="detail-tag">
                        {key}: {typeof log.details[key] === 'string' ? log.details[key].slice(0, 20) : '...'}
                      </span>
                    )) : 'No details'}
                  </span>
                </td>
                <td>
                  <button
                    className="view-detail-btn"
                    onClick={() => {
                      setSelectedLog(log);
                      setShowDetailModal(true);
                    }}
                  >
                    <FaEye /> View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Render pagination
  const renderPagination = () => {
    if (totalPages <= 1) return null;

    return (
      <div className="pagination">
        <button
          onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
          disabled={currentPage === 1}
          className="page-btn"
        >
          ← Previous
        </button>
        <span className="page-info">
          Page {currentPage} of {totalPages}
        </span>
        <button
          onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
          disabled={currentPage === totalPages}
          className="page-btn"
        >
          Next →
        </button>
      </div>
    );
  };

  // Render filter bar
  const renderFilters = () => (
    <div className="log-filters">
      <div className="filter-group">
        <div className="search-box">
          <FaSearch className="search-icon" />
          <input
            type="text"
            placeholder="Search logs..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            onKeyPress={(e) => e.key === 'Enter' && fetchLogs()}
          />
        </div>

        <select
          value={filters.action}
          onChange={(e) => setFilters({ ...filters, action: e.target.value })}
          className="filter-select"
        >
          <option value="">All Actions</option>
          <option value="document_upload">Document Upload</option>
          <option value="document_approved">Document Approved</option>
          <option value="document_rejected">Document Rejected</option>
          <option value="extraction_success">Extraction Success</option>
          <option value="extraction_failure">Extraction Failure</option>
          <option value="error_occurred">Error Occurred</option>
          <option value="manual_entry">Manual Entry</option>
          <option value="user_login">User Login</option>
          <option value="user_logout">User Logout</option>
          <option value="staff_review">Staff Review</option>
        </select>

        <select
          value={filters.resource_type}
          onChange={(e) => setFilters({ ...filters, resource_type: e.target.value })}
          className="filter-select"
        >
          <option value="">All Resources</option>
          <option value="document">Document</option>
          <option value="user">User</option>
          <option value="batch">Batch</option>
          <option value="organization">Organization</option>
        </select>
      </div>

      <div className="filter-actions">
        <button className="refresh-btn" onClick={fetchLogs}>
          <FaSync /> Refresh  {/* ✅ Changed from FaRefresh to FaSync */}
        </button>
        <button
          className="clear-btn"
          onClick={() => {
            setFilters({ action: '', resource_type: '', date_from: '', date_to: '', search: '' });
            setCurrentPage(1);
          }}
        >
          Clear Filters
        </button>
      </div>
    </div>
  );

  // Render detail modal
  const renderDetailModal = () => {
    if (!showDetailModal || !selectedLog) return null;

    return (
      <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
        <div className="modal-content log-detail-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>📋 Log Details</h3>
            <button className="modal-close" onClick={() => setShowDetailModal(false)}>✕</button>
          </div>
          <div className="modal-body">
            <div className="log-detail-grid">
              <div className="detail-item">
                <label>Action</label>
                <span className={`action-badge ${getActionColor(selectedLog.action)}`}>
                  {getActionIcon(selectedLog.action)}
                  {selectedLog.action?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
              </div>

              <div className="detail-item">
                <label>Resource Type</label>
                <span>{selectedLog.resource_type?.toUpperCase()}</span>
              </div>

              <div className="detail-item">
                <label>Resource ID</label>
                <code className="resource-id-code">{selectedLog.resource_id || 'N/A'}</code>
              </div>

              <div className="detail-item">
                <label>User</label>
                <span>{selectedLog.metadata?.user_email || 'System'}</span>
              </div>

              <div className="detail-item">
                <label>Time</label>
                <span>{formatDate(selectedLog.created_at)}</span>
              </div>

              <div className="detail-item">
                <label>User Agent</label>
                <span className="user-agent">{selectedLog.metadata?.user_agent || 'N/A'}</span>
              </div>
            </div>

            <div className="detail-section">
              <label>Details</label>
              <pre className="detail-json">
                {JSON.stringify(selectedLog.details, null, 2)}
              </pre>
            </div>

            <div className="detail-section">
              <label>Metadata</label>
              <pre className="detail-json">
                {JSON.stringify(selectedLog.metadata, null, 2)}
              </pre>
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn-close" onClick={() => setShowDetailModal(false)}>Close</button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="log-viewer">
      <div className="log-viewer-header">
        <div>
          <h2>📋 Activity Logs</h2>
          <p>Monitor all system activities and user actions</p>
        </div>
        <div className="header-actions">
          <button
            className={`view-toggle ${viewMode === 'table' ? 'active' : ''}`}
            onClick={() => setViewMode('table')}
          >
            <FaTable /> Table
          </button>
          <button
            className={`view-toggle ${viewMode === 'chart' ? 'active' : ''}`}
            onClick={() => setViewMode('chart')}
          >
            <FaChartBar /> Charts
          </button>
        </div>
      </div>

      {renderStats()}
      {renderFilters()}

      {viewMode === 'table' && renderLogsTable()}
      {viewMode === 'chart' && (
        <div className="chart-view">
          <p>Chart view coming soon...</p>
        </div>
      )}

      {renderPagination()}
      {renderDetailModal()}
    </div>
  );
};

export default LogViewer;