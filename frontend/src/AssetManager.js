import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import './css/AssetManager.css';
import toast from 'react-hot-toast';

function AssetManager({ organization }) {
  const [activeTab, setActiveTab] = useState('facilities');
  const [facilities, setFacilities] = useState([]);
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Form states
  const [newFacilityName, setNewFacilityName] = useState('');
  const [newFacilityPostcode, setNewFacilityPostcode] = useState('');
  const [newAssetName, setNewAssetName] = useState('');
  const [newAssetDesc, setNewAssetDesc] = useState('');
  const [selectedFacilityId, setSelectedFacilityId] = useState('');

  const fetchData = async () => {
  setLoading(true);
  const { data: facData } = await supabase.from('facilities').select('*').eq('organization_id', organization.id).order('created_at', { ascending: false });
  const { data: assetData } = await supabase.from('assets').select('*, facilities(name)').eq('facilities.organization_id', organization.id).order('created_at', { ascending: false });
    
    if (facData) setFacilities(facData);
    if (assetData) setAssets(assetData);
    setLoading(false);
  };

  useEffect(() => {
    if (organization) fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [organization]);
  
  const handleAddFacility = async (e) => {
    e.preventDefault();
    const { error } = await supabase.from('facilities').insert({
      organization_id: organization.id,
      name: newFacilityName,
      postcode: newFacilityPostcode
    });
    if (!error) {
      setNewFacilityName(''); setNewFacilityPostcode('');
      fetchData();
    }
  };

  const handleAddAsset = async (e) => {
    e.preventDefault();
    if (!selectedFacilityId) return toast.error('Please select a facility first.');
    
    const { error } = await supabase.from('assets').insert({
      facility_id: selectedFacilityId,
      name: newAssetName,
      description: newAssetDesc
    });
    if (!error) {
      setNewAssetName(''); setNewAssetDesc(''); setSelectedFacilityId('');
      fetchData();
    }
  };

  if (loading) {
    return (
      <div className="view-section">
        {/* Skeleton for the Section Title */}
        <div className="skeleton skeleton-text title" style={{ width: '30%', marginBottom: '1.5rem' }}></div>
        
        {/* Skeleton for the List Items / Cards */}
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
      </div>
    );
  }

  return (
    <div className="asset-manager-container">
      <h2>🏢 Facilities & Assets Manager</h2>
      <p className="subtitle">Register your physical locations and vehicles to enable advanced tracking and auto-mapping.</p>

      <div className="asset-tabs">
        <button className={`tab-btn ${activeTab === 'facilities' ? 'active' : ''}`} onClick={() => setActiveTab('facilities')}>Facilities</button>
        <button className={`tab-btn ${activeTab === 'assets' ? 'active' : ''}`} onClick={() => setActiveTab('assets')}>Assets (Vehicles/Meters)</button>
      </div>

      {activeTab === 'facilities' && (
        <div className="tab-content">
          <form onSubmit={handleAddFacility} className="add-form">
            <input type="text" placeholder="Facility Name (e.g., Birmingham Hub)" value={newFacilityName} onChange={(e) => setNewFacilityName(e.target.value)} required />
            <input type="text" placeholder="Postcode (e.g., B1 1AA)" value={newFacilityPostcode} onChange={(e) => setNewFacilityPostcode(e.target.value)} required />
            <button type="submit" className="add-btn">+ Add Facility</button>
          </form>
          
          <div className="list-grid">
            {facilities.map(fac => (
              <div key={fac.id} className="list-card">
                <h4>{fac.name}</h4>
                <p>📍 {fac.postcode}</p>
              </div>
            ))}
            {facilities.length === 0 && <p className="empty-msg">No facilities registered yet.</p>}
          </div>
        </div>
      )}

      {activeTab === 'assets' && (
        <div className="tab-content">
          <form onSubmit={handleAddAsset} className="add-form">
            <select value={selectedFacilityId} onChange={(e) => setSelectedFacilityId(e.target.value)} required>
              <option value="">Select a Facility...</option>
              {facilities.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
            </select>
            <input type="text" placeholder="Asset Name (e.g., Van BV67 AAA)" value={newAssetName} onChange={(e) => setNewAssetName(e.target.value)} required />
            <input type="text" placeholder="Description (Optional)" value={newAssetDesc} onChange={(e) => setNewAssetDesc(e.target.value)} />
            <button type="submit" className="add-btn">+ Add Asset</button>
          </form>

          <div className="list-grid">
            {assets.map(asset => (
              <div key={asset.id} className="list-card">
                <h4>{asset.name}</h4>
                <p>🏢 {asset.facilities?.name || 'Unknown Facility'}</p>
                {asset.description && <p className="desc">{asset.description}</p>}
              </div>
            ))}
            {assets.length === 0 && <p className="empty-msg">No assets registered yet.</p>}
          </div>
        </div>
      )}
    </div>
  );
}

export default AssetManager;