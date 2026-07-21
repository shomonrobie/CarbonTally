import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import toast from 'react-hot-toast';

export default function StaffDashboard({ onBack }) {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);

  // Fetch pending queue items
  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from('manual_review_queue')
      .select('*')
      .eq('status', 'pending')
      .order('priority', { ascending: false })
      .order('created_at', { ascending: true });

    if (error) {
      console.error("Error fetching queue:", error);
      toast.error("Failed to load queue");
    } else {
      setQueue(data || []);
    }
    setLoading(false);
  };

  const handleClaim = (item) => {
    setSelectedItem(item);
  };

  const handleBackToList = () => {
    setSelectedItem(null);
    fetchQueue(); // Refresh the list
  };

  if (selectedItem) {
    // We will build this Manual Extraction Form in the next step!
    return (
      <ManualExtractionForm 
        item={selectedItem} 
        onBack={handleBackToList} 
        onComplete={() => {
          toast.success("Data extracted and saved!");
          handleBackToList();
        }}
      />
    );
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <button onClick={onBack} style={{ marginBottom: '0.5rem', background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '0.9rem' }}>
            ← Back to App
          </button>
          <h1 style={{ margin: 0, fontSize: '1.8rem', color: '#0f172a' }}>📋 Manual Review Queue</h1>
          <p style={{ color: '#64748b', margin: '0.5rem 0 0 0' }}>{queue.length} document(s) pending manual extraction</p>
        </div>
        <button onClick={fetchQueue} style={{ padding: '0.5rem 1rem', background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', cursor: 'pointer' }}>
          🔄 Refresh
        </button>
      </div>

      {loading ? (
        <p>Loading queue...</p>
      ) : queue.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem', background: '#f8fafc', borderRadius: '12px', color: '#64748b' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎉</div>
          <h3>All caught up!</h3>
          <p>No pending manual reviews at this time.</p>
        </div>
      ) : (
        <div style={{ background: 'white', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
              <tr>
                <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.875rem', color: '#64748b' }}>File Name</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.875rem', color: '#64748b' }}>Type</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.875rem', color: '#64748b' }}>Priority</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.875rem', color: '#64748b' }}>Submitted</th>
                <th style={{ padding: '1rem', textAlign: 'right', fontSize: '0.875rem', color: '#64748b' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((item) => (
                <tr key={item.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '1rem', fontWeight: '500' }}>{item.file_name}</td>
                  <td style={{ padding: '1rem' }}>
                    <span style={{ 
                      padding: '0.25rem 0.75rem', 
                      borderRadius: '999px', 
                      fontSize: '0.75rem', 
                      fontWeight: '600',
                      background: item.file_type === 'PDF' ? '#dbeafe' : '#fef3c7',
                      color: item.file_type === 'PDF' ? '#1e40af' : '#92400e'
                    }}>
                      {item.file_type}
                    </span>
                  </td>
                  <td style={{ padding: '1rem' }}>
                    {item.priority >= 1 ? '🔥 High' : '📄 Normal'}
                  </td>
                  <td style={{ padding: '1rem', color: '#64748b', fontSize: '0.875rem' }}>
                    {new Date(item.created_at).toLocaleDateString()} {new Date(item.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    <button 
                      onClick={() => handleClaim(item)}
                      style={{ 
                        padding: '0.5rem 1rem', 
                        background: '#16a34a', 
                        color: 'white', 
                        border: 'none', 
                        borderRadius: '6px', 
                        fontWeight: '600', 
                        cursor: 'pointer' 
                      }}
                    >
                      👁️ Review & Extract
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// Placeholder for the next step
function ManualExtractionForm({ item, onBack, onComplete }) {
  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h2>Manual Extraction Form (Coming Next!)</h2>
      <p>Review ID: {item.id}</p>
      <button onClick={onBack} style={{ padding: '0.5rem 1rem', marginTop: '1rem' }}>Back to List</button>
    </div>
  );
}