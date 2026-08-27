// AssetManager.jsx - Fixed API Endpoints

import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import './css/AssetManager.css';
import toast from 'react-hot-toast';

function AssetManager({ organization }) {
  const [activeTab, setActiveTab] = useState('facilities');
  const [facilities, setFacilities] = useState([]);
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedFacility, setSelectedFacility] = useState(null);
  
  // Form states for Facilities
  const [newFacility, setNewFacility] = useState({
    name: '',
    address_line1: '',
    address_line2: '',
    city: '',
    county: '',
    postcode: '',
    country: 'United Kingdom',
    type: 'office'
  });
  
  // Form states for Assets
  const [newAsset, setNewAsset] = useState({
    name: '',
    description: '',
    type: '',
    facility_id: ''
  });

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  const fetchData = async () => {
    if (!organization?.id) {
      console.log('⏳ Waiting for organization ID...');
      return;
    }

    setLoading(true);
    const token = await getToken();
    
    try {
      // ✅ FIX: Include organization ID in the path
      // GET /api/organizations/{org_id}/facilities
      const facResponse = await fetch(`${API_URL}/api/organizations/${organization.id}/facilities?limit=1000`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (facResponse.ok) {
        const data = await facResponse.json();
        setFacilities(data.facilities || []);
        console.log('✅ Facilities loaded:', data.facilities?.length || 0);
      } else {
        console.error('❌ Failed to fetch facilities:', facResponse.status);
      }

      // ✅ FIX: Include organization ID in the path
      // GET /api/organizations/{org_id}/assets
      const assetResponse = await fetch(`${API_URL}/api/organizations/${organization.id}/assets?limit=1000`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (assetResponse.ok) {
        const data = await assetResponse.json();
        setAssets(data.assets || []);
        console.log('✅ Assets loaded:', data.assets?.length || 0);
      } else {
        console.error('❌ Failed to fetch assets:', assetResponse.status);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (organization?.id) {
      fetchData();
    }
  }, [organization?.id]);

  const handleFacilityInputChange = (field, value) => {
    setNewFacility(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAddFacility = async (e) => {
    e.preventDefault();
    
    if (!newFacility.name.trim()) {
      toast.error('Facility name is required');
      return;
    }

    if (!newFacility.postcode.trim()) {
      toast.error('Postcode is required');
      return;
    }

    setIsSubmitting(true);
    const token = await getToken();

    try {
      // ✅ FIX: POST /api/organizations/{org_id}/facilities
      const response = await fetch(`${API_URL}/api/organizations/${organization.id}/facilities`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newFacility.name,
          address_line1: newFacility.address_line1 || null,
          address_line2: newFacility.address_line2 || null,
          city: newFacility.city || null,
          county: newFacility.county || null,
          postcode: newFacility.postcode,
          country: newFacility.country || 'United Kingdom',
          type: newFacility.type || 'office'
        })
      });

      if (response.ok) {
        toast.success(`✅ Facility "${newFacility.name}" added successfully!`);
        setNewFacility({
          name: '',
          address_line1: '',
          address_line2: '',
          city: '',
          county: '',
          postcode: '',
          country: 'United Kingdom',
          type: 'office'
        });
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to add facility');
      }
    } catch (error) {
      console.error('Error adding facility:', error);
      toast.error('Failed to add facility');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddAsset = async (e) => {
    e.preventDefault();
    
    if (!newAsset.facility_id) {
      toast.error('Please select a facility first.');
      return;
    }

    if (!newAsset.name.trim()) {
      toast.error('Asset name is required');
      return;
    }

    setIsSubmitting(true);
    const token = await getToken();

    try {
      // ✅ FIX: POST /api/organizations/{org_id}/assets
      const response = await fetch(`${API_URL}/api/organizations/${organization.id}/assets`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          facility_id: newAsset.facility_id,
          name: newAsset.name,
          description: newAsset.description || null,
          type: newAsset.type || 'other'
        })
      });

      if (response.ok) {
        toast.success(`✅ Asset "${newAsset.name}" added successfully!`);
        setNewAsset({
          name: '',
          description: '',
          type: '',
          facility_id: ''
        });
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to add asset');
      }
    } catch (error) {
      console.error('Error adding asset:', error);
      toast.error('Failed to add asset');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteFacility = async (facilityId, facilityName) => {
    if (!window.confirm(`Are you sure you want to deactivate "${facilityName}"?`)) return;

    const token = await getToken();

    try {
      // ✅ FIX: DELETE /api/organizations/{org_id}/facilities/{facility_id}
      const response = await fetch(`${API_URL}/api/organizations/${organization.id}/facilities/${facilityId}?permanent=false`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success(`Facility "${facilityName}" deactivated`);
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete facility');
      }
    } catch (error) {
      console.error('Error deleting facility:', error);
      toast.error('Failed to delete facility');
    }
  };

  const handleDeleteAsset = async (assetId, assetName) => {
    if (!window.confirm(`Are you sure you want to deactivate "${assetName}"?`)) return;

    const token = await getToken();

    try {
      // ✅ FIX: DELETE /api/organizations/{org_id}/assets/{asset_id}
      const response = await fetch(`${API_URL}/api/organizations/${organization.id}/assets/${assetId}?permanent=false`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success(`Asset "${assetName}" deactivated`);
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete asset');
      }
    } catch (error) {
      console.error('Error deleting asset:', error);
      toast.error('Failed to delete asset');
    }
  };

  const formatFacilityAddress = (facility) => {
    const parts = [];
    if (facility.address_line1) parts.push(facility.address_line1);
    if (facility.address_line2) parts.push(facility.address_line2);
    if (facility.city) parts.push(facility.city);
    if (facility.county) parts.push(facility.county);
    if (facility.postcode) parts.push(facility.postcode);
    if (facility.country) parts.push(facility.country);
    return parts.length > 0 ? parts.join(', ') : facility.postcode || null;
  };

  const getAssetsForFacility = (facilityId) => {
    return assets.filter(a => a.facility_id === facilityId);
  };

  if (loading) {
    return (
      <div className="view-section">
        <div className="skeleton skeleton-text title" style={{ width: '30%', marginBottom: '1.5rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
      </div>
    );
  }

  if (!organization?.id) {
    return (
      <div className="view-section">
        <div className="empty-state">
          <p className="empty-msg">No organization selected.</p>
          <p className="empty-hint">Please select an organization to manage assets.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="asset-manager-container">
      <div className="asset-header">
        <div>
          <h2>🏢 Facilities & Assets Manager</h2>
          <p className="subtitle">Register your physical locations and vehicles to enable advanced tracking and auto-mapping.</p>
        </div>
        <div className="header-stats">
          <div className="stat-badge">
            <span className="stat-number">{facilities.length}</span>
            <span className="stat-label">Facilities</span>
          </div>
          <div className="stat-badge">
            <span className="stat-number">{assets.length}</span>
            <span className="stat-label">Assets</span>
          </div>
        </div>
      </div>

      <div className="asset-tabs">
        <button 
          className={`tab-btn ${activeTab === 'facilities' ? 'active' : ''}`} 
          onClick={() => setActiveTab('facilities')}
        >
          🏢 Facilities
        </button>
        <button 
          className={`tab-btn ${activeTab === 'assets' ? 'active' : ''}`} 
          onClick={() => setActiveTab('assets')}
        >
          🔧 Assets
        </button>
      </div>

      {/* FACILITIES TAB */}
      {activeTab === 'facilities' && (
        <div className="tab-content">
          {/* Add Facility Form */}
          <div className="add-section">
            <h3>➕ Add New Facility</h3>
            <form onSubmit={handleAddFacility} className="add-form facility-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Facility Name *</label>
                  <input 
                    type="text" 
                    placeholder="e.g., London Office" 
                    value={newFacility.name} 
                    onChange={(e) => handleFacilityInputChange('name', e.target.value)} 
                    required 
                  />
                </div>
                <div className="form-group">
                  <label>Postcode *</label>
                  <input 
                    type="text" 
                    placeholder="e.g., EC1A 1BB" 
                    value={newFacility.postcode} 
                    onChange={(e) => handleFacilityInputChange('postcode', e.target.value)} 
                    required 
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Address Line 1</label>
                  <input 
                    type="text" 
                    placeholder="Street address" 
                    value={newFacility.address_line1} 
                    onChange={(e) => handleFacilityInputChange('address_line1', e.target.value)} 
                  />
                </div>
                <div className="form-group">
                  <label>Address Line 2</label>
                  <input 
                    type="text" 
                    placeholder="Apartment, suite, etc." 
                    value={newFacility.address_line2} 
                    onChange={(e) => handleFacilityInputChange('address_line2', e.target.value)} 
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>City/Town</label>
                  <input 
                    type="text" 
                    placeholder="e.g., London" 
                    value={newFacility.city} 
                    onChange={(e) => handleFacilityInputChange('city', e.target.value)} 
                  />
                </div>
                <div className="form-group">
                  <label>County/State</label>
                  <input 
                    type="text" 
                    placeholder="e.g., Greater London" 
                    value={newFacility.county} 
                    onChange={(e) => handleFacilityInputChange('county', e.target.value)} 
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Country</label>
                  <select 
                    value={newFacility.country} 
                    onChange={(e) => handleFacilityInputChange('country', e.target.value)}
                  >
                    <option value="United Kingdom">🇬🇧 United Kingdom</option>
                    <option value="Ireland">🇮🇪 Ireland</option>
                    <option value="France">🇫🇷 France</option>
                    <option value="Germany">🇩🇪 Germany</option>
                    <option value="Spain">🇪🇸 Spain</option>
                    <option value="Italy">🇮🇹 Italy</option>
                    <option value="Netherlands">🇳🇱 Netherlands</option>
                    <option value="Belgium">🇧🇪 Belgium</option>
                    <option value="Portugal">🇵🇹 Portugal</option>
                    <option value="Sweden">🇸🇪 Sweden</option>
                    <option value="Denmark">🇩🇰 Denmark</option>
                    <option value="Norway">🇳🇴 Norway</option>
                    <option value="Finland">🇫🇮 Finland</option>
                    <option value="Other">🌍 Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Facility Type</label>
                  <select 
                    value={newFacility.type} 
                    onChange={(e) => handleFacilityInputChange('type', e.target.value)}
                  >
                    <option value="office">🏢 Office</option>
                    <option value="warehouse">📦 Warehouse</option>
                    <option value="retail">🛍️ Retail</option>
                    <option value="manufacturing">🏭 Manufacturing</option>
                    <option value="data_centre">💻 Data Centre</option>
                    <option value="laboratory">🔬 Laboratory</option>
                    <option value="hospital">🏥 Hospital</option>
                    <option value="school">🏫 School</option>
                    <option value="hotel">🏨 Hotel</option>
                    <option value="restaurant">🍽️ Restaurant</option>
                    <option value="other">🏠 Other</option>
                  </select>
                </div>
              </div>
              <button type="submit" className="add-btn" disabled={isSubmitting}>
                {isSubmitting ? '⏳ Adding...' : '+ Add Facility'}
              </button>
            </form>
          </div>

          {/* Facilities Grid */}
          <div className="facilities-grid">
            {facilities.map(fac => {
              const facilityAssets = getAssetsForFacility(fac.id);
              return (
                <div key={fac.id} className="facility-card">
                  <div className="facility-card-header">
                    <div className="facility-name-section">
                      <h4>{fac.name}</h4>
                      <span className={`status-badge ${fac.is_active !== false ? 'active' : 'inactive'}`}>
                        {fac.is_active !== false ? '● Active' : '● Inactive'}
                      </span>
                    </div>
                    <button 
                      className="delete-btn" 
                      onClick={() => handleDeleteFacility(fac.id, fac.name)}
                      title="Delete facility"
                    >
                      ✕
                    </button>
                  </div>
                  
                  <div className="facility-card-body">
                    <div className="facility-address">
                      <p className="address-line">
                        {fac.address_line1 && <span>{fac.address_line1}</span>}
                        {fac.address_line2 && <span>, {fac.address_line2}</span>}
                      </p>
                      <p className="address-line">
                        {fac.city && <span>{fac.city}</span>}
                        {fac.county && <span>, {fac.county}</span>}
                      </p>
                      <p className="address-line">
                        <strong>{fac.postcode}</strong>
                        {fac.country && <span>, {fac.country}</span>}
                      </p>
                      {fac.type && (
                        <span className="type-badge">{fac.type}</span>
                      )}
                    </div>
                    
                    <div className="facility-stats">
                      <div className="stat-item">
                        <span className="stat-value">{facilityAssets.length}</span>
                        <span className="stat-label">Assets</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-value">{fac.emissions_count || 0}</span>
                        <span className="stat-label">Records</span>
                      </div>
                    </div>
                  </div>

                  {/* Asset List - Quick View */}
                  {facilityAssets.length > 0 && (
                    <div className="facility-assets-preview">
                      <p className="assets-title">Assets ({facilityAssets.length})</p>
                      <div className="asset-tags">
                        {facilityAssets.slice(0, 5).map(a => (
                          <span key={a.id} className="asset-tag">{a.name}</span>
                        ))}
                        {facilityAssets.length > 5 && (
                          <span className="asset-tag more">+{facilityAssets.length - 5} more</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
            {facilities.length === 0 && (
              <div className="empty-state">
                <p className="empty-msg">No facilities registered yet.</p>
                <p className="empty-hint">Use the form above to add your first facility.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ASSETS TAB */}
      {activeTab === 'assets' && (
        <div className="tab-content">
          <div className="add-section">
            <h3>➕ Add New Asset</h3>
            <form onSubmit={handleAddAsset} className="add-form asset-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Facility *</label>
                  <select 
                    value={newAsset.facility_id} 
                    onChange={(e) => setNewAsset(prev => ({ ...prev, facility_id: e.target.value }))} 
                    required
                  >
                    <option value="">Select a Facility...</option>
                    {facilities.filter(f => f.is_active !== false).map(f => (
                      <option key={f.id} value={f.id}>
                        {f.name} {f.city ? `(${f.city})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Asset Name *</label>
                  <input 
                    type="text" 
                    placeholder="e.g., Delivery Van BV67 AAA" 
                    value={newAsset.name} 
                    onChange={(e) => setNewAsset(prev => ({ ...prev, name: e.target.value }))} 
                    required 
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Description</label>
                  <input 
                    type="text" 
                    placeholder="Brief description (optional)" 
                    value={newAsset.description} 
                    onChange={(e) => setNewAsset(prev => ({ ...prev, description: e.target.value }))} 
                  />
                </div>
                <div className="form-group">
                  <label>Asset Type</label>
                  <select 
                    value={newAsset.type} 
                    onChange={(e) => setNewAsset(prev => ({ ...prev, type: e.target.value }))}
                  >
                    <option value="">Select Type...</option>
                    <option value="vehicle">🚗 Vehicle</option>
                    <option value="boiler">🔥 Boiler</option>
                    <option value="generator">⚡ Generator</option>
                    <option value="meter">📊 Meter</option>
                    <option value="chiller">❄️ Chiller</option>
                    <option value="hvac">🌡️ HVAC</option>
                    <option value="lighting">💡 Lighting</option>
                    <option value="server">🖥️ Server</option>
                    <option value="other">🏷️ Other</option>
                  </select>
                </div>
              </div>
              <button 
                type="submit" 
                className="add-btn" 
                disabled={isSubmitting || facilities.length === 0}
              >
                {isSubmitting ? '⏳ Adding...' : '+ Add Asset'}
              </button>
            </form>
          </div>

          {/* Assets Grid */}
          <div className="assets-grid">
            {assets.map(asset => {
              const facility = facilities.find(f => f.id === asset.facility_id);
              return (
                <div key={asset.id} className="asset-card">
                  <div className="asset-card-header">
                    <div className="asset-name-section">
                      <h4>{asset.name}</h4>
                      <span className={`status-badge ${asset.is_active !== false ? 'active' : 'inactive'}`}>
                        {asset.is_active !== false ? '● Active' : '● Inactive'}
                      </span>
                    </div>
                    <button 
                      className="delete-btn" 
                      onClick={() => handleDeleteAsset(asset.id, asset.name)}
                      title="Delete asset"
                    >
                      ✕
                    </button>
                  </div>
                  <div className="asset-card-body">
                    <div className="asset-facility">
                      <span className="facility-icon">🏢</span>
                      <span>{facility?.name || 'Unknown Facility'}</span>
                    </div>
                    {asset.type && (
                      <span className="type-badge">{asset.type}</span>
                    )}
                    {asset.description && (
                      <p className="asset-description">{asset.description}</p>
                    )}
                    <div className="asset-stats">
                      <div className="stat-item">
                        <span className="stat-value">{asset.emissions_count || 0}</span>
                        <span className="stat-label">Records</span>
                      </div>
                      {asset.serial_number && (
                        <div className="stat-item">
                          <span className="stat-label">SN: {asset.serial_number}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            {assets.length === 0 && (
              <div className="empty-state">
                <p className="empty-msg">No assets registered yet.</p>
                <p className="empty-hint">Add assets to your facilities for better tracking.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default AssetManager;