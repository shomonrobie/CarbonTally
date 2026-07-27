// admin/src/components/AdminAssignment.jsx
import React, { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';
import toast from 'react-hot-toast';
import {
  FaSpinner,
  FaUserPlus,
  FaUser,
  FaCheckCircle,
  FaClock,
  FaExclamationTriangle,
  FaFilePdf,
  FaImage,
  FaFileAlt,
  FaSearch,
  FaTimes,
  FaCalendarAlt,
  FaLayerGroup,
  FaArrowRight
} from 'react-icons/fa';
import '../css/AdminAssignment.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AdminAssignment = () => {
  // State
  const [reviews, setReviews] = useState([]);
  const [staffList, setStaffList] = useState([]);
  const [stats, setStats] = useState({});
  const [staffSummary, setStaffSummary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: 'pending',
    priority: '',
    search: ''
  });
  const [selectedReview, setSelectedReview] = useState(null);
  const [selectedStaff, setSelectedStaff] = useState('');
  const [assignmentNote, setAssignmentNote] = useState('');
  const [deadline, setDeadline] = useState('');
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showBatchAssignModal, setShowBatchAssignModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const limit = 20;

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  // Fetch data
  const fetchData = async () => {
    setLoading(true);
    const token = await getToken();

    try {
      // Fetch available reviews
      const params = new URLSearchParams({
        page: currentPage,
        limit: limit
      });
      if (filters.status) params.append('status', filters.status);
      if (filters.priority) params.append('priority', filters.priority);
      if (filters.search) params.append('search', filters.search);

      const reviewsResponse = await fetch(`${API_URL}/api/admin/assignments/available?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (reviewsResponse.ok) {
        const data = await reviewsResponse.json();
        setReviews(data.items || []);
        setStats(data.stats || {});
        setTotalItems(data.total || 0);
        setTotalPages(data.total_pages || 1);
      }

      // Fetch staff list
      const staffResponse = await fetch(`${API_URL}/api/admin/assignments/staff`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (staffResponse.ok) {
        const data = await staffResponse.json();
        setStaffList(data.staff || []);
      }

      // Fetch stats
      const statsResponse = await fetch(`${API_URL}/api/admin/assignments/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (statsResponse.ok) {
        const data = await statsResponse.json();
        setStaffSummary(data.staff_summary || []);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
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
      const response = await fetch(`${API_URL}/api/admin/assignments/${selectedReview.id}/assign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          staff_user_id: selectedStaff,
          note: assignmentNote,
          deadline: deadline || null
        })
      });

      if (response.ok) {
        toast.success('✅ Review assigned successfully');
        setShowAssignModal(false);
        setSelectedStaff('');
        setAssignmentNote('');
        setDeadline('');
        fetchData();
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

  // Handle batch assign
  const handleBatchAssign = async () => {
    if (!selectedReview?.batch_id || !selectedStaff) {
      toast.error('Please select a staff member');
      return;
    }

    setSubmitting(true);
    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/admin/assignments/batch/${selectedReview.batch_id}/assign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          staff_user_id: selectedStaff,
          note: assignmentNote,
          deadline: deadline || null
        })
      });

      if (response.ok) {
        toast.success('✅ Batch assigned successfully');
        setShowBatchAssignModal(false);
        setShowAssignModal(false);
        setSelectedStaff('');
        setAssignmentNote('');
        setDeadline('');
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to assign batch');
      }
    } catch (error) {
      console.error('Error assigning batch:', error);
      toast.error('Failed to assign batch');
    } finally {
      setSubmitting(false);
    }
  };

  // Get status badge
  const getStatusBadge = (status) => {
    const statusMap = {
      'pending': { label: '⏳ Pending', color: 'status-pending' },
      'assigned': { label: '📌 Assigned', color: 'status-assigned' },
      'in_progress': { label: '🔄 In Progress', color: 'status-in-progress' },
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
    <div className="assignment-stats">
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
    </div>
  );

  // Render staff workload
  const renderStaffWorkload = () => (
    <div className="staff-workload">
      <h4>👥 Staff Workload</h4>
      <div className="workload-grid">
        {staffSummary.map((staff) => (
          <div key={staff.id} className="workload-item">
            <span className="staff-name">{staff.name}</span>
            <div className="workload-bars">
              <div className="workload-bar">
                <div 
                  className="workload-fill" 
                  style={{ 
                    width: `${Math.min((staff.assigned + staff.in_progress) * 10, 100)}%`,
                    background: staff.assigned + staff.in_progress > 3 ? '#ef4444' : '#3b82f6'
                  }} 
                />
              </div>
              <span className="workload-count">
                {staff.assigned + staff.in_progress} ({staff.completed} completed)
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // Render reviews table
  const renderReviewsTable = () => {
    if (loading) {
      return (
        <div className="loading-state">
          <FaSpinner className="spinner" />
          <p>Loading reviews...</p>
        </div>
      );
    }

    if (reviews.length === 0) {
      return (
        <div className="empty-state">
          <div className="empty-icon">🎉</div>
          <h3>No pending reviews</h3>
          <p>All caught up! No documents waiting for assignment.</p>
        </div>
      );
    }

    return (
      <div className="reviews-table-container">
        <table className="reviews-table">
          <thead>
            <tr>
              <th>Document</th>
              <th>Organization</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {reviews.map((review) => {
              const priority = getPriorityBadge(review.priority);
              const status = getStatusBadge(review.status);
              const isBatch = review.batch_id;

              return (
                <tr key={review.id} className="review-row">
                  <td>
                    <div className="doc-info">
                      <span className="doc-icon">{getFileIcon(review.file_type)}</span>
                      <span className="doc-name">{review.file_name}</span>
                      {isBatch && (
                        <span className="batch-tag">
                          <FaLayerGroup /> Batch
                        </span>
                      )}
                    </div>
                  </td>
                  <td>{review.organization_name || 'N/A'}</td>
                  <td>
                    <span className={`priority-badge ${priority.color}`}>
                      {priority.label}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${status.color}`}>
                      {status.label}
                    </span>
                  </td>
                  <td>
                    <div className="date-info">
                      <span>{formatDate(review.created_at)}</span>
                    </div>
                  </td>
                  <td>
                    <div className="action-buttons">
                      {isBatch ? (
                        <button
                          className="btn-assign-batch"
                          onClick={() => {
                            setSelectedReview(review);
                            setShowBatchAssignModal(true);
                          }}
                        >
                          <FaLayerGroup /> Assign Batch
                        </button>
                      ) : (
                        <button
                          className="btn-assign"
                          onClick={() => {
                            setSelectedReview(review);
                            setShowAssignModal(true);
                          }}
                        >
                          <FaUserPlus /> Assign
                        </button>
                      )}
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
    if (!showAssignModal || !selectedReview) return null;

    return (
      <div className="modal-overlay" onClick={() => setShowAssignModal(false)}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>📌 Assign Review</h3>
            <button className="modal-close" onClick={() => setShowAssignModal(false)}>✕</button>
          </div>
          <div className="modal-body">
            <div className="doc-preview">
              <p><strong>Document:</strong> {selectedReview.file_name}</p>
              <p><strong>Organization:</strong> {selectedReview.organization_name || 'N/A'}</p>
              <p><strong>Priority:</strong> {getPriorityBadge(selectedReview.priority).label}</p>
            </div>

            <div className="form-group">
              <label>Assign To *</label>
              <select
                value={selectedStaff}
                onChange={(e) => setSelectedStaff(e.target.value)}
              >
                <option value="">Select staff member...</option>
                {staffList.map((staff) => (
                  <option key={staff.id} value={staff.id}>
                    {staff.name} ({staff.assigned + staff.in_progress} active, {staff.completed} completed)
                  </option>
                ))}
              </select>
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

            <div className="form-group">
              <label><FaCalendarAlt /> Deadline (Optional)</label>
              <input
                type="datetime-local"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
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

  // Render batch assign modal
  const renderBatchAssignModal = () => {
    if (!showBatchAssignModal || !selectedReview) return null;

    return (
      <div className="modal-overlay" onClick={() => setShowBatchAssignModal(false)}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>📦 Assign Batch</h3>
            <button className="modal-close" onClick={() => setShowBatchAssignModal(false)}>✕</button>
          </div>
          <div className="modal-body">
            <div className="doc-preview">
              <p><strong>Batch:</strong> {selectedReview.batch_name || 'Unknown Batch'}</p>
              <p><strong>Organization:</strong> {selectedReview.organization_name || 'N/A'}</p>
              <p><strong>Files:</strong> {selectedReview.batch_progress?.total || 0} files</p>
              <p><strong>Progress:</strong> {selectedReview.batch_progress?.percentage || 0}% complete</p>
            </div>

            <div className="form-group">
              <label>Assign To *</label>
              <select
                value={selectedStaff}
                onChange={(e) => setSelectedStaff(e.target.value)}
              >
                <option value="">Select staff member...</option>
                {staffList.map((staff) => (
                  <option key={staff.id} value={staff.id}>
                    {staff.name} ({staff.assigned + staff.in_progress} active, {staff.completed} completed)
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Assignment Note (Optional)</label>
              <textarea
                value={assignmentNote}
                onChange={(e) => setAssignmentNote(e.target.value)}
                placeholder="Add notes about this batch assignment..."
                rows="2"
              />
            </div>

            <div className="form-group">
              <label><FaCalendarAlt /> Deadline (Optional)</label>
              <input
                type="datetime-local"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
              />
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn-cancel" onClick={() => setShowBatchAssignModal(false)}>
              Cancel
            </button>
            <button
              className="btn-assign-submit"
              onClick={handleBatchAssign}
              disabled={submitting || !selectedStaff}
            >
              {submitting ? <FaSpinner className="spinner" /> : <FaLayerGroup />}
              {submitting ? 'Assigning...' : 'Assign Batch'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="admin-assignment">
      <div className="assignment-header">
        <div>
          <h2>📋 Task Assignment</h2>
          <p>Assign documents and batches to staff members for review</p>
        </div>
        <button className="refresh-btn" onClick={fetchData}>
          🔄 Refresh
        </button>
      </div>

      {renderStats()}
      {renderStaffWorkload()}

      <div className="assignment-filters">
        <div className="filter-group">
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
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

      {renderReviewsTable()}
      {renderPagination()}
      {renderAssignModal()}
      {renderBatchAssignModal()}
    </div>
  );
};

export default AdminAssignment;