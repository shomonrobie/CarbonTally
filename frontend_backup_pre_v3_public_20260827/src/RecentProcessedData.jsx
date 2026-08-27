import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient'; // Adjust path to your actual supabase client
import toast from 'react-hot-toast';

export default function RecentProcessedData({ organizationId }) {
  const [processedItems, setProcessedItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (organizationId) {
      fetchProcessedData();
    }
  }, [organizationId]);

  const fetchProcessedData = async () => {
    setLoading(true);
    // Fetch recently completed manual extractions for this organization
    const { data, error } = await supabase
      .from('manual_review_queue')
      .select('*')
      .eq('organization_id', organizationId)
      .eq('status', 'completed')
      .order('completed_at', { ascending: false })
      .limit(10); // Show last 10 processed items

    if (error) {
      console.error('Error fetching processed data:', error);
    } else {
      setProcessedItems(data || []);
    }
    setLoading(false);
  };

  if (loading) {
    return <p style={{ textAlign: 'center', color: '#64748b', padding: '2rem' }}>Loading recent activity...</p>;
  }

  if (processedItems.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px dashed #cbd5e1' }}>
        <p style={{ color: '#64748b', fontSize: '1rem' }}>📭 No recently processed documents yet.</p>
        <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Upload a file or batch, and processed results will appear here.</p>
      </div>
    );
  }

  return (
    <div style={{ marginTop: '3rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0, fontSize: '1.25rem', color: '#0f172a' }}>✅ Recently Processed Documents</h3>
        <button 
          onClick={fetchProcessedData} 
          style={{ background: 'none', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '0.4rem 0.8rem', cursor: 'pointer', color: '#475569', fontSize: '0.875rem' }}
        >
          🔄 Refresh
        </button>
      </div>

      <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
          <thead style={{ backgroundColor: '#f8fafc' }}>
            <tr>
              <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#475569', borderBottom: '1px solid #e2e8f0' }}>Date</th>
              <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#475569', borderBottom: '1px solid #e2e8f0' }}>Asset / Facility</th>
              <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#475569', borderBottom: '1px solid #e2e8f0' }}>Energy Source / Category</th>
              <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#475569', borderBottom: '1px solid #e2e8f0' }}>Consumption</th>
              <th style={{ padding: '1rem', textAlign: 'right', fontWeight: '600', color: '#475569', borderBottom: '1px solid #e2e8f0' }}>Status</th>
            </tr>
          </thead>
          <tbody style={{ backgroundColor: '#ffffff' }}>
            {processedItems.map((item) => {
              const extraction = item.manual_extraction_result || {};
              return (
                <tr key={item.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '1rem', color: '#334155' }}>
                    {extraction.billing_start || 'N/A'}
                  </td>
                  <td style={{ padding: '1rem', color: '#334155', fontWeight: '500' }}>
                    {extraction.asset_name || 'Unassigned'}
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <span style={{ 
                      padding: '0.25rem 0.75rem', 
                      borderRadius: '999px', 
                      fontSize: '0.75rem', 
                      fontWeight: '600',
                      backgroundColor: '#dbeafe',
                      color: '#1e40af'
                    }}>
                      {extraction.fuel_utility_type || 'Unknown'}
                    </span>
                  </td>
                  <td style={{ padding: '1rem', color: '#334155', fontFamily: 'monospace' }}>
                    {extraction.consumption ? `${extraction.consumption}` : '0'} 
                    <span style={{ color: '#94a3b8', fontSize: '0.8rem', marginLeft: '4px' }}>
                      {item.data_type === 'utility' ? 'kWh' : item.data_type === 'fuel' ? 'L' : 'units'}
                    </span>
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    <span style={{ 
                      padding: '0.25rem 0.75rem', 
                      borderRadius: '999px', 
                      fontSize: '0.75rem', 
                      fontWeight: '600',
                      backgroundColor: '#dcfce7',
                      color: '#166534'
                    }}>
                      ✅ Processed
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      
      <p style={{ marginTop: '1rem', fontSize: '0.875rem', color: '#64748b' }}>
        💡 <strong>Next Step:</strong> These records have been manually verified by our team. 
        They will be added to your official SECR emissions logs once you approve them in the Review Queue.
      </p>
    </div>
  );
}