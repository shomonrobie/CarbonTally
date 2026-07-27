// admin/src/components/StaffReviewQueue.jsx
import React, { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';
import toast from 'react-hot-toast';
import {
  FaSpinner,
  FaCheckCircle,
  FaClock,
  FaUser,
  FaExclamationTriangle,
  FaFilePdf,
  FaImage,
  FaFileAlt,
  FaSearch,
  FaPlay,
  FaEye,
  FaEdit,
  FaSave,
  FaTimes
} from 'react-icons/fa';
import StaffManualEntry from './StaffManualEntry';
import './css/StaffReviewQueue.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const StaffReviewQueue = () => {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    search: ''
  });
  const [selectedReview, setSelectedReview] = useState(null);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const limit = 20;

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  // Fetch my queue
  const fetchMyQueue = async () => {
    setLoading(true);
    const token = await getToken();

    try {
      const params = new URLSearchParams({
        page: currentPage,
        limit: limit
      });
      if (filters.status) params.append('status', filters.status);
      if (filters.priority) params.append('priority', filters.priority);

      const response = await fetch(`${API_URL}/api/admin/reviews/my-queue?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setQueue(data.items || []);
        setStats(data.stats || {});
        setTotalItems(data.total || 0);
        setTotalPages(data.total_pages || 1);
      } else {
        toast.error('Failed to load your queue');
      }
    } catch (error) {
      console.error('Error fetching queue:', error);
      toast.error('Failed to load your queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMyQueue();
  }, [currentPage, filters.status, filters.priority]);

  // Handle start review
  const handleStartReview = async (review) => {
    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/admin/reviews/my-queue/${review.id}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        toast.success('Review started');
        fetchMyQueue();
        // Open manual entry
        setSelectedReview({ ...review, status: 'in_progress' });
        setShowManualEntry(true);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to start review');
      }
    } catch (error) {
      console.error('Error starting review:', error);
      toast.error('Failed to start review');
    }
  };

  // Handle open manual entry
  const handleOpenManualEntry = (review) => {
    setSelectedReview(review);
    setShowManualEntry(true);
  };

  // Handle complete
  const handleComplete = () => {
    setShowManualEntry(false);
    setSelectedReview(null);
    fetchMyQueue();
    toast.success('✅ Review completed!');
  };

  // Handle cancel
  const handleCancel = () => {
    setShowManualEntry(false);
    setSelectedReview(null);
    fetchMyQueue();
  };

  // Get status badge
  const getStatusBadge = (status) => {
    const statusMap = {
      'pending': { label: '⏳ Pending', color: 'status-pending' },
      'assigned': { label: '📌 Assigned', color: 'status-assigned' },
      'in_progress': { label: '🔄 In Progress', color: 'status-in-progress' },
      'ready_for_review': { label: '✅ Ready', color: 'status-ready' },
      'completed': { label: '✅ Completed', color: 'status-completed' },
      'rejected': { label: '❌ Rejected', color: 'status-rejected' }
    };
    return statusMap[status] || statusMap['pending'];
  };

  // Get priority badge
  const getPriorityBadge = (priority) => {
    const priorityMap = {
      2: { label: '🔴 High', color: 'priority-high' },
      1: { label: '🟠 Medium', color: 'priority-medium' },
      0: { label: '🟢 Low', color: 'priority-low' }
    };
    return priorityMap[priority] || priorityMap[0];
  };

  // Get file icon
  const getFileIcon = (fileType) => {
    const icons = {
      'PDF': <FaFilePdf />,
      'IMAGE': <FaImage />,
      'CSV': <FaFileAlt />,
      'EXCEL': <FaFileAlt />,
      'OTHER': <FaFileAlt />
    };
    return icons[fileType] || icons['OTHER'];
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Render stats
  const renderStats = () => (
    <div className="queue-stats">
      <div className="stat-card">
        <div className="stat-value">{stats.pending || 0}</div>
        <div className="stat-label">⏳ Pending</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.in_progress || 0}</div>
        <div className="stat-label">🔄 In Progress</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.completed || 0}</div>
        <div className="stat-label">✅ Completed</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.rejected || 0}</div>
        <div className="stat-label">❌ Rejected</div>
      </div>
      <div className="stat-card highlight">
        <div className="stat-value">{stats.high_priority || 0}</div>
        <div className="stat-label">🔴 High Priority</div>
      </div>
    </div>
  );

  // Render queue list
  const renderQueueList = () => {
    if (loading) {
      return (
        <div className="loading-state">
          <FaSpinner className="spinner" />
          <p>Loading your queue...</p>
        </div>
      );
    }

    if (queue.length === 0) {
      return (
        <div className="empty-state">
          <div className="empty-icon">🎉</div>
          <h3>All caught up!</h3>
          <p>No items in your review queue</p>
        </div>
      );
    }

    return (
      <div className="queue-list">
        {queue.map((item) => {
          const status = getStatusBadge(item.status);
          const priority = getPriorityBadge(item.priority);
          const canStart = item.status === 'pending' || item.status === 'assigned';
          const canContinue = item.status === 'in_progress';

          return (
            <div key={item.id} className={`queue-card ${item.status}`}>
              <div className="queue-card-header">
                <div className="doc-info">
                  <span className="doc-icon">{getFileIcon(item.file_type)}</span>
                  <span className="doc-name">{item.file_name}</span>
                  {item.batch_name && (
                    <span className="batch-tag">📦 {item.batch_name}</span>
                  )}
                </div>
                <div className="queue-card-actions">
                  {canStart && (
                    <button
                      className="btn-start"
                      onClick={() => handleStartReview(item)}
                    >
                      <FaPlay /> Start Review
                    </button>
                  )}
                  {canContinue && (
                    <button
                      className="btn-continue"
                      onClick={() => handleOpenManualEntry(item)}
                    >
                      <FaEdit /> Continue
                    </button>
                  )}
                  <button
                    className="btn-view"
                    onClick={() => handleOpenManualEntry(item)}
                  >
                    <FaEye /> View
                  </button>
                </div>
              </div>

              <div className="queue-card-body">
                <div className="queue-card-meta">
                  <span className={`priority-badge ${priority.color}`}>
                    {priority.label}
                  </span>
                  <span className={`status-badge ${status.color}`}>
                    {status.label}
                  </span>
                  <span className="org-name">
                    🏢 {item.organization_name || 'N/A'}
                  </span>
                  {item.batch_progress && (
                    <span className="batch-progress">
                      📊 {item.batch_progress.percentage}% complete
                    </span>
                  )}
                </div>
                <div className="queue-card-footer">
                  <span className="created-at">
                    📅 {formatDate(item.created_at)}
                  </span>
                  {item.customer_notes && (
                    <span className="customer-note-badge">
                      📝 Has customer notes
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
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
        >
          ← Previous
        </button>
        <span className="page-info">
          Page {currentPage} of {totalPages} ({totalItems} items)
        </span>
        <button
          onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
          disabled={currentPage === totalPages}
        >
          Next →
        </button>
      </div>
    );
  };

  // Main render
  return (
    <div className="staff-review-queue">
      {showManualEntry && selectedReview ? (
        <StaffManualEntry
          review={selectedReview}
          onComplete={handleComplete}
          onCancel={handleCancel}
        />
      ) : (
        <>
          <div className="queue-header">
            <div>
              <h2>📋 My Review Queue</h2>
              <p>Documents assigned to you for manual review</p>
            </div>
            <button className="refresh-btn" onClick={fetchMyQueue}>
              🔄 Refresh
            </button>
          </div>

          {renderStats()}

          <div className="queue-filters">
            <div className="filter-group">
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              >
                <option value="">All Status</option>
                <option value="pending">⏳ Pending</option>
                <option value="assigned">📌 Assigned</option>
                <option value="in_progress">🔄 In Progress</option>
                <option value="completed">✅ Completed</option>
                <option value="rejected">❌ Rejected</option>
              </select>
              <select
                value={filters.priority}
                onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
              >
                <option value="">All Priorities</option>
                <option value="2">🔴 High</option>
                <option value="1">🟠 Medium</option>
                <option value="0">🟢 Low</option>
              </select>
            </div>
          </div>

          {renderQueueList()}
          {renderPagination()}
        </>
      )}
    </div>
  );
};

export default StaffReviewQueue;