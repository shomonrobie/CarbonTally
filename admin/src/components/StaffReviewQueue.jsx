// admin/src/components/StaffReviewQueue.jsx
import React, { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';
import toast from 'react-hot-toast';
import {
  FaSpinner,
  FaCheckCircle,
  FaClock,
  FaUser,
  FaUserPlus,
  FaExclamationTriangle,
  FaFilePdf,
  FaImage,
  FaFileAlt,
  FaSearch,
  FaFilter,
  FaEye,
  FaEdit,
  FaCheck,
  FaTimes,
  FaPlay,
  FaStop,
  FaUserCheck,
  FaCalendarAlt,
  FaBolt
} from 'react-icons/fa';
import '../css/StaffReviewQueue.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const StaffReviewQueue = () => {
  // State
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    search: ''
  });
  const [selectedReview, setSelectedReview] = useState(null);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [staffList, setStaffList] = useState([]);
  const [selectedStaff, setSelectedStaff] = useState('');
  const [assignmentNote, setAssignmentNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const limit = 20;

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  // Fetch queue
  const fetchQueue = async () => {
    setLoading(true);
    const token = await getToken();

    try {
      const params = new URLSearchParams({
        page: currentPage,
        limit: limit
      });
      if (filters.status) params.append('status', filters.status);
      if (filters.priority) params.append('priority', filters.priority);
      if (filters.search) params.append('search', filters.search);

      const response = await fetch(`${API_URL}/api/admin/reviews/queue?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setQueue(data.items || []);
        setStats(data.stats || {});
        setTotalItems(data.total || 0);
        setTotalPages(data.total_pages || 1);
      } else {
        toast.error('Failed to load review queue');
      }
    } catch (error) {
      console.error('Error fetching queue:', error);
      toast.error('Failed to load review queue');
    } finally {
      setLoading(false);
    }
  };

  // Fetch staff list for assignment
  const fetchStaff = async () => {
    const token = await getToken();
    try {
      const response = await fetch(`${API_URL}/api/admin/reviews/staff/workload`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setStaffList(data.staff || []);
      }
    } catch (error) {
      console.error('Error fetching staff:', error);
    }
  };

  useEffect(() => {
    fetchQueue();
    fetchStaff();
  }, [currentPage, filters.status, filters.priority]);

  // Handle assign
  const handleAssign = async () => {
    if (!selectedReview || !selectedStaff) {
      toast.error('Please select a staff member');
      return;
    }

    setSubmitting(true);
    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/admin/reviews/${selectedReview.id}/assign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          assigned_to: selectedStaff,
          note: assignmentNote
        })
      });

      if (response.ok) {
        toast.success('Review assigned successfully');
        setShowAssignModal(false);
        setSelectedStaff('');
        setAssignmentNote('');
        fetchQueue();
        fetchStaff();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to assign review');
      }
    } catch (error) {
      console.error('Error assigning review:', error);
      toast.error('Failed to assign review');
    } finally {
      setSubmitting(false);
    }
  };

  // Handle start review
  const handleStartReview = async (review) => {
    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/admin/reviews/${review.id}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        toast.success('Review started');
        fetchQueue();
        fetchStaff();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to start review');
      }
    } catch (error) {
      console.error('Error starting review:', error);
      toast.error('Failed to start review');
    }
  };

  // Handle complete review
  const handleCompleteReview = async (review) => {
    if (!window.confirm('Mark this review as complete?')) return;

    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/admin/reviews/${review.id}/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          notes: `Completed by ${review.assigned_to_name || 'Staff'}`
        })
      });

      if (response.ok) {
        toast.success('Review completed and ready for customer');
        fetchQueue();
        fetchStaff();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to complete review');
      }
    } catch (error) {
      console.error('Error completing review:', error);
      toast.error('Failed to complete review');
    }
  };

  // Get status badge
  const getStatusBadge = (status) => {
    const statusMap = {
      'pending': { label: '⏳ Pending', color: 'status-pending' },
      'assigned': { label: '📌 Assigned', color: 'status-assigned' },
      'in_progress': { label: '🔄 In Progress', color: 'status-in-progress' },
      'ready_for_review': { label: '✅ Ready for Review', color: 'status-ready' },
      'completed': { label: '✅ Completed', color: 'status-completed' },
      'rejected': { label: '❌ Rejected', color: 'status-rejected' }
    };
    return statusMap[status] || { label: status, color: 'status-pending' };
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

  // Calculate time elapsed
  const timeElapsed = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const now = new Date();
    const diff = Math.floor((now - date) / (1000 * 60 * 60));
    if (diff < 1) return 'Just now';
    if (diff < 24) return `${diff}h ago`;
    return `${Math.floor(diff / 24)}d ago`;
  };

  // Render stats
  const renderStats = () => (
    <div className="queue-stats">
      <div className="stat-card">
        <div className="stat-value">{stats.pending || 0}</div>
        <div className="stat-label">⏳ Pending</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.assigned || 0}</div>
        <div className="stat-label">📌 Assigned</div>
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

  // Render queue table
  const renderQueueTable = () => {
    if (loading) {
      return (
        <div className="loading-state">
          <FaSpinner className="spinner" />
          <p>Loading queue...</p>
        </div>
      );
    }

    if (queue.length === 0) {
      return (
        <div className="empty-state">
          <div className="empty-icon">🎉</div>
          <h3>All caught up!</h3>
          <p>No items in the review queue</p>
        </div>
      );
    }

    return (
      <div className="queue-table-container">
        <table className="queue-table">
          <thead>
            <tr>
              <th>Document</th>
              <th>Organization</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Assigned To</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {queue.map((item) => {
              const status = getStatusBadge(item.status);
              const priority = getPriorityBadge(item.priority);
              const canAssign = item.status === 'pending' || item.status === 'assigned';
              const canStart = item.status === 'assigned' && item.assigned_to === supabase.auth.user()?.id;
              const canComplete = item.status === 'in_progress' && item.assigned_to === supabase.auth.user()?.id;

              return (
                <tr key={item.id} className={`queue-item ${item.sla_breached ? 'sla-breached' : ''}`}>
                  <td>
                    <div className="doc-info">
                      <span className="doc-icon">{getFileIcon(item.file_type)}</span>
                      <span className="doc-name" title={item.file_name}>
                        {item.file_name.length > 30 ? item.file_name.substring(0, 30) + '...' : item.file_name}
                      </span>
                      {item.batch_name && (
                        <span className="batch-tag">📦 {item.batch_name}</span>
                      )}
                    </div>
                  </td>
                  <td>{item.organization_name || 'N/A'}</td>
                  <td>
                    <span className={`priority-badge ${priority.color}`}>
                      {priority.label}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${status.color}`}>
                      {status.label}
                    </span>
                    {item.sla_breached && (
                      <span className="sla-warning" title="SLA Breached">
                        <FaExclamationTriangle />
                      </span>
                    )}
                  </td>
                  <td>
                    {item.assigned_to_name ? (
                      <span className="staff-name">
                        <FaUser className="staff-icon" />
                        {item.assigned_to_name}
                      </span>
                    ) : (
                      <span className="staff-name unassigned">Unassigned</span>
                    )}
                  </td>
                  <td>
                    <div className="date-info">
                      <span>{formatDate(item.created_at)}</span>
                      <span className="time-ago">{timeElapsed(item.created_at)}</span>
                    </div>
                  </td>
                  <td>
                    <div className="action-buttons">
                      {canAssign && (
                        <button
                          className="btn-assign"
                          onClick={() => {
                            setSelectedReview(item);
                            setShowAssignModal(true);
                          }}
                          title="Assign"
                        >
                          <FaUserPlus />
                        </button>
                      )}
                      {canStart && (
                        <button
                          className="btn-start"
                          onClick={() => handleStartReview(item)}
                          title="Start Review"
                        >
                          <FaPlay />
                        </button>
                      )}
                      {canComplete && (
                        <button
                          className="btn-complete"
                          onClick={() => handleCompleteReview(item)}
                          title="Complete Review"
                        >
                          <FaCheck />
                        </button>
                      )}
                      <button
                        className="btn-view"
                        onClick={() => {
                          setSelectedReview(item);
                          setShowReviewModal(true);
                        }}
                        title="View Details"
                      >
                        <FaEye />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
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

  // Render assign modal
  const renderAssignModal = () => {
    if (!showAssignModal) return null;

    return (
      <div className="modal-overlay" onClick={() => setShowAssignModal(false)}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>📌 Assign Review</h3>
            <button className="modal-close" onClick={() => setShowAssignModal(false)}>✕</button>
          </div>
          <div className="modal-body">
            <div className="doc-info-preview">
              <p><strong>Document:</strong> {selectedReview?.file_name}</p>
              <p><strong>Organization:</strong> {selectedReview?.organization_name}</p>
              <p><strong>Priority:</strong> {selectedReview && getPriorityBadge(selectedReview.priority).label}</p>
            </div>

            <div className="form-group">
              <label>Select Staff Member *</label>
              <select
                value={selectedStaff}
                onChange={(e) => setSelectedStaff(e.target.value)}
              >
                <option value="">Select a staff member...</option>
                {staffList.map((staff) => (
                  <option key={staff.id} value={staff.id}>
                    {staff.name} ({staff.assigned_reviews} assigned, {staff.total_completed} completed)
                  </option>
                ))}
              </select>
            </div>

            <div className="staff-workload">
              <h4>Staff Workload</h4>
              <div className="workload-grid">
                {staffList.slice(0, 5).map((staff) => (
                  <div key={staff.id} className="workload-item">
                    <span className="staff-name">{staff.name}</span>
                    <div className="workload-bars">
                      <div className="workload-bar">
                        <div className="workload-fill" style={{ width: `${Math.min(staff.workload_score * 10, 100)}%` }} />
                      </div>
                      <span className="workload-count">{staff.assigned_reviews} reviews</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Assignment Note (Optional)</label>
              <textarea
                value={assignmentNote}
                onChange={(e) => setAssignmentNote(e.target.value)}
                placeholder="Add notes about this assignment..."
                rows="2"
              />
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn-cancel" onClick={() => setShowAssignModal(false)}>
              Cancel
            </button>
            <button
              className="btn-assign-submit"
              onClick={handleAssign}
              disabled={submitting || !selectedStaff}
            >
              {submitting ? <FaSpinner className="spinner" /> : <FaUserPlus />}
              {submitting ? 'Assigning...' : 'Assign Review'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Render review details modal
  const renderReviewModal = () => {
    if (!showReviewModal || !selectedReview) return null;

    return (
      <div className="modal-overlay" onClick={() => setShowReviewModal(false)}>
        <div className="modal-content review-details" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>📄 Review Details</h3>
            <button className="modal-close" onClick={() => setShowReviewModal(false)}>✕</button>
          </div>
          <div className="modal-body">
            <div className="review-info-grid">
              <div className="info-group">
                <label>File</label>
                <p>{selectedReview.file_name}</p>
              </div>
              <div className="info-group">
                <label>Type</label>
                <p>{selectedReview.file_type}</p>
              </div>
              <div className="info-group">
                <label>Organization</label>
                <p>{selectedReview.organization_name || 'N/A'}</p>
              </div>
              <div className="info-group">
                <label>Priority</label>
                <p>{getPriorityBadge(selectedReview.priority).label}</p>
              </div>
              <div className="info-group">
                <label>Status</label>
                <p>{getStatusBadge(selectedReview.status).label}</p>
              </div>
              <div className="info-group">
                <label>Assigned To</label>
                <p>{selectedReview.assigned_to_name || 'Unassigned'}</p>
              </div>
              <div className="info-group">
                <label>Created</label>
                <p>{formatDate(selectedReview.created_at)}</p>
              </div>
              <div className="info-group">
                <label>Started</label>
                <p>{selectedReview.started_at ? formatDate(selectedReview.started_at) : 'Not started'}</p>
              </div>
              {selectedReview.batch_name && (
                <div className="info-group full-width">
                  <label>Batch</label>
                  <p>{selectedReview.batch_name}</p>
                  {selectedReview.batch_progress && (
                    <div className="batch-progress">
                      <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${selectedReview.batch_progress.percentage}%` }} />
                      </div>
                      <span>{selectedReview.batch_progress.percentage}%</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {selectedReview.customer_notes && (
              <div className="customer-notes">
                <h4>📝 Customer Notes</h4>
                <p>{selectedReview.customer_notes}</p>
              </div>
            )}

            {selectedReview.auto_extraction_result && (
              <div className="extraction-data">
                <h4>🤖 Auto-Extraction Data</h4>
                <pre>{JSON.stringify(selectedReview.auto_extraction_result, null, 2)}</pre>
              </div>
            )}
          </div>
          <div className="modal-footer">
            <button className="btn-cancel" onClick={() => setShowReviewModal(false)}>
              Close
            </button>
            {selectedReview.file_url && (
              <a
                href={selectedReview.file_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-download"
              >
                📥 Download
              </a>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="staff-review-queue">
      <div className="queue-header">
        <div>
          <h2>📋 Staff Review Queue</h2>
          <p>Manage documents requiring manual review and staff attention</p>
        </div>
        <button className="refresh-btn" onClick={() => { fetchQueue(); fetchStaff(); }}>
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
          <div className="search-box">
            <FaSearch className="search-icon" />
            <input
              type="text"
              placeholder="Search files..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </div>
        </div>
      </div>

      {renderQueueTable()}
      {renderPagination()}
      {renderAssignModal()}
      {renderReviewModal()}
    </div>
  );
};

export default StaffReviewQueue;