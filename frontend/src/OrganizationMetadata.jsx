// OrganizationMetadata.jsx - Complete with Backend API

import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import './css/OrganizationMetadata.css';
import toast from 'react-hot-toast';

function OrganizationMetadata({ organization, userRole }) {
  const [metadata, setMetadata] = useState({
    total_employees: 0,
    full_time_employees: 0,
    part_time_employees: 0,
    contract_employees: 0,
    average_employees: 0,
    annual_revenue: 0,
    ebitda: 0,
    total_assets: 0,
    total_facilities: 0,
    total_floor_area_sqft: 0,
    occupied_floor_area_sqft: 0,
    renewable_energy_percentage: 0,
    carbon_offset_percentage: 0,
    energy_intensity: 0,
    reporting_standard: 'SECR',
    fiscal_year_start: '',
    fiscal_year_end: '',
    primary_contact_name: '',
    primary_contact_email: '',
    primary_contact_phone: '',
    sustainability_officer_name: '',
    sustainability_officer_email: '',
    industry_sector: '',
    naics_code: '',
    sic_code: '',
  });
  
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState(null);
  const isAdmin = userRole === 'admin';

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  const fetchMetadata = async () => {
    try {
      setFetching(true);
      setError(null);
      const token = await getToken();
      
      const response = await fetch(
        `${API_URL}/organizations/${organization.id}/metadata`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const result = await response.json();
        if (result.data) {
          setMetadata({
            ...metadata,
            ...result.data,
            fiscal_year_start: result.data.fiscal_year_start || '',
            fiscal_year_end: result.data.fiscal_year_end || '',
          });
        }
      } else if (response.status === 401) {
        toast.error('Session expired. Please refresh the page.');
      } else {
        console.error('Failed to fetch metadata:', response.status);
        setError('Failed to load organization data');
      }
    } catch (error) {
      console.error('Error fetching metadata:', error);
      setError('Failed to load organization data');
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    if (organization?.id) {
      fetchMetadata();
    }
  }, [organization?.id]);

  const handleInputChange = (field, value) => {
    setMetadata(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNumberChange = (field, value) => {
    const numValue = parseFloat(value) || 0;
    setMetadata(prev => ({
      ...prev,
      [field]: numValue
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const token = await getToken();
      
      const response = await fetch(
        `${API_URL}/organizations/${organization.id}/metadata`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(metadata),
        }
      );

      if (response.ok) {
        const result = await response.json();
        toast.success('✅ Organization data saved successfully!');
        if (result.data) {
          setMetadata({ ...metadata, ...result.data });
        }
      } else if (response.status === 401) {
        toast.error('Session expired. Please refresh the page.');
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || 'Failed to save organization data');
      }
    } catch (error) {
      console.error('Error saving metadata:', error);
      toast.error('Failed to save organization data');
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="view-section">
        <div className="skeleton skeleton-text title" style={{ width: '30%', marginBottom: '1.5rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
      </div>
    );
  }

  return (
    <div className="org-metadata-container">
      <h2>📊 Organization Data for Reports</h2>
      <p className="subtitle">
        Enter your organization's operational data. This information is used to generate professional compliance reports with accurate metrics and intensity calculations.
      </p>

      {!isAdmin && (
        <div className="info-banner">
          ⚠️ Only organization admins can edit this data. You have view-only access.
        </div>
      )}

      {error && (
        <div className="error-banner">
          ❌ {error}
          <button onClick={fetchMetadata} className="retry-btn">Retry</button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="metadata-form">
        {/* ========== EMPLOYEE DATA ========== */}
        <div className="form-section">
          <h3>👥 Workforce Data</h3>
          <p className="section-hint">Used for emissions intensity calculations (tonnes CO2e per employee)</p>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="total_employees">Total Employees *</label>
              <input
                id="total_employees"
                type="number"
                min="0"
                step="1"
                value={metadata.total_employees || ''}
                onChange={(e) => handleNumberChange('total_employees', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 150"
                required
              />
              <small>Full workforce count including all employees</small>
            </div>
            
            <div className="form-group">
              <label htmlFor="full_time_employees">Full-Time Employees</label>
              <input
                id="full_time_employees"
                type="number"
                min="0"
                step="1"
                value={metadata.full_time_employees || ''}
                onChange={(e) => handleNumberChange('full_time_employees', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 120"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="part_time_employees">Part-Time Employees</label>
              <input
                id="part_time_employees"
                type="number"
                min="0"
                step="1"
                value={metadata.part_time_employees || ''}
                onChange={(e) => handleNumberChange('part_time_employees', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 30"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="average_employees">Average Headcount (Year)</label>
              <input
                id="average_employees"
                type="number"
                min="0"
                step="1"
                value={metadata.average_employees || ''}
                onChange={(e) => handleNumberChange('average_employees', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 145"
              />
              <small>Average employee count over the reporting year</small>
            </div>
          </div>
        </div>

        {/* ========== FINANCIAL DATA ========== */}
        <div className="form-section">
          <h3>💰 Financial Data</h3>
          <p className="section-hint">Used for revenue-based intensity metrics (tonnes CO2e per £1M revenue)</p>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="annual_revenue">Annual Revenue (£)</label>
              <input
                id="annual_revenue"
                type="number"
                min="0"
                step="1000"
                value={metadata.annual_revenue || ''}
                onChange={(e) => handleNumberChange('annual_revenue', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 5000000"
              />
              <small>Total annual revenue in GBP</small>
            </div>
            
            <div className="form-group">
              <label htmlFor="ebitda">EBITDA (£)</label>
              <input
                id="ebitda"
                type="number"
                min="0"
                step="1000"
                value={metadata.ebitda || ''}
                onChange={(e) => handleNumberChange('ebitda', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 750000"
              />
              <small>Earnings before interest, taxes, depreciation, amortization</small>
            </div>
            
            <div className="form-group">
              <label htmlFor="total_assets">Total Assets (£)</label>
              <input
                id="total_assets"
                type="number"
                min="0"
                step="1000"
                value={metadata.total_assets || ''}
                onChange={(e) => handleNumberChange('total_assets', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 12500000"
              />
            </div>
          </div>
        </div>

        {/* ========== FACILITY DATA ========== */}
        <div className="form-section">
          <h3>🏭 Facility & Operational Data</h3>
          <p className="section-hint">Used for facility efficiency metrics (tonnes CO2e per sqft or per facility)</p>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="total_facilities">Total Facilities</label>
              <input
                id="total_facilities"
                type="number"
                min="0"
                step="1"
                value={metadata.total_facilities || ''}
                onChange={(e) => handleNumberChange('total_facilities', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 5"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="total_floor_area_sqft">Total Floor Area (sq ft)</label>
              <input
                id="total_floor_area_sqft"
                type="number"
                min="0"
                step="100"
                value={metadata.total_floor_area_sqft || ''}
                onChange={(e) => handleNumberChange('total_floor_area_sqft', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 50000"
              />
              <small>Total square footage across all facilities</small>
            </div>
            
            <div className="form-group">
              <label htmlFor="occupied_floor_area_sqft">Occupied Floor Area (sq ft)</label>
              <input
                id="occupied_floor_area_sqft"
                type="number"
                min="0"
                step="100"
                value={metadata.occupied_floor_area_sqft || ''}
                onChange={(e) => handleNumberChange('occupied_floor_area_sqft', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 45000"
              />
              <small>Floor area currently in use/occupied</small>
            </div>
          </div>
        </div>

        {/* ========== SUSTAINABILITY DATA ========== */}
        <div className="form-section">
          <h3>🌱 Sustainability Metrics</h3>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="renewable_energy_percentage">Renewable Energy (%)</label>
              <input
                id="renewable_energy_percentage"
                type="number"
                min="0"
                max="100"
                step="0.5"
                value={metadata.renewable_energy_percentage || ''}
                onChange={(e) => handleNumberChange('renewable_energy_percentage', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 45"
              />
              <small>Percentage of energy from renewable sources</small>
            </div>
            
            <div className="form-group">
              <label htmlFor="carbon_offset_percentage">Carbon Offset (%)</label>
              <input
                id="carbon_offset_percentage"
                type="number"
                min="0"
                max="100"
                step="0.5"
                value={metadata.carbon_offset_percentage || ''}
                onChange={(e) => handleNumberChange('carbon_offset_percentage', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 20"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="energy_intensity">Energy Intensity (kWh/employee)</label>
              <input
                id="energy_intensity"
                type="number"
                min="0"
                step="100"
                value={metadata.energy_intensity || ''}
                onChange={(e) => handleNumberChange('energy_intensity', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 15000"
              />
              <small>kWh per employee or kWh per sqft</small>
            </div>
          </div>
        </div>

        {/* ========== REPORTING PREFERENCES ========== */}
        <div className="form-section">
          <h3>📊 Reporting & Compliance</h3>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="reporting_standard">Reporting Standard</label>
              <select
                id="reporting_standard"
                value={metadata.reporting_standard || 'SECR'}
                onChange={(e) => handleInputChange('reporting_standard', e.target.value)}
                disabled={!isAdmin}
              >
                <option value="SECR">SECR (UK)</option>
                <option value="CSRD">CSRD (EU)</option>
                <option value="ISSB">ISSB (International)</option>
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="fiscal_year_start">Fiscal Year Start</label>
              <input
                id="fiscal_year_start"
                type="date"
                value={metadata.fiscal_year_start || ''}
                onChange={(e) => handleInputChange('fiscal_year_start', e.target.value)}
                disabled={!isAdmin}
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="fiscal_year_end">Fiscal Year End</label>
              <input
                id="fiscal_year_end"
                type="date"
                value={metadata.fiscal_year_end || ''}
                onChange={(e) => handleInputChange('fiscal_year_end', e.target.value)}
                disabled={!isAdmin}
              />
            </div>
          </div>
        </div>

        {/* ========== CONTACT INFORMATION ========== */}
        <div className="form-section">
          <h3>📧 Primary Contacts</h3>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="primary_contact_name">Primary Contact Name</label>
              <input
                id="primary_contact_name"
                type="text"
                value={metadata.primary_contact_name || ''}
                onChange={(e) => handleInputChange('primary_contact_name', e.target.value)}
                disabled={!isAdmin}
                placeholder="John Doe"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="primary_contact_email">Primary Contact Email</label>
              <input
                id="primary_contact_email"
                type="email"
                value={metadata.primary_contact_email || ''}
                onChange={(e) => handleInputChange('primary_contact_email', e.target.value)}
                disabled={!isAdmin}
                placeholder="john@company.com"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="primary_contact_phone">Primary Contact Phone</label>
              <input
                id="primary_contact_phone"
                type="tel"
                value={metadata.primary_contact_phone || ''}
                onChange={(e) => handleInputChange('primary_contact_phone', e.target.value)}
                disabled={!isAdmin}
                placeholder="+44 123 456 7890"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="sustainability_officer_name">Sustainability Officer</label>
              <input
                id="sustainability_officer_name"
                type="text"
                value={metadata.sustainability_officer_name || ''}
                onChange={(e) => handleInputChange('sustainability_officer_name', e.target.value)}
                disabled={!isAdmin}
                placeholder="Jane Smith"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="sustainability_officer_email">Sustainability Officer Email</label>
              <input
                id="sustainability_officer_email"
                type="email"
                value={metadata.sustainability_officer_email || ''}
                onChange={(e) => handleInputChange('sustainability_officer_email', e.target.value)}
                disabled={!isAdmin}
                placeholder="jane@company.com"
              />
            </div>
          </div>
        </div>

        {/* ========== INDUSTRY CLASSIFICATION ========== */}
        <div className="form-section">
          <h3>🏷️ Industry Classification</h3>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="industry_sector">Industry Sector</label>
              <input
                id="industry_sector"
                type="text"
                value={metadata.industry_sector || ''}
                onChange={(e) => handleInputChange('industry_sector', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., Technology, Manufacturing, Retail"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="naics_code">NAICS Code</label>
              <input
                id="naics_code"
                type="text"
                value={metadata.naics_code || ''}
                onChange={(e) => handleInputChange('naics_code', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 541512"
              />
              <small>North American Industry Classification System</small>
            </div>
            
            <div className="form-group">
              <label htmlFor="sic_code">SIC Code</label>
              <input
                id="sic_code"
                type="text"
                value={metadata.sic_code || ''}
                onChange={(e) => handleInputChange('sic_code', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 7371"
              />
              <small>Standard Industrial Classification</small>
            </div>
          </div>
        </div>

        {/* ========== SUBMIT BUTTON ========== */}
        <div className="form-actions">
          <button
            type="submit"
            className="add-btn"
            disabled={!isAdmin || loading}
          >
            {loading ? '⏳ Saving...' : '💾 Save Organization Data'}
          </button>
          {!isAdmin && (
            <p className="hint-text">🔒 You have view-only access. Contact an admin to make changes.</p>
          )}
        </div>
      </form>
    </div>
  );
}

export default OrganizationMetadata;