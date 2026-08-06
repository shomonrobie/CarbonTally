// frontend/src/components/DocumentStatus.jsx
import React, { useState, useEffect } from 'react';
import { useRealtime, useDocumentStatus } from '../context/RealtimeContext';
import { supabase } from '../supabaseClient';
import toast from 'react-hot-toast';

function DocumentStatus({ organization }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const { isConnected } = useRealtime();
  const { documents: realtimeDocs, statusCounts } = useDocumentStatus();

  useEffect(() => {
    fetchDocuments();
  }, [organization]);

  useEffect(() => {
    // Update from Realtime
    if (realtimeDocs.length > 0) {
      setDocuments(realtimeDocs);
    }
  }, [realtimeDocs]);

  const fetchDocuments = async () => {
    if (!organization) return;
    
    try {
      setLoading(true);
      
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/customer-documents?organization_id=${organization.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to fetch documents');
      
      const data = await response.json();
      setDocuments(data.documents || []);
      
    } catch (error) {
      console.error('Error fetching documents:', error);
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': '#f59e0b',
      'processing': '#3b82f6',
      'extracted': '#8b5cf6',
      'organized': '#06b6d4',
      'approved': '#22c55e',
      'rejected': '#ef4444',
      'uploaded': '#f59e0b'
    };
    return colors[status] || '#94a3b8';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'pending': '⏳',
      'processing': '⚙️',
      'extracted': '📋',
      'organized': '📁',
      'approved': '✅',
      'rejected': '❌',
      'uploaded': '📤'
    };
    return icons[status] || '📄';
  };

  const getStatusLabel = (status) => {
    const labels = {
      'pending': 'Pending',
      'processing': 'Processing',
      'extracted': 'Extracted',
      'organized': 'Organized',
      'approved': 'Approved',
      'rejected': 'Rejected',
      'uploaded': 'Uploaded'
    };
    return labels[status] || status;
  };

  const filteredDocuments = filter === 'all' 
    ? documents 
    : documents.filter(d => d.status === filter);

  const getProgressPercentage = (status) => {
    const steps = {
      'uploaded': 10,
      'pending': 20,
      'processing': 40,
      'extracted': 60,
      'organized': 75,
      'approved': 100,
      'rejected': 100
    };
    return steps[status] || 0;
  };

  if (loading) {
    return <div className="loading-state">Loading documents...</div>;
  }

  return (
    <div className="document-status-container">
      <div className="document-status-header">
        <h2>📄 Document Status</h2>
        <div className="realtime-status">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
          {isConnected ? 'Live updates' : 'Offline'}
        </div>
      </div>

      {/* Status Cards */}
      <div className="status-cards">
        <div className="status-card total">
          <span className="status-icon">📊</span>
          <div className="status-info">
            <span className="status-count">{documents.length}</span>
            <span className="status-label">Total Documents</span>
          </div>
        </div>
        {Object.entries(statusCounts || {}).map(([status, count]) => (
          <div key={status} className="status-card" style={{ borderColor: getStatusColor(status) }}>
            <span className="status-icon">{getStatusIcon(status)}</span>
            <div className="status-info">
              <span className="status-count">{count}</span>
              <span className="status-label">{getStatusLabel(status)}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs">
        <button 
          className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All ({documents.length})
        </button>
        {Object.entries(statusCounts || {}).map(([status, count]) => (
          <button 
            key={status}
            className={`filter-tab ${filter === status ? 'active' : ''}`}
            onClick={() => setFilter(status)}
          >
            {getStatusLabel(status)} ({count})
          </button>
        ))}
      </div>

      {/* Document List */}
      <div className="document-list">
        {filteredDocuments.length === 0 ? (
          <div className="empty-state">No documents found</div>
        ) : (
          filteredDocuments.map(doc => (
            <div key={doc.id} className="document-item">
              <div className="document-info">
                <div className="document-name">{doc.file_name}</div>
                <div className="document-meta">
                  <span className="document-type">{doc.file_type}</span>
                  <span className="document-date">
                    {new Date(doc.upload_date).toLocaleDateString()}
                  </span>
                  {doc.asset_name && (
                    <span className="document-asset">🏭 {doc.asset_name}</span>
                  )}
                </div>
              </div>
              <div className="document-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ 
                      width: `${getProgressPercentage(doc.status)}%`,
                      backgroundColor: getStatusColor(doc.status)
                    }}
                  />
                </div>
                <span 
                  className="document-status-badge"
                  style={{ backgroundColor: getStatusColor(doc.status) }}
                >
                  {getStatusIcon(doc.status)} {getStatusLabel(doc.status)}
                </span>
              </div>
              <div className="document-actions">
                <button 
                  className="action-btn"
                  onClick={() => {/* View document */}}
                >
                  👁️
                </button>
                {doc.status === 'extracted' && (
                  <button 
                    className="action-btn verify-btn"
                    onClick={() => {/* Verify document */}}
                  >
                    ✅
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Live Updates Feed */}
      {isConnected && documents.length > 0 && (
        <div className="live-updates">
          <div className="live-updates-header">
            <span className="live-dot" />
            Live Updates
          </div>
          <div className="update-item">
            <span className="update-time">Just now</span>
            <span className="update-text">Document status updated</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default DocumentStatus;