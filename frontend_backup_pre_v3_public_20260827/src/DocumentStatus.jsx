// DocumentStatus.jsx - Complete with Pagination, Filter, Search, Sort

import React, { useState, useEffect, useMemo } from 'react';
import { supabase } from './supabaseClient';
import toast from 'react-hot-toast';
import './css/DocumentStatus.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const DocumentStatus = ({ organization }) => {
  // State
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  
  // Filter/Search/Sort state
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('uploaded_at');
  const [sortOrder, setSortOrder] = useState('desc');
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [pageSizeOptions] = useState([10, 20, 50, 100]);

  // Review modal state
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  // Build query params
  const buildQueryParams = () => {
    const params = new URLSearchParams();
    if (filterStatus !== 'all') params.append('status', filterStatus);
    if (searchTerm) params.append('search', searchTerm);
    if (sortBy) params.append('sort_by', sortBy);
    if (sortOrder) params.append('sort_order', sortOrder);
    params.append('limit', limit);
    params.append('offset', (currentPage - 1) * limit);
    return params.toString();
  };

  // Fetch documents with pagination, filter, search
  const fetchDocuments = async () => {
  if (!organization?.id) return;
  
  try {
    // ✅ Use Supabase directly
    const { data, error } = await supabase
      .from('organization_files')
      .select('*')
      .eq('organization_id', organization.id)
      .eq('is_active', true)
      .order('uploaded_at', { ascending: false })
      .limit(10);

    if (error) {
      console.error('❌ Supabase error:', error);
      throw new Error('Failed to fetch documents');
    }

    setDocuments(data || []);
    console.log(`✅ Documents fetched: ${data?.length || 0}`);
    
  } catch (error) {
    console.error('Error fetching documents:', error);
    setDocuments([]);
  }
};


  // Fetch stats only
  const fetchStats = async () => {
    if (!organization?.id) return;
    
    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/customer-documents?organization_id=${organization.id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
      
    // try {
    //   const response = await fetch(`${API_URL}/api/documents/stats`, {
    //     headers: { 'Authorization': `Bearer ${token}` }
    //   });

      if (response.ok) {
        const data = await response.json();
        setStats(data.stats || {});
        console.log(`✅ DocumentStatus fetched: ${data?.length || 0}`);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  // Fetch on filter/ search/ sort/ page change
  useEffect(() => {
    if (organization?.id) {
      fetchDocuments();
      fetchStats();
    }
  }, [
    organization?.id, 
    filterStatus, 
    searchTerm, 
    sortBy, 
    sortOrder, 
    currentPage, 
    limit
  ]);

  // Handle search with debounce
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (organization?.id) {
        setCurrentPage(1); // Reset to first page on search
        fetchDocuments();
      }
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  // Handle review action
  const handleReviewAction = async (action) => {
    if (!selectedDocument) return;

    setSubmitting(true);
    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/documents/${selectedDocument.id}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          action: action,
          notes: reviewNotes
        })
      });

      if (response.ok) {
        toast.success(`Document ${action === 'approve' ? 'approved' : 'rejected'} successfully!`);
        setShowReviewModal(false);
        setSelectedDocument(null);
        setReviewNotes('');
        fetchDocuments();
        fetchStats();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to process review');
      }
    } catch (error) {
      console.error('Error reviewing document:', error);
      toast.error('Failed to process review');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'uploaded': { label: '📤 Uploaded', color: 'status-uploaded' },
      'processing': { label: '⏳ Processing', color: 'status-processing' },
      'staff_review': { label: '🔄 Staff Review', color: 'status-staff-review' },
      'ready_for_review': { label: '📝 Ready for Review', color: 'status-ready' },
      'approved': { label: '✅ Approved', color: 'status-approved' },
      'rejected': { label: '❌ Rejected', color: 'status-rejected' }
    };
    return statusMap[status] || { label: status, color: 'status-uploaded' };
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileIcon = (fileType) => {
    const icons = {
      'PDF': '📄',
      'IMAGE': '🖼️',
      'CSV': '📊',
      'EXCEL': '📊',
      'SPREADSHEET': '📊',
      'OTHER': '📁'
    };
    return icons[fileType] || '📁';
  };

  // Stats render
  const renderStats = () => {
    if (!stats) return null;

    const statItems = [
      { key: 'uploaded', label: '📤 Uploaded', color: '#64748b' },
      { key: 'processing', label: '⏳ Processing', color: '#f59e0b' },
      { key: 'staff_review', label: '🔄 Staff Review', color: '#8b5cf6' },
      { key: 'ready_for_review', label: '📝 Ready for Review', color: '#3b82f6' },
      { key: 'approved', label: '✅ Approved', color: '#22c55e' },
      { key: 'rejected', label: '❌ Rejected', color: '#ef4444' },
    ];

    return (
      <div className="document-stats">
        {statItems.map(item => (
          <div key={item.key} className="stat-card">
            <div className="stat-value" style={{ color: item.color }}>
              {stats[item.key] || 0}
            </div>
            <div className="stat-label">{item.label}</div>
          </div>
        ))}
      </div>
    );
  };

  // Sort control
  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
    setCurrentPage(1);
  };

  // Render documents table
  const renderDocuments = () => {
    if (loading) {
      return (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading documents...</p>
        </div>
      );
    }

    if (documents.length === 0) {
      return (
        <div className="empty-state">
          <div className="empty-icon">📄</div>
          <h3>No documents found</h3>
          <p>
            {searchTerm || filterStatus !== 'all' 
              ? 'Try adjusting your filters or search terms.'
              : 'Upload your first document to get started.'}
          </p>
        </div>
      );
    }

    return (
      <div className="documents-table-container">
        <table className="documents-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('name')} style={{ cursor: 'pointer' }}>
                Document {sortBy === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('file_type')} style={{ cursor: 'pointer' }}>
                Type {sortBy === 'file_type' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('size_bytes')} style={{ cursor: 'pointer' }}>
                Size {sortBy === 'size_bytes' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('status')} style={{ cursor: 'pointer' }}>
                Status {sortBy === 'status' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('uploaded_at')} style={{ cursor: 'pointer' }}>
                Uploaded {sortBy === 'uploaded_at' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map(doc => {
              const status = getStatusBadge(doc.status);
              return (
                <tr key={doc.id} className="document-row">
                  <td>
                    <div className="doc-name">
                      <span className="doc-icon">{getFileIcon(doc.file_type)}</span>
                      <span className="doc-title" title={doc.name}>
                        {doc.name.length > 30 ? doc.name.substring(0, 30) + '...' : doc.name}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className="doc-type-badge">{doc.file_type || 'OTHER'}</span>
                  </td>
                  <td>{formatFileSize(doc.size_bytes || 0)}</td>
                  <td>
                    <span className={`status-badge ${status.color}`}>
                      {status.label}
                    </span>
                  </td>
                  <td>
                    {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td>
                    <div className="doc-actions">
                      {doc.status === 'ready_for_review' && (
                        <button
                          className="action-btn review-btn"
                          onClick={() => {
                            setSelectedDocument(doc);
                            setShowReviewModal(true);
                          }}
                        >
                          📝 Review
                        </button>
                      )}
                      <button
                        className="action-btn view-btn"
                        onClick={() => {
                          window.open(`${API_URL}/api/organizations/files/${doc.id}/download`, '_blank');
                        }}
                      >
                        👁️ View
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

  // Pagination render
  const renderPagination = () => {
    if (totalPages <= 1) return null;

    const pageNumbers = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage < maxVisiblePages - 1) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(i);
    }

    return (
      <div className="pagination-container">
        <div className="pagination-info">
          <span>
            Showing {((currentPage - 1) * limit) + 1} to{' '}
            {Math.min(currentPage * limit, totalItems)} of {totalItems} items
          </span>
          <div className="pagination-size">
            <label>Rows per page:</label>
            <select
              value={limit}
              onChange={(e) => {
                setLimit(Number(e.target.value));
                setCurrentPage(1);
              }}
            >
              {pageSizeOptions.map(size => (
                <option key={size} value={size}>{size}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="pagination-controls">
          <button
            onClick={() => setCurrentPage(1)}
            disabled={currentPage === 1}
            className="page-btn"
          >
            ««
          </button>
          <button
            onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
            className="page-btn"
          >
            «
          </button>
          
          {startPage > 1 && <span className="page-ellipsis">…</span>}
          
          {pageNumbers.map(num => (
            <button
              key={num}
              onClick={() => setCurrentPage(num)}
              className={`page-btn ${currentPage === num ? 'active' : ''}`}
            >
              {num}
            </button>
          ))}
          
          {endPage < totalPages && <span className="page-ellipsis">…</span>}
          
          <button
            onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
            className="page-btn"
          >
            »
          </button>
          <button
            onClick={() => setCurrentPage(totalPages)}
            disabled={currentPage === totalPages}
            className="page-btn"
          >
            »»
          </button>
        </div>
      </div>
    );
  };

  // Clear all filters
  const clearFilters = () => {
    setFilterStatus('all');
    setSearchTerm('');
    setSortBy('uploaded_at');
    setSortOrder('desc');
    setCurrentPage(1);
  };

  return (
    <div className="document-status-container">
      {/* Header */}
      <div className="document-header">
        <div>
          <h2>📄 Document Status</h2>
          <p className="subtitle">Track and review your uploaded documents</p>
        </div>
        <div className="header-actions">
          <button
            className="refresh-btn"
            onClick={() => { fetchDocuments(); fetchStats(); }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Stats */}
      {renderStats()}

      {/* Filters */}
      <div className="document-filters">
        <div className="filter-group">
          <select
            value={filterStatus}
            onChange={(e) => {
              setFilterStatus(e.target.value);
              setCurrentPage(1);
            }}
            className="filter-select"
          >
            <option value="all">📊 All Documents</option>
            <option value="uploaded">📤 Uploaded</option>
            <option value="processing">⏳ Processing</option>
            <option value="staff_review">🔄 Staff Review</option>
            <option value="ready_for_review">📝 Ready for Review</option>
            <option value="approved">✅ Approved</option>
            <option value="rejected">❌ Rejected</option>
          </select>
          
          <div className="search-box">
            <input
              type="text"
              placeholder="Search by filename..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            {searchTerm && (
              <button
                className="search-clear"
                onClick={() => setSearchTerm('')}
              >
                ✕
              </button>
            )}
          </div>
        </div>
        
        <div className="filter-actions">
          <button
            className="clear-btn"
            onClick={clearFilters}
          >
            Clear Filters
          </button>
          <span className="filter-count">
            {totalItems} document{totalItems !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Documents Table */}
      {renderDocuments()}

      {/* Pagination */}
      {renderPagination()}

      {/* Review Modal */}
      {showReviewModal && selectedDocument && (
        <div className="modal-overlay" onClick={() => setShowReviewModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📝 Review Document</h3>
              <button
                className="modal-close"
                onClick={() => setShowReviewModal(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="doc-info">
                <p><strong>File:</strong> {selectedDocument.name}</p>
                <p><strong>Type:</strong> {selectedDocument.file_type}</p>
                <p><strong>Uploaded:</strong> {selectedDocument.uploaded_at ? new Date(selectedDocument.uploaded_at).toLocaleString() : 'N/A'}</p>
                <p><strong>Status:</strong> {getStatusBadge(selectedDocument.status).label}</p>
                {selectedDocument.status === 'ready_for_review' && selectedDocument.metadata?.extraction_result && (
                  <div className="extraction-preview">
                    <p><strong>Extracted Data:</strong></p>
                    <pre>{JSON.stringify(selectedDocument.metadata.extraction_result, null, 2)}</pre>
                  </div>
                )}
              </div>
              <div className="form-group">
                <label>Notes (Optional)</label>
                <textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Add any notes about this document..."
                  className="modal-textarea"
                  rows="3"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button
                className="btn-reject"
                onClick={() => handleReviewAction('reject')}
                disabled={submitting}
              >
                {submitting ? 'Processing...' : '❌ Reject'}
              </button>
              <button
                className="btn-approve"
                onClick={() => handleReviewAction('approve')}
                disabled={submitting}
              >
                {submitting ? 'Processing...' : '✅ Approve'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentStatus;