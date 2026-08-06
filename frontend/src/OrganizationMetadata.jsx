// OrganizationMetadata.jsx - Updated with Individual Endpoints

import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import './css/OrganizationMetadata.css';
import toast from 'react-hot-toast';

function OrganizationMetadata({ organization, userRole }) {
  // State for all metadata sections
  const [orgData, setOrgData] = useState({
    name: '',
    company_number: '',
    country: 'UK',
    timezone: 'Europe/London',
    currency: 'GBP',
    reporting_standard: 'SECR',
    website: '',
  });

  const [employeeData, setEmployeeData] = useState({
    total_employees: 0,
    full_time_employees: 0,
    part_time_employees: 0,
    contract_employees: 0,
    average_employees: 0,
  });

  const [financialData, setFinancialData] = useState({
    annual_revenue: 0,
    ebitda: 0,
    total_assets: 0,
    fiscal_year_start: '',
    fiscal_year_end: '',
  });

  const [sustainabilityData, setSustainabilityData] = useState({
    renewable_energy_percentage: 0,
    carbon_offset_percentage: 0,
    energy_intensity: 0,
    reporting_standard: 'SECR',
  });

  const [contactData, setContactData] = useState({
    primary_contact_name: '',
    primary_contact_email: '',
    primary_contact_phone: '',
    sustainability_officer_name: '',
    sustainability_officer_email: '',
  });

  const [industryData, setIndustryData] = useState({
    industry_sector: '',
    naics_code: '',
    sic_code: '',
  });

  const [customMetrics, setCustomMetrics] = useState({});
  
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState(null);
  const isAdmin = userRole === 'admin';

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  // ============================================
  // FETCH ALL METADATA SECTIONS
  // ============================================
  const fetchMetadata = async () => {
    if (!organization?.id) {
      console.log('⏳ Waiting for organization...');
      setFetching(false);
      return;
    }

    try {
      setFetching(true);
      setError(null);
      const token = await getToken();
      const orgId = organization.id;

      // Fetch organization data
      const orgResponse = await fetch(
        `${API_URL}/api/organizations/${orgId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (orgResponse.ok) {
        const data = await orgResponse.json();
        setOrgData({
          name: data.name || '',
          company_number: data.company_number || '',
          country: data.country || 'UK',
          timezone: data.timezone || 'Europe/London',
          currency: data.currency || 'GBP',
          reporting_standard: data.reporting_standard || 'SECR',
          website: data.website || '',
        });
      }

      // Fetch all metadata sections in parallel
      const [employeeRes, financialRes, sustainabilityRes, contactRes, industryRes, customRes] = await Promise.all([
        fetch(`${API_URL}/api/organizations/${orgId}/metadata/employees`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/organizations/${orgId}/metadata/financials`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/organizations/${orgId}/metadata/sustainability`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/organizations/${orgId}/metadata/contacts`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/organizations/${orgId}/metadata/industry`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/organizations/${orgId}/metadata/custom-metrics`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
      ]);

      // Process employee data
      if (employeeRes.ok) {
        const data = await employeeRes.json();
        setEmployeeData(data.data || {});
      }

      // Process financial data
      if (financialRes.ok) {
        const data = await financialRes.json();
        setFinancialData({
          annual_revenue: data.data?.annual_revenue || 0,
          ebitda: data.data?.ebitda || 0,
          total_assets: data.data?.total_assets || 0,
          fiscal_year_start: data.data?.fiscal_year_start || '',
          fiscal_year_end: data.data?.fiscal_year_end || '',
        });
      }

      // Process sustainability data
      if (sustainabilityRes.ok) {
        const data = await sustainabilityRes.json();
        setSustainabilityData({
          renewable_energy_percentage: data.data?.renewable_energy_percentage || 0,
          carbon_offset_percentage: data.data?.carbon_offset_percentage || 0,
          energy_intensity: data.data?.energy_intensity || 0,
          reporting_standard: data.data?.reporting_standard || 'SECR',
        });
      }

      // Process contact data
      if (contactRes.ok) {
        const data = await contactRes.json();
        setContactData(data.data || {});
      }

      // Process industry data
      if (industryRes.ok) {
        const data = await industryRes.json();
        setIndustryData(data.data || {});
      }

      // Process custom metrics
      if (customRes.ok) {
        const data = await customRes.json();
        setCustomMetrics(data.data || {});
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
    } else {
      setFetching(false);
    }
  }, [organization?.id]);

  // ============================================
  // HANDLE CHANGES
  // ============================================
  const handleOrgChange = (field, value) => {
    setOrgData(prev => ({ ...prev, [field]: value }));
  };

  const handleEmployeeChange = (field, value) => {
    const numValue = value === '' ? 0 : parseFloat(value) || 0;
    setEmployeeData(prev => ({ ...prev, [field]: numValue }));
  };

  const handleFinancialChange = (field, value) => {
    const numValue = value === '' ? 0 : parseFloat(value) || 0;
    setFinancialData(prev => ({ ...prev, [field]: numValue }));
  };

  const handleSustainabilityChange = (field, value) => {
    const numValue = value === '' ? 0 : parseFloat(value) || 0;
    setSustainabilityData(prev => ({ ...prev, [field]: numValue }));
  };

  const handleContactChange = (field, value) => {
    setContactData(prev => ({ ...prev, [field]: value }));
  };

  const handleIndustryChange = (field, value) => {
    setIndustryData(prev => ({ ...prev, [field]: value }));
  };

  // ============================================
  // SAVE ALL METADATA SECTIONS
  // ============================================
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!organization?.id) {
      toast.error('No organization found. Please set up your organization first.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = await getToken();
      const orgId = organization.id;
      let hasError = false;

      // Step 1: Update organization
      const orgPayload = {
        name: orgData.name,
        company_number: orgData.company_number || null,
        country: orgData.country || 'UK',
        timezone: orgData.timezone || 'Europe/London',
        currency: orgData.currency || 'GBP',
        reporting_standard: orgData.reporting_standard || 'SECR',
        website: orgData.website || null,
        updated_at: new Date().toISOString()
      };

      const orgResponse = await fetch(
        `${API_URL}/api/organizations/${orgId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(orgPayload),
        }
      );

      if (!orgResponse.ok) {
        hasError = true;
        toast.error('Failed to update organization details');
      }

      // Step 2: Update employee metadata
      const employeePayload = { ...employeeData };
      const empResponse = await fetch(
        `${API_URL}/api/organizations/${orgId}/metadata/employees`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(employeePayload),
        }
      );

      if (!empResponse.ok) {
        hasError = true;
        toast.error('Failed to update employee data');
      }

      // Step 3: Update financial metadata
      const financialPayload = { ...financialData };
      const finResponse = await fetch(
        `${API_URL}/api/organizations/${orgId}/metadata/financials`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(financialPayload),
        }
      );

      if (!finResponse.ok) {
        hasError = true;
        toast.error('Failed to update financial data');
      }

      // Step 4: Update sustainability metadata
      const sustainPayload = { ...sustainabilityData };
      const susResponse = await fetch(
        `${API_URL}/api/organizations/${orgId}/metadata/sustainability`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(sustainPayload),
        }
      );

      if (!susResponse.ok) {
        hasError = true;
        toast.error('Failed to update sustainability data');
      }

      // Step 5: Update contact metadata
      const contactPayload = { ...contactData };
      const contResponse = await fetch(
        `${API_URL}/api/organizations/${orgId}/metadata/contacts`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(contactPayload),
        }
      );

      if (!contResponse.ok) {
        hasError = true;
        toast.error('Failed to update contact data');
      }

      // Step 6: Update industry metadata
      const industryPayload = { ...industryData };
      const indResponse = await fetch(
        `${API_URL}/api/organizations/${orgId}/metadata/industry`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(industryPayload),
        }
      );

      if (!indResponse.ok) {
        hasError = true;
        toast.error('Failed to update industry data');
      }

      if (!hasError) {
        toast.success('✅ Organization data saved successfully!');
        await fetchMetadata(); // Refresh data
      } else {
        toast.warning('Some sections failed to save. Please review and try again.');
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
        {/* ========== COMPANY INFORMATION ========== */}
        <div className="form-section">
          <h3>🏢 Company Information</h3>
          <p className="section-hint">Basic company details used for report headers and compliance</p>
          
          <div className="form-grid">
            <div className="form-group full-width">
              <label htmlFor="name">Company Name *</label>
              <input
                id="name"
                type="text"
                value={orgData.name || ''}
                onChange={(e) => handleOrgChange('name', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., Babui Limited"
                required
              />
              <small>This will appear on all reports and documents</small>
            </div>
            
            <div className="form-group">
              <label htmlFor="company_number">Company Registration Number</label>
              <input
                id="company_number"
                type="text"
                value={orgData.company_number || ''}
                onChange={(e) => handleOrgChange('company_number', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 12345678"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="website">Website</label>
              <input
                id="website"
                type="url"
                value={orgData.website || ''}
                onChange={(e) => handleOrgChange('website', e.target.value)}
                disabled={!isAdmin}
                placeholder="https://www.company.com"
              />
            </div>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="country">Country</label>
              <select
                id="country"
                value={orgData.country || 'UK'}
                onChange={(e) => handleOrgChange('country', e.target.value)}
                disabled={!isAdmin}
              >
                <option value="UK">🇬🇧 United Kingdom</option>
                <option value="US">🇺🇸 United States</option>
                <option value="EU">🇪🇺 Europe</option>
                <option value="Other">🌍 Other</option>
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="currency">Currency</label>
              <select
                id="currency"
                value={orgData.currency || 'GBP'}
                onChange={(e) => handleOrgChange('currency', e.target.value)}
                disabled={!isAdmin}
              >
                <option value="GBP">💷 GBP (£)</option>
                <option value="USD">💵 USD ($)</option>
                <option value="EUR">💶 EUR (€)</option>
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="timezone">Timezone</label>
              <select
                id="timezone"
                value={orgData.timezone || 'Europe/London'}
                onChange={(e) => handleOrgChange('timezone', e.target.value)}
                disabled={!isAdmin}
              >
                <option value="Europe/London">🇬🇧 London (GMT/BST)</option>
                <option value="Europe/Paris">🇫🇷 Paris (CET)</option>
                <option value="America/New_York">🇺🇸 New York (EST/EDT)</option>
                <option value="America/Los_Angeles">🇺🇸 Los Angeles (PST/PDT)</option>
                <option value="Asia/Dubai">🇦🇪 Dubai (GST)</option>
                <option value="Asia/Singapore">🇸🇬 Singapore (SGT)</option>
                <option value="Australia/Sydney">🇦🇺 Sydney (AEST/AEDT)</option>
              </select>
            </div>
          </div>
        </div>

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
                value={employeeData.total_employees || ''}
                onChange={(e) => handleEmployeeChange('total_employees', e.target.value)}
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
                value={employeeData.full_time_employees || ''}
                onChange={(e) => handleEmployeeChange('full_time_employees', e.target.value)}
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
                value={employeeData.part_time_employees || ''}
                onChange={(e) => handleEmployeeChange('part_time_employees', e.target.value)}
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
                value={employeeData.average_employees || ''}
                onChange={(e) => handleEmployeeChange('average_employees', e.target.value)}
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
                value={financialData.annual_revenue || ''}
                onChange={(e) => handleFinancialChange('annual_revenue', e.target.value)}
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
                value={financialData.ebitda || ''}
                onChange={(e) => handleFinancialChange('ebitda', e.target.value)}
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
                value={financialData.total_assets || ''}
                onChange={(e) => handleFinancialChange('total_assets', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 12500000"
              />
            </div>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="fiscal_year_start">Fiscal Year Start</label>
              <input
                id="fiscal_year_start"
                type="date"
                value={financialData.fiscal_year_start || ''}
                onChange={(e) => handleFinancialChange('fiscal_year_start', e.target.value)}
                disabled={!isAdmin}
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="fiscal_year_end">Fiscal Year End</label>
              <input
                id="fiscal_year_end"
                type="date"
                value={financialData.fiscal_year_end || ''}
                onChange={(e) => handleFinancialChange('fiscal_year_end', e.target.value)}
                disabled={!isAdmin}
              />
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
                value={sustainabilityData.renewable_energy_percentage || ''}
                onChange={(e) => handleSustainabilityChange('renewable_energy_percentage', e.target.value)}
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
                value={sustainabilityData.carbon_offset_percentage || ''}
                onChange={(e) => handleSustainabilityChange('carbon_offset_percentage', e.target.value)}
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
                value={sustainabilityData.energy_intensity || ''}
                onChange={(e) => handleSustainabilityChange('energy_intensity', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., 15000"
              />
              <small>kWh per employee or kWh per sqft</small>
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
                value={contactData.primary_contact_name || ''}
                onChange={(e) => handleContactChange('primary_contact_name', e.target.value)}
                disabled={!isAdmin}
                placeholder="John Doe"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="primary_contact_email">Primary Contact Email</label>
              <input
                id="primary_contact_email"
                type="email"
                value={contactData.primary_contact_email || ''}
                onChange={(e) => handleContactChange('primary_contact_email', e.target.value)}
                disabled={!isAdmin}
                placeholder="john@company.com"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="primary_contact_phone">Primary Contact Phone</label>
              <input
                id="primary_contact_phone"
                type="tel"
                value={contactData.primary_contact_phone || ''}
                onChange={(e) => handleContactChange('primary_contact_phone', e.target.value)}
                disabled={!isAdmin}
                placeholder="+44 123 456 7890"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="sustainability_officer_name">Sustainability Officer</label>
              <input
                id="sustainability_officer_name"
                type="text"
                value={contactData.sustainability_officer_name || ''}
                onChange={(e) => handleContactChange('sustainability_officer_name', e.target.value)}
                disabled={!isAdmin}
                placeholder="Jane Smith"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="sustainability_officer_email">Sustainability Officer Email</label>
              <input
                id="sustainability_officer_email"
                type="email"
                value={contactData.sustainability_officer_email || ''}
                onChange={(e) => handleContactChange('sustainability_officer_email', e.target.value)}
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
                value={industryData.industry_sector || ''}
                onChange={(e) => handleIndustryChange('industry_sector', e.target.value)}
                disabled={!isAdmin}
                placeholder="e.g., Technology, Manufacturing, Retail"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="naics_code">NAICS Code</label>
              <input
                id="naics_code"
                type="text"
                value={industryData.naics_code || ''}
                onChange={(e) => handleIndustryChange('naics_code', e.target.value)}
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
                value={industryData.sic_code || ''}
                onChange={(e) => handleIndustryChange('sic_code', e.target.value)}
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