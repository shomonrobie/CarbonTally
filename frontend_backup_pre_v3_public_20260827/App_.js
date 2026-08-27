// App.js - Refactored with API Endpoints

import React, { useState, useEffect, useMemo } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, Link } from 'react-router-dom';
import { supabase } from './supabaseClient';
import Login from './Login';
import * as XLSX from 'xlsx';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './App.css';
import TeamManagement from './TeamManagement';
import AssetManager from './AssetManager';
import CookieBanner from './CookieBanner';
import PrivacyPolicy from './PrivacyPolicy';
import CookiePolicy from './CookiePolicy';
import PricingPage from './PricingPage';
import TermsPage from './TermsPage';
import LandingPage from './LandingPage';
import CarbonReductionPlan from './CarbonReductionPlan';
import AboutUs from './AboutUs';
import BulkUpload from './BulkUpload';
import RecentProcessedData from './RecentProcessedData';
import PDFIngestionPortal from './PDFIngestionPortal';
import toast from 'react-hot-toast';
import OnboardingWizard from './OnboardingWizard';

// API Constants
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Constants
const DEFRA_FACTORS = { 
  'Diesel': 2.54, 
  'Petrol': 2.16, 
  'AdBlue': 0.0, 
  'Unknown Fuel': 0.0,
  'Electricity': 0.20712, 
  'Natural Gas': 0.18316, 
  'Unknown Utility': 0.0,
  'Flight (Short Haul)': 0.155, 
  'Flight (Long Haul)': 0.195, 
  'Rail (National)': 0.035, 
  'Hotel Stay': 10.5, 
  'Mixed Waste': 0.500, 
  'Recycled Waste': -0.050, 
  'Unknown Scope 3': 0.0 
};

const FIELD_CONFIGS = {
  fuel: { 
    type: 'Standardized Fuel', 
    volume: 'Volume (L)', 
    factor: 'DEFRA Factor (kgCO2e/L)', 
    site: 'Vehicle Registration', 
    date: 'Transaction Date' 
  },
  utility: { 
    type: 'Standardized Utility', 
    volume: 'Consumption (kWh)', 
    factor: 'DEFRA Factor (kgCO2e/kWh)', 
    site: 'Site Name', 
    date: 'Billing Period Start' 
  },
  scope3: { 
    type: 'Standardized Scope3', 
    volume: 'Quantity', 
    factor: 'DEFRA Factor', 
    site: 'Description', 
    date: 'Date' 
  }
};

const CATEGORY_OPTIONS = {
  utility: ['Electricity', 'Natural Gas'],
  scope3: [
    'Flight (Short Haul)', 'Flight (Long Haul)', 
    'Rail (National)', 'Hotel Stay', 
    'Mixed Waste', 'Recycled Waste'
  ],
  fuel: ['Diesel', 'Petrol', 'AdBlue']
};

// ============================================
// AUTH HELPERS
// ============================================

const getToken = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || localStorage.getItem('access_token');
};

const fetchWithAuth = async (endpoint, options = {}) => {
  const token = await getToken();
  
  // Ensure endpoint starts with /api
  let url = endpoint;
  if (!url.startsWith('/api')) {
    url = `/api${url.startsWith('/') ? url : '/' + url}`;
  }
  
  const fullUrl = `${API_URL}${url}`;
  
  const response = await fetch(fullUrl, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    console.error(`❌ API Error ${response.status}: ${fullUrl}`);
  }
  
  return response;
};

// ============================================
// PROTECTED ROUTE
// ============================================

function ProtectedRoute({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (loading) return <div className="loading-screen">Loading...</div>;
  if (!session) return <Navigate to="/" replace />;
  return children;
}

function DashboardLayout({ children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {children}
      <footer className="footer-bottom-dashboard">
        <div className="footer-bottom-content">
          <p>© {new Date().getFullYear()} CarbonTally (UK) Ltd. All rights reserved.</p>
          <div className="footer-legal-links">
            <Link to="/privacy">Privacy Policy</Link>
            <Link to="/cookies">Cookie Policy</Link>
            <Link to="/terms">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

// ============================================
// MAIN DASHBOARD COMPONENT
// ============================================

function Dashboard() {
  const navigate = useNavigate();
  
  // Auth & Organization State
  const [session, setSession] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [userRole, setUserRole] = useState(null);
  
  // UI State
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showBulkUpload, setShowBulkUpload] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState('');
  
  // Onboarding State
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  
  // Upload State
  const [file, setFile] = useState(null);
  const [uploadType, setUploadType] = useState('fuel');
  const [result, setResult] = useState(null);
  const [data, setData] = useState([]);
  
  // Data Processing State
  const [cleanData, setCleanData] = useState([]);
  const [flaggedData, setFlaggedData] = useState([]);
  const [pdfFile, setPdfFile] = useState(null);
  const [showPDFPortal, setShowPDFPortal] = useState(false);
  
  // Dashboard Data
  const [dashboardStats, setDashboardStats] = useState({ 
    totalEmissions: 0, 
    totalTransactions: 0 
  });
  const [historyData, setHistoryData] = useState([]);
  const [assets, setAssets] = useState([]);
  const [facilities, setFacilities] = useState([]);
  
  // Year selector state
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  // ============================================
  // COMPUTED DATA
  // ============================================

  const trendData = useMemo(() => {
    if (!historyData.length) return [];
    const grouped = {};
    historyData.forEach(row => {
      const month = row.start_date ? row.start_date.substring(0, 7) : 'Unknown';
      grouped[month] = (grouped[month] || 0) + (parseFloat(row.calculated_kg_co2e) || 0);
    });
    return Object.keys(grouped).sort().map(month => ({ 
      month, 
      tonnes: parseFloat((grouped[month] / 1000).toFixed(2)) 
    }));
  }, [historyData]);

  const availableYears = useMemo(() => {
    if (!historyData || historyData.length === 0) {
      if (dashboardStats.totalTransactions > 0) {
        return [new Date().getFullYear()];
      }
      return [];
    }
    const years = new Set();
    historyData.forEach(row => {
      if (row.start_date) {
        const year = parseInt(row.start_date.substring(0, 4));
        if (!isNaN(year)) {
          years.add(year);
        }
      }
    });
    return Array.from(years).sort((a, b) => b - a);
  }, [historyData]);

  // ============================================
  // API DATA FETCHING FUNCTIONS
  // ============================================

  // ✅ GET /api/organizations/{org_id}/assets/stats
  const fetchDashboardStats = async (orgId) => {
    try {
      const response = await fetchWithAuth(`/api/organizations/${orgId}/assets/stats`);
      
      if (!response.ok) {
        // Fallback to facilities/stats
        const fallbackResponse = await fetchWithAuth(`/api/organizations/${orgId}/facilities/stats`);
        if (!fallbackResponse.ok) throw new Error('Failed to fetch stats');
        
        const data = await fallbackResponse.json();
        setDashboardStats({
          totalEmissions: data.data?.total_assets || 0,
          totalTransactions: data.data?.active_assets || 0
        });
        return;
      }
      
      const data = await response.json();
      setDashboardStats({
        totalEmissions: data.data?.total_assets || 0,
        totalTransactions: data.data?.active_assets || 0
      });
    } catch (error) {
      console.error('❌ Error fetching dashboard stats:', error);
      setDashboardStats({ totalEmissions: 0, totalTransactions: 0 });
    }
  };

  // ✅ GET /api/organizations/{org_id}/emissions-data
  const fetchHistory = async () => {
    if (!organization) {
      console.log("⏳ Waiting for organization data...");
      return;
    }

    console.log("🚀 Fetching history for org:", organization.id);
    setLoadingHistory(true);
    
    try {
      let response = await fetchWithAuth(`/api/organizations/${organization.id}/emissions-data?limit=10000`);
      
      if (!response.ok) {
        // Fallback to /api/emissions
        response = await fetchWithAuth(`/api/emissions?organization_id=${organization.id}&limit=10000`);
      }
      
      if (!response.ok) throw new Error('Failed to fetch history');
      
      const data = await response.json();
      setHistoryData(data.records || data.emissions || []);
      console.log(`✅ History fetched: ${data.records?.length || 0} records`);
    } catch (error) {
      console.error("❌ Error fetching history:", error);
      setHistoryData([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  // ✅ GET /api/organizations/{org_id}/assets
  const fetchAssets = async (orgId) => {
    try {
      const response = await fetchWithAuth(`/api/organizations/${orgId}/assets?limit=1000`);
      if (!response.ok) throw new Error('Failed to fetch assets');
      
      const data = await response.json();
      setAssets(data.assets || []);
      return data.assets || [];
    } catch (error) {
      console.error('❌ Error fetching assets:', error);
      setAssets([]);
      return [];
    }
  };

  // ✅ GET /api/organizations/{org_id}/facilities
  const fetchFacilities = async (orgId) => {
    try {
      const response = await fetchWithAuth(`/api/organizations/${orgId}/facilities?limit=1000`);
      if (!response.ok) throw new Error('Failed to fetch facilities');
      
      const data = await response.json();
      setFacilities(data.facilities || []);
      return data.facilities || [];
    } catch (error) {
      console.error('❌ Error fetching facilities:', error);
      setFacilities([]);
      return [];
    }
  };

  // ✅ GET /api/organizations/members/{user_id}
  const fetchOrganization = async (userId) => {
    try {
      const response = await fetchWithAuth(`/api/organizations/members/${userId}`);
      if (!response.ok) throw new Error('Failed to fetch organization');
      
      const data = await response.json();
      
      if (data?.organization) {
        setOrganization(data.organization);
        setUserRole(data.role);
        return data.organization;
      } else if (data?.organizations && data.organizations.length > 0) {
        const org = data.organizations[0];
        setOrganization(org);
        setUserRole('admin');
        return org;
      }
      return null;
    } catch (error) {
      console.error('❌ Error fetching organization:', error);
      return null;
    }
  };

  // ✅ GET /api/defra-factors/{year}
  const fetchDefraFactors = async (year) => {
    try {
      const response = await fetchWithAuth(`/api/defra-factors/${year}`);
      if (!response.ok) {
        // Try without year
        const fallbackResponse = await fetchWithAuth(`/api/defra-factors`);
        if (!fallbackResponse.ok) throw new Error('Failed to fetch DEFRA factors');
        return await fallbackResponse.json();
      }
      return await response.json();
    } catch (error) {
      console.error('❌ Error fetching DEFRA factors:', error);
      return null;
    }
  };

  // ✅ POST /api/emissions
  const saveEmissions = async (records) => {
    try {
      const response = await fetchWithAuth('/api/emissions', {
        method: 'POST',
        body: JSON.stringify({
          organization_id: organization.id,
          records: records
        })
      });
      
      if (!response.ok) throw new Error('Failed to save emissions');
      return await response.json();
    } catch (error) {
      console.error('❌ Error saving emissions:', error);
      throw error;
    }
  };

  // ============================================
  // ORGANIZATION LOADING
  // ============================================

  const loadOrganizationData = async (org) => {
    if (!org) return;
    
    try {
      await Promise.all([
        fetchDashboardStats(org.id),
        fetchAssets(org.id),
        fetchFacilities(org.id),
        fetchHistory()
      ]);
    } catch (error) {
      console.error('❌ Error loading organization data:', error);
    }
  };

  // ============================================
  // EFFECTS
  // ============================================

  useEffect(() => {
    const initOrg = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setSession(session);
      
      if (session) {
        const org = await fetchOrganization(session.user.id);
        if (org) {
          await loadOrganizationData(org);
        }
      }
    };

    initOrg();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session) {
        fetchOrganization(session.user.id).then(org => {
          if (org) loadOrganizationData(org);
        });
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  // Check onboarding
  useEffect(() => {
    const checkOnboarding = async () => {
      if (!organization) {
        setOnboardingChecked(true);
        return;
      }

      try {
        const response = await fetchWithAuth(`/api/organizations/${organization.id}/facilities?limit=1`);
        if (!response.ok) throw new Error('Failed to check facilities');
        
        const data = await response.json();
        const facilitiesList = data.facilities || [];

        if (facilitiesList.length === 0) {
          console.log('🚀 No facilities found - showing onboarding');
          setShowOnboarding(true);
        } else {
          console.log('✅ Facilities found - skipping onboarding');
          setShowOnboarding(false);
        }
      } catch (error) {
        console.error('Error checking facilities:', error);
      }

      setOnboardingChecked(true);
    };

    checkOnboarding();
  }, [organization]);

  // Update clean/flagged data
  useEffect(() => {
    const flagged = data.filter(row => row.needs_review);
    const clean = data.filter(row => !row.needs_review);
    setFlaggedData(flagged);
    setCleanData(clean);
  }, [data]);

  // Update selected year
  useEffect(() => {
    if (availableYears.length > 0) {
      setSelectedYear(availableYears[0]);
    }
  }, [availableYears]);

  // ============================================
  // FILE UPLOAD FUNCTIONS
  // ============================================

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    const isPDF = selectedFile.type === 'application/pdf' || selectedFile.name.toLowerCase().endsWith('.pdf');
    const isImage = selectedFile.type.startsWith('image/');

    if (isPDF || isImage) {
      setPdfFile(selectedFile);
      setShowPDFPortal(true);
      setFile(null);
      setError('');
    } else {
      setFile(selectedFile);
      setPdfFile(null);
      setShowPDFPortal(false);
      setError('');
    }
  };

  // ✅ POST /api/upload-csv
  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('data_type', uploadType);

    try {
      const token = await getToken();
      
      const response = await fetch(`${API_URL}/api/upload-csv`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });
      
      if (!response.ok) throw new Error(`Upload failed: ${response.status}`);
      
      const result = await response.json();
      setResult(result);
      setData(result.data);
      toast.success('✅ CSV processed successfully!');
    } catch (err) {
      console.error('❌ Upload error:', err);
      setError('Error processing file: ' + (err.message));
      toast.error('❌ Failed to process CSV');
    } finally { 
      setLoading(false); 
    }
  };

  // ============================================
  // DATA PROCESSING FUNCTIONS
  // ============================================

  const getFieldConfig = (type) => {
    return FIELD_CONFIGS[type] || FIELD_CONFIGS.fuel;
  };

  const calculateEmissions = (row, fieldConfig) => {
    const volume = parseFloat(row[fieldConfig.volume]);
    const factor = parseFloat(row[fieldConfig.factor]);
    
    if (!isNaN(volume) && !isNaN(factor)) {
      return parseFloat((volume * factor).toFixed(2));
    }
    return 0;
  };

  const handleInputChange = (index, field, value) => {
    const newData = [...data];
    const row = { ...newData[index] };
    const dataType = result?.data_type || 'fuel';
    const fieldConfig = getFieldConfig(dataType);

    row[field] = value;

    if (field === fieldConfig.type) {
      row[fieldConfig.factor] = DEFRA_FACTORS[value] || 0;
    }

    row['Total kgCO2e'] = calculateEmissions(row, fieldConfig);

    newData[index] = row;
    setData(newData);
  };

  const validateRow = (index) => {
    const newData = [...data];
    const row = { ...newData[index] };
    const dataType = result?.data_type || 'fuel';
    const fieldConfig = getFieldConfig(dataType);

    const volume = parseFloat(row[fieldConfig.volume]);
    const site = row[fieldConfig.site];

    const hasValidVolume = !isNaN(volume) && volume > 0;
    const hasValidType = row[fieldConfig.type] && !row[fieldConfig.type].toLowerCase().includes('unknown');
    const hasValidSite = site && site !== '' && site !== 'UNKNOWN' && site !== 'UNKNOWN_SITE';

    if (hasValidVolume && hasValidType && hasValidSite) {
      row['needs_review'] = false;
      row['review_reason'] = '';
      row['Total kgCO2e'] = calculateEmissions(row, fieldConfig);
    } else {
      row['needs_review'] = true;
      if (!hasValidVolume) row['review_reason'] = `Missing/Invalid ${fieldConfig.volume}`;
      else if (!hasValidType) row['review_reason'] = 'Unrecognized Category';
      else if (!hasValidSite) row['review_reason'] = `Missing ${fieldConfig.site}`;
    }

    newData[index] = row;
    setData(newData);
  };

  // ✅ POST /api/emissions
  const handleSaveToDatabase = async () => {
    if (!organization || !session) {
      setError('You must be logged in to save data.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const dataType = result?.data_type || 'fuel';
      const fieldConfig = getFieldConfig(dataType);

      // Fetch DEFRA factors from API
      const currentYear = new Date().getFullYear();
      const defraData = await fetchDefraFactors(currentYear);
      
      const defraMap = {};
      if (defraData?.factors) {
        defraData.factors.forEach(f => {
          defraMap[f.activity_type] = f.id;
        });
      }

      const recordsToSave = cleanData.map(row => {
        const rawName = row[fieldConfig.site];
        const fuelType = row[fieldConfig.type];
        
        const matchedAsset = assets.find(a => 
          a.name.toUpperCase() === rawName?.toUpperCase()
        );
        
        const defraFactorId = defraMap[fuelType] || null;

        return {
          organization_id: organization.id,
          asset_id: matchedAsset ? matchedAsset.id : null,
          defra_factor_id: defraFactorId,
          start_date: row[fieldConfig.date], 
          end_date: row[fieldConfig.date],
          raw_quantity: parseFloat(row[fieldConfig.volume]) || 0,
          calculated_kg_co2e: parseFloat(row['Total kgCO2e']) || 0,
          created_by_user_id: session.user.id,
          metadata: {
            scope: dataType === 'scope3' ? 'Scope 3' : (dataType === 'utility' ? 'Scope 2' : 'Scope 1'),
            asset_name: rawName,
            fuel_type: fuelType,
            defra_factor_used: row[fieldConfig.factor],
            original_filename: result.filename,
            auto_mapped: !!matchedAsset
          }
        };
      });

      await saveEmissions(recordsToSave);

      toast.success(`✅ Successfully saved ${cleanData.length} records!`);
      
      await fetchHistory();
      await fetchDashboardStats(organization.id);
      
      setResult(null);
      setData([]);
      setCleanData([]);
      setFlaggedData([]);
      setFile(null);
      setActiveTab('dashboard');

    } catch (err) {
      console.error("Database Save Error:", err);
      setError('Failed to save: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // EXPORT FUNCTIONS
  // ============================================

  const exportSECRReport = () => {
    const wb = XLSX.utils.book_new();
    const summaryData = [
      ["CarbonTally SECR REPORT", ""],
      ["Company:", organization?.name || "N/A"],
      ["Total Gross Emissions", (dashboardStats.totalEmissions / 1000).toFixed(2), "tonnes CO2e"],
      ["Total Transactions", dashboardStats.totalTransactions]
    ];
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(summaryData), "Summary");
    XLSX.writeFile(wb, `CarbonTally_Report_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setSession(null);
    setOrganization(null);
    setResult(null);
    setData([]);
    navigate('/');
  };

  // ============================================
  // RENDER FUNCTIONS
  // ============================================

  const renderFileUpload = () => (
    <div className="upload-section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ margin: 0 }}>Upload Data Statement</h2>
        <button
          onClick={() => setShowBulkUpload(true)}
          style={{
            padding: '0.6rem 1.2rem',
            backgroundColor: '#16a34a',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontWeight: '600',
            cursor: 'pointer',
            fontSize: '0.9rem',
          }}
        >
          📦 Switch to Bulk Upload
        </button>
      </div>
      
      <div className="upload-type-selector">
        <label className={`type-option ${uploadType === 'fuel' ? 'active' : ''}`}>
          <input type="radio" name="uploadType" value="fuel" checked={uploadType === 'fuel'} onChange={() => setUploadType('fuel')} />
          ⛽ Scope 1: Fuel
        </label>
        <label className={`type-option ${uploadType === 'utility' ? 'active' : ''}`}>
          <input type="radio" name="uploadType" value="utility" checked={uploadType === 'utility'} onChange={() => setUploadType('utility')} />
          🔌 Scope 2: Utility
        </label>
        <label className={`type-option ${uploadType === 'scope3' ? 'active' : ''}`}>
          <input type="radio" name="uploadType" value="scope3" checked={uploadType === 'scope3'} onChange={() => setUploadType('scope3')} />
          🌱 Scope 3: Travel/Waste
        </label>
      </div>

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileChange({ target: { files: e.dataTransfer.files } });
          }
        }}
        onClick={() => document.getElementById('singleFileInput').click()}
        style={{
          border: `2px dashed ${file ? '#16a34a' : '#cbd5e1'}`,
          borderRadius: '12px',
          padding: '3rem 1rem',
          textAlign: 'center',
          backgroundColor: file ? '#f0fdf4' : '#f8fafc',
          marginBottom: '1.5rem',
          cursor: 'pointer',
          transition: 'all 0.2s ease'
        }}
      >
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>
          {file ? '✅' : '📄'}
        </div>
        <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem', fontWeight: '600', color: '#0f172a' }}>
          {file ? file.name : 'Drag & drop your file here'}
        </p>
        <p style={{ color: '#64748b', marginBottom: '0.5rem' }}>
          or click to browse
        </p>
        <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
          Supports CSV, XLSX, PDF, JPG, PNG
        </p>
        
        <input
          id="singleFileInput"
          type="file"
          accept=".csv,.xlsx,.pdf,.jpg,.jpeg,.png"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </div>

      {file && (
        <button 
          onClick={() => {
            setFile(null);
            const fileInput = document.getElementById('singleFileInput');
            if (fileInput) fileInput.value = '';
          }}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#ffffff',
            color: '#ef4444',
            border: '1px solid #fca5a5',
            borderRadius: '6px',
            cursor: 'pointer',
            marginBottom: '1rem',
            fontWeight: '500',
            fontSize: '0.875rem'
          }}
        >
          ✕ Remove File
        </button>
      )}

      <button onClick={handleUpload} disabled={loading || !file} className="upload-button" style={{ width: '100%' }}>
        {loading ? 'Processing...' : (
          uploadType === 'fuel' ? 'Calculate Scope 1 Emissions' :
          uploadType === 'utility' ? 'Calculate Scope 2 Emissions' :
          'Calculate Scope 3 Emissions'
        )}
      </button>

      {error && <div className="error">{error}</div>}
    </div>
  );

  const renderReviewQueue = () => {
    if (!result) return null;

    const dataType = result?.data_type || 'fuel';
    const fieldConfig = getFieldConfig(dataType);
    const categoryOptions = CATEGORY_OPTIONS[dataType] || [];

    return (
      <>
        <div className="tabs">
          <button className={`tab-btn ${cleanData.length > 0 ? 'active' : ''}`}>
            Verified ({cleanData.length})
          </button>
          <button className={`tab-btn ${flaggedData.length > 0 ? 'active' : ''}`}>
            Review Queue ({flaggedData.length})
          </button>
        </div>

        {flaggedData.length > 0 && (
          <div className="review-section">
            <h2>⚠️ Data Review Required</h2>
            <table className="review-table">
              <thead>
                <tr>
                  <th>{dataType === 'utility' ? 'Billing Period' : 'Date'}</th>
                  <th>{dataType === 'utility' ? 'Site / Facility' : dataType === 'scope3' ? 'Description' : 'Vehicle'}</th>
                  <th>Issue</th>
                  <th>{dataType === 'utility' ? 'Utility Type' : dataType === 'scope3' ? 'Category' : 'Fuel Type'}</th>
                  <th>{dataType === 'utility' ? 'Consumption (kWh)' : dataType === 'scope3' ? 'Quantity' : 'Volume (L)'}</th>
                  <th>kgCO2e</th>
                </tr>
              </thead>
              <tbody>
                {flaggedData.map((row, dataIndex) => {
                  const index = data.indexOf(row);
                  const fields = getFieldConfig(dataType);

                  return (
                    <tr key={dataIndex} className="flagged-row">
                      <td>{row[fields.date] || 'N/A'}</td>
                      <td>{row[fields.site] || 'N/A'}</td>
                      <td style={{ color: '#ef4444', fontSize: '0.875rem' }}>
                        {row.review_reason || 'Review needed'}
                      </td>
                      <td>
                        <select 
                          value={row[fields.type] || ''} 
                          onChange={(e) => handleInputChange(index, fields.type, e.target.value)}
                          onBlur={() => validateRow(index)}
                          className="edit-input"
                        >
                          <option value="">Select Category...</option>
                          {categoryOptions.map(option => (
                            <option key={option} value={option}>{option}</option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <input 
                          type="number" 
                          step="0.01"
                          value={row[fields.volume] === null ? '' : row[fields.volume]} 
                          onChange={(e) => handleInputChange(index, fields.volume, e.target.value === '' ? null : parseFloat(e.target.value))}
                          onBlur={() => validateRow(index)}
                          className="edit-input"
                          placeholder={dataType === 'utility' ? "e.g., 4500" : dataType === 'scope3' ? "e.g., 1500" : "e.g., 45.2"}
                        />
                      </td>
                      <td>{row['Total kgCO2e'] || 0}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>                  
          </div>
        )}

        <div className="action-buttons">
          <button 
            onClick={handleSaveToDatabase} 
            disabled={loading || cleanData.length === 0} 
            className="save-button"
          >
            💾 Save {cleanData.length} Verified Records to Database
          </button>
        </div>
      </>
    );
  };

  const renderDashboard = () => (
    <div className="view-section">
      <div className="dashboard-header">
        <h2>Executive Overview</h2>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          {availableYears.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <label htmlFor="reportYear" style={{ fontWeight: '600', color: '#475569' }}>
                Report Year:
              </label>
              <select
                id="reportYear"
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  border: '1px solid #cbd5e1',
                  backgroundColor: 'white',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                {availableYears.map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
          )}
          
          <button 
            onClick={exportSECRReport}
            disabled={loading || availableYears.length === 0}
            className="export-button"
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: availableYears.length === 0 ? '#94a3b8' : '#16a34a',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontWeight: '600',
              cursor: (loading || availableYears.length === 0) ? 'not-allowed' : 'pointer',
              fontSize: '0.95rem',
              whiteSpace: 'nowrap'
            }}
          >
            {loading ? '⏳ Generating...' : '📥 Export SECR Report'}
          </button>
        </div>
      </div>
      <div className="summary-cards">
        <div className="card highlight">
          <h3>Total Lifetime Emissions</h3>
          <div className="metric">{dashboardStats.totalEmissions.toLocaleString()} kgCO2e</div>
          <div className="subtext">{(dashboardStats.totalEmissions / 1000).toFixed(2)} tonnes CO2e</div>
        </div>
        <div className="card">
          <h3>Total Transactions Logged</h3>
          <div className="metric">{dashboardStats.totalTransactions}</div>
          <div className="subtext">Across all uploaded batches</div>
        </div>
      </div>
      
      {availableYears.length > 0 ? (
        <div style={{ 
          marginTop: '1rem', 
          padding: '0.75rem 1rem', 
          backgroundColor: '#f8fafc', 
          borderRadius: '8px',
          border: '1px solid #e2e8f0'
        }}>
          <p style={{ margin: 0, color: '#475569', fontSize: '0.9rem' }}>
            📊 Available data for years: {availableYears.join(', ')}
          </p>
        </div>
      ) : (
        <div style={{ 
          marginTop: '1rem', 
          padding: '0.75rem 1rem', 
          backgroundColor: '#fef3c7', 
          borderRadius: '8px',
          border: '1px solid #f59e0b'
        }}>
          <p style={{ margin: 0, color: '#92400e', fontSize: '0.9rem' }}>
            ⚠️ No emissions data found. Upload data to generate SECR reports.
          </p>
        </div>
      )}
      
      <div className="empty-state-chart">
        <p>💡 Tip: Go to <strong>Upload Data</strong> to process a new fuel card statement, or check <strong>History & Trends</strong> to see your month-over-month progress.</p>
      </div>
    </div>
  );

  const renderHistory = () => (
    <div className="view-section">
      <h2>📈 Emissions Trends & History</h2>
      {loadingHistory ? (
        <div className="loading-state">Loading...</div>
      ) : historyData.length === 0 ? (
        <div className="empty-state">No historical data found yet.</div>
      ) : (
        <>
          <div className="chart-section">
            <h3>Monthly Emissions Trend</h3>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" />
                <YAxis 
                  label={{ value: 'Tonnes CO2e', angle: -90, position: 'insideLeft' }} 
                  tickFormatter={(value) => `${value}t`} 
                />
                <Tooltip formatter={(value) => [`${value} tonnes CO2e`, 'Emissions']} />
                <Line type="monotone" dataKey="tonnes" stroke="#2563eb" strokeWidth={3} dot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="data-table">
            <h3>Recent Transaction History</h3>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Asset / Facility</th>
                  <th>Energy Source</th>
                  <th>Consumption</th>
                  <th>Emissions (kgCO2e)</th>
                  <th>DEFRA Factor</th>
                </tr>
              </thead>
              <tbody>
                {[...historyData].reverse().slice(0, 15).map((row, index) => {
                  const assetName = row.assets?.name || row.metadata?.asset_name || row.metadata?.vehicle_registration || 'N/A';
                  const fuelType = row.metadata?.fuel_type || row.defra_conversion_factors?.activity_type || 'N/A';
                  const defraFactor = row.defra_conversion_factors?.co2e_multiplier || row.metadata?.defra_factor_used || 'N/A';
                  
                  let unit = 'L';
                  if (fuelType === 'Electricity' || fuelType === 'Natural Gas') unit = 'kWh';
                  if (fuelType?.includes('Flight') || fuelType?.includes('Rail')) unit = 'passenger-km';
                  if (fuelType?.includes('Waste')) unit = 'kg';
                  if (fuelType === 'Hotel Stay') unit = 'nights';
                  
                  return (
                    <tr key={index}>
                      <td>{row.start_date}</td>
                      <td>{assetName}</td>
                      <td>{fuelType}</td>
                      <td>{row.raw_quantity} {unit}</td>
                      <td className="emission-cell">{parseFloat(row.calculated_kg_co2e).toFixed(2)}</td>
                      <td>{typeof defraFactor === 'number' ? defraFactor.toFixed(4) : defraFactor}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );

  // ============================================
  // MAIN RENDER
  // ============================================

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-top">
          <h1>🌱 CarbonTally</h1>
          <div className="user-menu">
            <span className="company-name">{organization?.name}</span>
            <button onClick={handleLogout} className="logout-button">Logout</button>
          </div>
        </div>
        
        <nav className="main-nav">
          <button 
            className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`} 
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Dashboard
          </button>
          <button 
            className={`nav-btn ${activeTab === 'upload' ? 'active' : ''}`} 
            onClick={() => setActiveTab('upload')}
          >
            ⬆️ Upload Data
          </button>
          <button 
            className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`} 
            onClick={() => { 
              setActiveTab('history'); 
              if (organization) 
                fetchHistory(); 
            }}
          >
            📈 History & Trends
          </button>
          {userRole === 'admin' && (
            <button 
              className={`nav-btn ${activeTab === 'team' ? 'active' : ''}`} 
              onClick={() => setActiveTab('team')}
            >
              👥 Team Management
            </button>
          )}
          <button 
            className={`nav-btn ${activeTab === 'assets' ? 'active' : ''}`} 
            onClick={() => setActiveTab('assets')}
          >
            🏢 Assets
          </button>
        </nav>
      </header>

      <div className="container">
        {activeTab === 'dashboard' && renderDashboard()}
        
        {showPDFPortal && pdfFile && (
          <PDFIngestionPortal
            file={pdfFile}
            dataType={uploadType}
            organizationId={organization?.id}
            onBack={() => {
              setShowPDFPortal(false);
              setPdfFile(null);
              setFile(null);
            }}
            onApprove={(data) => {
              console.log("Approved extraction:", data);
              toast.success("Data approved and saved!");
              setShowPDFPortal(false);
              setPdfFile(null);
              setFile(null);
              setActiveTab('history');
            }}
            onPurge={() => {
              toast.success("File discarded");
              setShowPDFPortal(false);
              setPdfFile(null);
              setFile(null);
            }}
          />
        )}
        
        {activeTab === 'upload' && !showPDFPortal && (
          <div className="view-section">
            {!showBulkUpload ? (
              <>
                {renderFileUpload()}
                {renderReviewQueue()}
                {organization?.id && <RecentProcessedData organizationId={organization.id} />}
              </>
            ) : (
              <BulkUpload 
                organizationId={organization?.id}
                onBack={() => setShowBulkUpload(false)}
              />
            )}
          </div>
        )}
        
        {activeTab === 'history' && renderHistory()}

        {activeTab === 'team' && (
          <TeamManagement organization={organization} userRole={userRole} />
        )}

        {activeTab === 'assets' && (
          <AssetManager organization={organization} />
        )}
      </div>
      
      {showOnboarding && onboardingChecked && (
        <OnboardingWizard
          userId={session?.user?.id}
          onComplete={() => {
            setShowOnboarding(false);
          }}
          onSkip={() => setShowOnboarding(false)}
        />
      )}
    </div>
  );
}

// ============================================
// MAIN APP
// ============================================

export default function App() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(() => {
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange(() => {
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }
  
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/cookies" element={<CookiePolicy />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/about" element={<AboutUs />} />
        <Route path="/carbon-reduction-plan" element={<CarbonReductionPlan />} />
        
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <DashboardLayout>
              <Dashboard />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      
      <CookieBanner />
    </BrowserRouter>
  );
}