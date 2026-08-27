// frontend/src/components/DashboardSummary.jsx
import React, { useState, useEffect } from 'react';
import { useRealtime, useDocumentStatus } from '../context/RealtimeContext';

function DashboardSummary({ organization }) {
  const { isConnected, onlineStaff } = useRealtime();
  const { statusCounts } = useDocumentStatus();
  const [stats, setStats] = useState({
    totalEmissions: 0,
    totalTransactions: 0,
    totalDocuments: 0,
    pendingReviews: 0
  });

  useEffect(() => {
    fetchStats();
  }, [organization]);

  // Update stats when document status changes
  useEffect(() => {
    if (statusCounts) {
      setStats(prev => ({
        ...prev,
        totalDocuments: Object.values(statusCounts).reduce((a, b) => a + b, 0),
        pendingReviews: statusCounts.pending || 0
      }));
    }
  }, [statusCounts]);

  const fetchStats = async () => {
    if (!organization) return;
    
    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/emissions/stats?organization_id=${organization.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to fetch stats');
      
      const data = await response.json();
      setStats(prev => ({
        ...prev,
        totalEmissions: data.total_emissions || 0,
        totalTransactions: data.total_transactions || 0
      }));
      
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  return (
    <div className="dashboard-summary">
      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon">🌍</div>
          <div className="card-value">{stats.totalEmissions.toLocaleString()}</div>
          <div className="card-label">Total Emissions (kgCO2e)</div>
          <div className="card-sub">{(stats.totalEmissions / 1000).toFixed(2)} tonnes</div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📊</div>
          <div className="card-value">{stats.totalTransactions}</div>
          <div className="card-label">Total Transactions</div>
          <div className="card-sub">Across all batches</div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📄</div>
          <div className="card-value">{stats.totalDocuments}</div>
          <div className="card-label">Total Documents</div>
          <div className="card-sub">
            <span className="status-badge pending">{statusCounts?.pending || 0} pending</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">👥</div>
          <div className="card-value">{onlineStaff.length}</div>
          <div className="card-label">Team Online</div>
          <div className="card-sub">
            <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
            {isConnected ? 'Live' : 'Offline'}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardSummary;