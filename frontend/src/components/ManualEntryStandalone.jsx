// frontend/src/components/ManualEntryStandalone.jsx
// Fixed assets loading and display

import React, { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';
import toast from 'react-hot-toast';
import {
  FaSpinner,
  FaCheckCircle,
  FaExclamationTriangle,
  FaCalendarAlt,
  FaBolt,
  FaBuilding,
  FaCar,
  FaArrowLeft
} from 'react-icons/fa';
import '../css/ManualEntryStandalone.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ManualEntryStandalone = ({ organization, onComplete, onCancel }) => {
  // Form state
  const [formData, setFormData] = useState({
    billing_start: '',
    reporting_year: new Date().getFullYear(),
    consumption: '',
    fuel_utility_type: '',
    facility_id: '',
    asset_name: '',
    notes: '',
    unit: 'kWh',
    scope: 'scope1'
  });

  // Data states
  const [facilities, setFacilities] = useState([]);
  const [assets, setAssets] = useState([]);
  const [selectedFacilityId, setSelectedFacilityId] = useState('');
  const [fuelTypes, setFuelTypes] = useState([]);
  const [units, setUnits] = useState([]);
  
  // Loading states
  const [loading, setLoading] = useState(true);
  const [loadingAssets, setLoadingAssets] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  // Fetch all data on mount
  useEffect(() => {
    if (organization?.id) {
      fetchAllData();
    }
  }, [organization?.id]);

  // Fetch assets when facility changes
  useEffect(() => {
    if (selectedFacilityId) {
      fetchAssetsForFacility(selectedFacilityId);
    } else {
      setAssets([]);
    }
  }, [selectedFacilityId]);

  const fetchAllData = async () => {
    console.log('📡 Fetching all data for manual entry...');
    setLoading(true);
    
    const token = await getToken();
    
    if (!token) {
      console.error('❌ No token available');
      setLoading(false);
      toast.error('Authentication required. Please login again.');
      return;
    }

    try {
      // ✅ FIX: Use organization.id instead of organizationId
      const orgId = organization.id;
      
      // Fetch fuel types, units, and facilities in parallel
      const [fuelResponse, unitResponse, facilitiesResponse] = await Promise.all([
        fetch(`${API_URL}/api/reference/fuel-types`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        
        fetch(`${API_URL}/api/reference/units`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        
        // ✅ FIX: Use orgId variable
        fetch(
          `${API_URL}/api/organizations/${orgId}/facilities?limit=1000`,
          {
            headers: { 'Authorization': `Bearer ${token}` }
          }
        )
      ]);

      // Process fuel types
      if (fuelResponse.ok) {
        const data = await fuelResponse.json();
        setFuelTypes(data.fuel_types || []);
        console.log('✅ Fuel types loaded:', data.fuel_types?.length || 0);
      }

      // Process units
      if (unitResponse.ok) {
        const data = await unitResponse.json();
        setUnits(data.units || []);
        console.log('✅ Units loaded:', data.units?.length || 0);
      }

      // Process facilities
      if (facilitiesResponse.ok) {
        const data = await facilitiesResponse.json();
        setFacilities(data.facilities || []);
        console.log('✅ Facilities loaded:', data.facilities?.length || 0);
      }

    } catch (error) {
      console.error('❌ Error fetching data:', error);
      toast.error('Failed to load data. Please refresh and try again.');
    } finally {
      setLoading(false);
    }
  };

  // ✅ FIX: Fetch assets for a specific facility with org ID
  const fetchAssetsForFacility = async (facilityId) => {
    if (!facilityId || !organization?.id) {
      setAssets([]);
      return;
    }

    console.log(`📡 Fetching assets for facility: ${facilityId}`);
    setLoadingAssets(true);

    try {
      const token = await getToken();
      
      // ✅ FIX: Include organization ID in the path
      const response = await fetch(
        `${API_URL}/api/organizations/${organization.id}/assets?facility_id=${facilityId}&limit=1000`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        console.log(`✅ Assets loaded for facility ${facilityId}:`, data.assets?.length || 0);
        setAssets(data.assets || []);
      } else {
        console.warn('⚠️ Assets response not OK:', response.status);
        setAssets([]);
      }
    } catch (error) {
      console.error('❌ Error fetching assets:', error);
      setAssets([]);
    } finally {
      setLoadingAssets(false);
    }
  };

  const handleChange = (field, value) => {
    const newData = { ...formData, [field]: value };
    setFormData(newData);
    calculateProgress(newData);
  };

  const handleFacilitySelect = (facilityId) => {
    console.log('🏢 Facility selected:', facilityId);
    setSelectedFacilityId(facilityId);
    handleChange('facility_id', facilityId);
    handleChange('asset_name', ''); // Reset asset when facility changes
    // Assets will be fetched via the useEffect
  };

  const calculateProgress = (data) => {
    const sections = ['billing_start', 'consumption', 'fuel_utility_type', 'asset_name'];
    let completed = 0;
    sections.forEach(section => {
      if (data[section] && data[section].toString().trim() !== '') {
        completed++;
      }
    });
    const progressValue = Math.round((completed / sections.length) * 100);
    setProgress(progressValue);
  };

  const handleSubmit = async () => {
    if (!formData.billing_start) {
      toast.error('Please enter billing period start date');
      return;
    }
    if (!formData.consumption || parseFloat(formData.consumption) <= 0) {
      toast.error('Please enter a valid consumption value');
      return;
    }
    if (!formData.fuel_utility_type) {
      toast.error('Please select fuel/utility type');
      return;
    }
    if (!formData.asset_name) {
      toast.error('Please enter asset name');
      return;
    }

    setSubmitting(true);

    try {
      const token = await getToken();
      const consumption = parseFloat(formData.consumption);
      
      let defraFactorId = null;
      let multiplier = 2.68;
      
      try {
        const defraResponse = await fetch(
          `${API_URL}/api/defra-factors/${formData.reporting_year}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        
        if (defraResponse.ok) {
          const defraData = await defraResponse.json();
          const factor = defraData.factors?.find(f => f.activity_type === formData.fuel_utility_type);
          if (factor) {
            defraFactorId = factor.id;
            multiplier = parseFloat(factor.co2e_multiplier) || 2.68;
          }
        }
      } catch (error) {
        console.warn('Could not fetch DEFRA factor, using default:', error);
      }

      // Get asset ID
      let assetId = null;
      if (formData.asset_name && selectedFacilityId) {
        try {
          // ✅ FIX: Include organization ID in the path
          const assetResponse = await fetch(
            `${API_URL}/api/organizations/${organization.id}/assets?facility_id=${selectedFacilityId}&limit=1000`,
            { headers: { 'Authorization': `Bearer ${token}` } }
          );
          
          if (assetResponse.ok) {
            const assetData = await assetResponse.json();
            const asset = assetData.assets?.find(a => a.name === formData.asset_name);
            if (asset) {
              assetId = asset.id;
              console.log('✅ Asset found:', assetId);
            }
          }
        } catch (error) {
          console.warn('Could not fetch asset:', error);
        }
      }

      const kgCo2e = consumption * multiplier;

      const scopeMap = {
        scope1: 'Scope 1',
        scope2: 'Scope 2',
        scope3: 'Scope 3'
      };

      const payload = {
        organization_id: organization.id,
        asset_id: assetId,
        defra_factor_id: defraFactorId,
        start_date: formData.billing_start,
        end_date: formData.billing_start,
        raw_quantity: consumption,
        calculated_kg_co2e: kgCo2e,
        metadata: {
          source: 'manual_entry_standalone',
          scope: scopeMap[formData.scope] || 'Scope 1',
          fuel_utility_type: formData.fuel_utility_type,
          facility_id: formData.facility_id,
          asset_name: formData.asset_name,
          notes: formData.notes,
          unit: formData.unit,
          reporting_year: formData.reporting_year,
          multiplier_used: multiplier,
          entry_date: new Date().toISOString()
        }
      };

      const response = await fetch(`${API_URL}/api/emissions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        toast.success('✅ Data saved successfully!');
        if (onComplete) onComplete();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to save data');
      }
    } catch (error) {
      console.error('Error submitting:', error);
      toast.error('Failed to submit data');
    } finally {
      setSubmitting(false);
    }
  };

  // Show loading state
  if (loading) {
    return (
      <div className="manual-entry-standalone">
        <div className="standalone-header">
          <div className="header-left">
            <button className="back-btn" onClick={onCancel}>
              <FaArrowLeft /> Cancel
            </button>
            <h2>✏️ Manual Data Entry</h2>
          </div>
          <div className="header-right">
            <div className="loading-spinner">
              <FaSpinner className="spinner" />
              <span>Loading data...</span>
            </div>
          </div>
        </div>
        <div className="standalone-body">
          <div className="standalone-form">
            <div className="loading-placeholder">
              <div className="skeleton skeleton-text" style={{ width: '100%', height: '40px', marginBottom: '1rem' }} />
              <div className="skeleton skeleton-text" style={{ width: '100%', height: '60px', marginBottom: '1rem' }} />
              <div className="skeleton skeleton-text" style={{ width: '100%', height: '60px', marginBottom: '1rem' }} />
              <div className="skeleton skeleton-text" style={{ width: '100%', height: '60px', marginBottom: '1rem' }} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="manual-entry-standalone">
      {/* Header */}
      <div className="standalone-header">
        <div className="header-left">
          <button className="back-btn" onClick={onCancel}>
            <FaArrowLeft /> Cancel
          </button>
          <h2>✏️ Manual Data Entry</h2>
        </div>
        <div className="header-right">
          <div className="progress-indicator">
            <span className="progress-label">{progress}% Complete</span>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          </div>
        </div>
      </div>

      <div className="standalone-body">
        <div className="standalone-form">
          <p className="form-hint">
            Enter your emissions data directly. No file upload required.
          </p>

          {/* Scope Selection */}
          <div className="form-section">
            <div className="section-header">
              <h4>📊 Scope Selection</h4>
            </div>

            <div className="scope-selector">
              <button
                className={`scope-btn ${formData.scope === 'scope1' ? 'active' : ''}`}
                onClick={() => handleChange('scope', 'scope1')}
              >
                🔥 Scope 1
                <span className="scope-desc">Direct Emissions</span>
              </button>
              <button
                className={`scope-btn ${formData.scope === 'scope2' ? 'active' : ''}`}
                onClick={() => handleChange('scope', 'scope2')}
              >
                ⚡ Scope 2
                <span className="scope-desc">Electricity</span>
              </button>
              <button
                className={`scope-btn ${formData.scope === 'scope3' ? 'active' : ''}`}
                onClick={() => handleChange('scope', 'scope3')}
              >
                🌱 Scope 3
                <span className="scope-desc">Other Indirect</span>
              </button>
            </div>
          </div>

          {/* General Info */}
          <div className="form-section">
            <div className="section-header">
              <h4>📋 General Info</h4>
              <span className={`section-status ${formData.billing_start ? 'completed' : 'pending'}`}>
                {formData.billing_start ? '✅' : '⏳'}
              </span>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label><FaCalendarAlt /> Billing Period Start *</label>
                <input
                  type="date"
                  value={formData.billing_start}
                  onChange={(e) => handleChange('billing_start', e.target.value)}
                  className={!formData.billing_start ? 'error' : ''}
                />
              </div>

              <div className="form-group">
                <label>Reporting Year</label>
                <select
                  value={formData.reporting_year}
                  onChange={(e) => handleChange('reporting_year', parseInt(e.target.value))}
                >
                  {[new Date().getFullYear(), new Date().getFullYear() - 1, new Date().getFullYear() - 2].map(y => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Consumption */}
          <div className="form-section">
            <div className="section-header">
              <h4>⚡ Consumption</h4>
              <span className={`section-status ${formData.consumption ? 'completed' : 'pending'}`}>
                {formData.consumption ? '✅' : '⏳'}
              </span>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Units *</label>
                <select
                  value={formData.unit}
                  onChange={(e) => handleChange('unit', e.target.value)}
                >
                  <option value="">Select unit...</option>
                  {units.map(unit => (
                    <option key={unit.id} value={unit.code}>
                      {unit.name} {unit.symbol ? `(${unit.symbol})` : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Consumption Value *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.consumption}
                  onChange={(e) => handleChange('consumption', e.target.value)}
                  placeholder="Enter consumption value"
                  className={(!formData.consumption || parseFloat(formData.consumption) <= 0) ? 'error' : ''}
                />
              </div>
            </div>
          </div>

          {/* Activity */}
          <div className="form-section">
            <div className="section-header">
              <h4>🏭 Activity</h4>
              <span className={`section-status ${formData.fuel_utility_type && formData.asset_name ? 'completed' : 'pending'}`}>
                {formData.fuel_utility_type && formData.asset_name ? '✅' : '⏳'}
              </span>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label><FaBolt /> Fuel/Utility Type *</label>
                <select
                  value={formData.fuel_utility_type}
                  onChange={(e) => handleChange('fuel_utility_type', e.target.value)}
                  className={!formData.fuel_utility_type ? 'error' : ''}
                >
                  <option value="">Select type...</option>
                  {fuelTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label} {type.reporting_year ? `(${type.reporting_year})` : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label><FaBuilding /> Facility</label>
                <select
                  value={selectedFacilityId}
                  onChange={(e) => handleFacilitySelect(e.target.value)}
                >
                  <option value="">Select facility...</option>
                  {facilities.map(f => (
                    <option key={f.id} value={f.id}>
                      {f.name} {f.city ? `(${f.city})` : ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* ✅ Asset field with proper loading and suggestions */}
            <div className="form-group">
              <label><FaCar /> Asset (Vehicle/Meter) *</label>
              <input
                type="text"
                value={formData.asset_name}
                onChange={(e) => handleChange('asset_name', e.target.value)}
                placeholder={selectedFacilityId ? "Type asset name or select from suggestions" : "Select a facility first"}
                className={!formData.asset_name ? 'error' : ''}
                disabled={!selectedFacilityId}
              />
              
              {/* ✅ Show asset suggestions when a facility is selected */}
              {selectedFacilityId && (
                <>
                  {loadingAssets ? (
                    <div className="asset-loading">
                      <FaSpinner className="spinner-small" />
                      <span>Loading assets...</span>
                    </div>
                  ) : assets.length > 0 ? (
                    <div className="asset-suggestions">
                      {assets.slice(0, 5).map(a => (
                        <button
                          key={a.id}
                          className="asset-suggestion"
                          onClick={() => handleChange('asset_name', a.name)}
                        >
                          {a.name} {a.type ? `(${a.type})` : ''}
                        </button>
                      ))}
                      {assets.length > 5 && (
                        <span className="asset-more">+{assets.length - 5} more</span>
                      )}
                    </div>
                  ) : (
                    <div className="asset-empty">
                      <span className="asset-empty-text">No assets found for this facility. You can still type an asset name.</span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Notes */}
          <div className="form-section">
            <div className="section-header">
              <h4>📝 Notes</h4>
            </div>

            <div className="form-group">
              <label>Additional Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => handleChange('notes', e.target.value)}
                placeholder="Add any notes or comments about this entry..."
                rows="3"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="form-actions">
            <button className="btn-cancel" onClick={onCancel}>
              Cancel
            </button>
            <button
              className="btn-submit"
              onClick={handleSubmit}
              disabled={submitting || progress < 100}
            >
              {submitting ? (
                <><FaSpinner className="spinner" /> Saving...</>
              ) : (
                <><FaCheckCircle /> Save Entry</>
              )}
            </button>
          </div>

          {progress < 100 && (
            <div className="form-hint">
              <FaExclamationTriangle />
              <span>
                {100 - progress}% of fields remaining. Please complete all required fields.
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ManualEntryStandalone;