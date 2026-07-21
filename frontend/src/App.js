import React, { useState, useEffect, useMemo } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { supabase } from './supabaseClient';
import Login from './Login';
import axios from 'axios';
import * as XLSX from 'xlsx';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './App.css';
import TeamManagement from './TeamManagement';
import AssetManager from './AssetManager';
import CookieBanner from './CookieBanner';
import PrivacyPolicy from './PrivacyPolicy';
import CookiePolicy from './CookiePolicy';
import TermsPage from './TermsPage';
import LandingPage from './LandingPage';
import CarbonReductionPlan from './CarbonReductionPlan';
import AboutUs from './AboutUs';
import BulkUpload from './BulkUpload';

const DEFRA_FACTORS = { 
  'Diesel': 2.54, 'Petrol': 2.16, 'AdBlue': 0.0, 'Unknown Fuel': 0.0,
  'Electricity': 0.20712, 'Natural Gas': 0.18316, 'Unknown Utility': 0.0,
  'Flight (Short Haul)': 0.155, 
  'Flight (Long Haul)': 0.195, 
  'Rail (National)': 0.035, 
  'Hotel Stay': 10.5, 
  'Mixed Waste': 0.500, 
  'Recycled Waste': -0.050, 
  'Unknown Scope 3': 0.0 
};

// Protected Route Component
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

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  if (!session) {
    return <Navigate to="/" replace />;
  }

  return children;
}

// Main Dashboard Component
function Dashboard() {
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [organization, setOrganization] = useState(null);
  
  // --- ALL YOUR EXISTING STATE VARIABLES ---
  const [activeTab, setActiveTab] = useState('dashboard');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [data, setData] = useState([]);
  const [error, setError] = useState('');
  const [dashboardStats, setDashboardStats] = useState({ totalEmissions: 0, totalTransactions: 0 });
  const [historyData, setHistoryData] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const [assets, setAssets] = useState([]);
  const [uploadType, setUploadType] = useState('fuel');
  const [facilities, setFacilities] = useState([]);
  
  // --- NEW STATE VARIABLES YOU ASKED ABOUT ---
  const [showLogin, setShowLogin] = useState(false);
  const [subscriptionTier, setSubscriptionTier] = useState('free');
  const [showPDFPortal, setShowPDFPortal] = useState(false);
  const [pdfFile, setPdfFile] = useState(null);
  const [showBulkUpload, setShowBulkUpload] = useState(false);
  
  // --- AUTH & ORG FETCHING ---
  useEffect(() => {
    const getOrgAndAssets = async (userId) => {
      const { data, error } = await supabase
        .from('organization_members')
        .select(`role, organization_id, organizations (id, name, company_number)`)
        .eq('user_id', userId).single();

      if (error) {
        console.error("Error fetching organization:", error);
      }

      if (data && data.organizations) {
        setOrganization(data.organizations);
        setUserRole(data.role);
        fetchDashboardStats(data.organizations.id);
        
        const { data: assetData } = await supabase.from('assets').select('id, name');
        if (assetData) setAssets(assetData);
      }
      
      const { data: facData, error: facError } = await supabase
          .from('facilities')
          .select('id, name');
        
      if (facError) {
        console.error("❌ Error fetching facilities:", facError);
      } else {
        console.log("✅ Facilities fetched:", facData);
        setFacilities(facData || []);
      }
    };

    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session) getOrgAndAssets(session.user.id);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session) getOrgAndAssets(session.user.id);
    });

    return () => subscription.unsubscribe();
  }, []);

  // --- DASHBOARD STATS ---
  const fetchDashboardStats = async (orgId) => {
    const { data, error } = await supabase
      .from('emissions_logs')
      .select('calculated_kg_co2e')
      .eq('organization_id', orgId);

    if (data && !error) {
      const total = data.reduce((sum, row) => sum + (parseFloat(row.calculated_kg_co2e) || 0), 0);
      setDashboardStats({
        totalEmissions: total,
        totalTransactions: data.length
      });
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setSession(null);
    setOrganization(null);
    setResult(null);
    setData([]);
    navigate('/');
  };

  // --- UPLOAD & REVIEW LOGIC ---
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
    setResult(null);
    setData([]);
  };

  const handleUpload = async () => {
    if (!file) return setError('Please select a file first');
    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('data_type', uploadType);

    try {
      const response = await axios.post('http://localhost:8000/upload-csv', formData, { 
        headers: { 'Content-Type': 'multipart/form-data' } 
      });
      setResult(response.data);
      setData(response.data.data);
    } catch (err) {
      setError('Error processing file: ' + (err.response?.data?.detail || err.message));
    } finally { 
      setLoading(false); 
    }
  };

  // --- YOUR EXISTING HANDLERS ---
  const handleInputChange = (index, field, value) => {
    const newData = [...data];
    const row = { ...newData[index] };
    row[field] = value;

    const dataType = result?.data_type || 'fuel';
    
    const fields = {
      fuel:    { type: 'Standardized Fuel',    volume: 'Volume (L)',         factor: 'DEFRA Factor (kgCO2e/L)',  site: 'Vehicle Registration' },
      utility: { type: 'Standardized Utility', volume: 'Consumption (kWh)',  factor: 'DEFRA Factor (kgCO2e/kWh)',site: 'Site Name' },
      scope3:  { type: 'Standardized Scope3',  volume: 'Quantity',           factor: 'DEFRA Factor',             site: 'Description' }
    };
    const currentFields = fields[dataType] || fields.fuel;

    if (field === currentFields.type) {
      row[currentFields.factor] = DEFRA_FACTORS[value] || 0;
    }

    const volume = parseFloat(row[currentFields.volume]);
    const factor = parseFloat(row[currentFields.factor]);
    
    if (!isNaN(volume) && !isNaN(factor)) {
      row['Total kgCO2e'] = parseFloat((volume * factor).toFixed(2));
    } else {
      row['Total kgCO2e'] = 0;
    }

    newData[index] = row;
    setData(newData);
  };

  const validateRow = (index) => {
    const newData = [...data];
    const row = { ...newData[index] };

    const dataType = result?.data_type || 'fuel';
    
    const fields = {
      fuel:    { type: 'Standardized Fuel',    volume: 'Volume (L)',         factor: 'DEFRA Factor (kgCO2e/L)',  site: 'Vehicle Registration' },
      utility: { type: 'Standardized Utility', volume: 'Consumption (kWh)',  factor: 'DEFRA Factor (kgCO2e/kWh)',site: 'Site Name' },
      scope3:  { type: 'Standardized Scope3',  volume: 'Quantity',           factor: 'DEFRA Factor',             site: 'Description' }
    };
    const currentFields = fields[dataType] || fields.fuel;

    const volume = parseFloat(row[currentFields.volume]);
    const factor = parseFloat(row[currentFields.factor]);
    const site = row[currentFields.site];

    const hasValidVolume = !isNaN(volume) && volume > 0;
    const hasValidType = row[currentFields.type] && !row[currentFields.type].toLowerCase().includes('unknown');
    const hasValidSite = site && site !== '' && site !== 'UNKNOWN' && site !== 'UNKNOWN_SITE';

    if (hasValidVolume && hasValidType && hasValidSite) {
      row['needs_review'] = false;
      row['review_reason'] = '';
      row['Total kgCO2e'] = parseFloat((volume * factor).toFixed(2));
    } else {
      row['needs_review'] = true;
      if (!hasValidVolume) row['review_reason'] = `Missing/Invalid ${currentFields.volume}`;
      else if (!hasValidType) row['review_reason'] = 'Unrecognized Category';
      else if (!hasValidSite) row['review_reason'] = `Missing ${currentFields.site}`;
    }

    newData[index] = row;
    setData(newData);
  };

  const flaggedData = data.filter(row => row.needs_review);
  const cleanData = data.filter(row => !row.needs_review);

  const handleSaveToDatabase = async () => {
    if (!organization || !session) {
      setError('You must be logged in to save data.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const dataType = result?.data_type || 'fuel';
      
      const fields = {
        fuel:    { type: 'Standardized Fuel',    volume: 'Volume (L)',         factor: 'DEFRA Factor (kgCO2e/L)',  site: 'Vehicle Registration', date: 'Transaction Date' },
        utility: { type: 'Standardized Utility', volume: 'Consumption (kWh)',  factor: 'DEFRA Factor (kgCO2e/kWh)',site: 'Site Name',              date: 'Billing Period Start' },
        scope3:  { type: 'Standardized Scope3',  volume: 'Quantity',           factor: 'DEFRA Factor',             site: 'Description',            date: 'Date' }
      };
      const currentFields = fields[dataType] || fields.fuel;

      const recordsToSave = cleanData.map(row => {
        const rawName = row[currentFields.site];
        const matchedAsset = assets.find(a => a.name.toUpperCase() === rawName?.toUpperCase());
        
        return {
          organization_id: organization.id,
          asset_id: matchedAsset ? matchedAsset.id : null,
          defra_factor_id: null, 
          start_date: row[currentFields.date], 
          end_date: row[currentFields.date],
          raw_quantity: parseFloat(row[currentFields.volume]) || 0,
          calculated_kg_co2e: parseFloat(row['Total kgCO2e']) || 0,
          created_by_user_id: session.user.id,
          metadata: {
            scope: dataType === 'scope3' ? 'Scope 3' : (dataType === 'utility' ? 'Scope 2' : 'Scope 1'),
            asset_name: rawName,
            fuel_type: row[currentFields.type],
            defra_factor_used: row[currentFields.factor],
            original_filename: result.filename,
            auto_mapped: matchedAsset ? true : false
          }
        };
      });

      console.log("🔍 ATTEMPTING TO SAVE THESE RECORDS:", recordsToSave);

      const { error } = await supabase
        .from('emissions_logs')
        .insert(recordsToSave);

      if (error) throw error;

      alert(`✅ Successfully saved ${cleanData.length} records!`);
      
      await fetchHistory(); 
      fetchDashboardStats(organization.id);
      setResult(null); 
      setData([]); 
      setFile(null); 
      setActiveTab('dashboard'); 

    } catch (err) {
      console.error("❌ Database Save Error:", err);
      setError('Failed to save: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // --- HISTORY & TRENDS ---
  const fetchHistory = async () => {
    if (!organization) {
      console.log("⏳ Waiting for organization data...");
      return; 
    }

    console.log("🚀 Fetching history for org:", organization.id);
    setLoadingHistory(true);
    
    const { data, error } = await supabase
      .from('emissions_logs')
      .select(`
        start_date, 
        raw_quantity, 
        calculated_kg_co2e, 
        metadata, 
        assets (
          name
        )
      `)
      .eq('organization_id', organization.id)
      .order('start_date', { ascending: true });
    
    if (error) {
      console.error("❌ History fetch error:", error);
      setLoadingHistory(false); 
    } else {
      console.log("✅ History fetched successfully:", data?.length, "records");
      setHistoryData(data || []);
      setLoadingHistory(false);
    }
  };

  const trendData = useMemo(() => {
    if (!historyData.length) return [];
    const grouped = {};
    historyData.forEach(row => {
      const month = row.start_date ? row.start_date.substring(0, 7) : 'Unknown';
      grouped[month] = (grouped[month] || 0) + (parseFloat(row.calculated_kg_co2e) || 0);
    });
    return Object.keys(grouped).sort().map(month => ({ month, tonnes: parseFloat((grouped[month] / 1000).toFixed(2)) }));
  }, [historyData]);

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

  // --- RENDER ---
  return (
    <div className="App">
      <header className="App-header">
        <div className="header-top">
          <h1>🌱 CarbonTally</h1>
          <div className="user-menu">
            <span className="company-name">{organization?.name}</span>
            <span className="subscription-badge">{subscriptionTier}</span>
            <button onClick={handleLogout} className="logout-button">Logout</button>
          </div>
        </div>
        
        <nav className="main-nav">
          <button className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>📊 Dashboard</button>
          <button className={`nav-btn ${activeTab === 'upload' ? 'active' : ''}`} onClick={() => setActiveTab('upload')}>📤 Upload Data</button>
          <button 
            className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`} 
            onClick={() => { 
              setActiveTab('history'); 
              if (organization) fetchHistory(); 
            }}
          >
            📈 History & Trends
          </button>
          {userRole === 'admin' && (
            <button className={`nav-btn ${activeTab === 'team' ? 'active' : ''}`} onClick={() => setActiveTab('team')}>
              👥 Team Management
            </button>
          )}
          <button className={`nav-btn ${activeTab === 'assets' ? 'active' : ''}`} onClick={() => setActiveTab('assets')}>🏢 Assets</button>
        </nav>
      </header>

      <div className="container">
        {/* DASHBOARD VIEW */}
        {activeTab === 'dashboard' && (
          <div className="view-section">
            <div className="dashboard-header">
              <h2>Executive Overview</h2>
              <button onClick={exportSECRReport} className="export-button">📥 Export SECR Report</button>
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
          </div>
        )}

        {/* UPLOAD & REVIEW VIEW */}
        {activeTab === 'upload' && (
          <div className="view-section">
            <div className="upload-section">
              <h2>Upload Data Statement</h2>
              
              <div className="upload-type-selector">
                <label className={`type-option ${uploadType === 'fuel' ? 'active' : ''}`}>
                  <input type="radio" name="uploadType" value="fuel" checked={uploadType === 'fuel'} onChange={() => setUploadType('fuel')} />
                  ⛽ Scope 1: Fuel Card (Litres)
                </label>
                <label className={`type-option ${uploadType === 'utility' ? 'active' : ''}`}>
                  <input type="radio" name="uploadType" value="utility" checked={uploadType === 'utility'} onChange={() => setUploadType('utility')} />
                  ⚡ Scope 2: Utility Bill (kWh)
                </label>
                <label className={`type-option ${uploadType === 'scope3' ? 'active' : ''}`}>
                  <input type="radio" name="uploadType" value="scope3" checked={uploadType === 'scope3'} onChange={() => setUploadType('scope3')} />
                  🌱 Scope 3: Travel & Waste
                </label>
              </div>

              <input type="file" accept=".csv,.xlsx" onChange={handleFileChange} className="file-input" />
              <button onClick={handleUpload} disabled={loading || !file} className="upload-button">
                {loading ? 'Processing...' : (
                  uploadType === 'fuel' ? 'Calculate Scope 1 Emissions' :
                  uploadType === 'utility' ? 'Calculate Scope 2 Emissions' :
                  'Calculate Scope 3 Emissions'
                )}
              </button>
              {error && <div className="error">{error}</div>}
            </div>

            {result && (
              <>
                <div className="tabs">
                  <button className={`tab-btn ${cleanData.length > 0 ? 'active' : ''}`}>Verified ({cleanData.length})</button>
                  <button className={`tab-btn ${flaggedData.length > 0 ? 'active' : ''}`}>Review Queue ({flaggedData.length})</button>
                </div>

                {flaggedData.length > 0 && (
                  <div className="review-section">
                    <h2>⚠️ Data Review Required</h2>
                    <table className="review-table">
                      <thead>
                        <tr>
                          <th>{result?.data_type === 'utility' ? 'Billing Period' : 'Date'}</th>
                          <th>{result?.data_type === 'utility' ? 'Site / Facility' : 'Vehicle'}</th>
                          <th>Issue</th>
                          <th>{result?.data_type === 'utility' ? 'Utility Type' : 'Fuel Type'}</th>
                          <th>{result?.data_type === 'utility' ? 'Consumption (kWh)' : 'Volume (L)'}</th>
                          <th>kgCO2e</th>
                        </tr>
                      </thead>
                      <tbody>
                        {flaggedData.map((row, index) => {
                          const dataIndex = data.indexOf(row);
                          const dataType = result?.data_type || 'fuel';
                          const fields = {
                            fuel:    { type: 'Standardized Fuel',    volume: 'Volume (L)',         factor: 'DEFRA Factor (kgCO2e/L)',  site: 'Vehicle Registration' },
                            utility: { type: 'Standardized Utility', volume: 'Consumption (kWh)',  factor: 'DEFRA Factor (kgCO2e/kWh)',site: 'Site Name' },
                            scope3:  { type: 'Standardized Scope3',  volume: 'Quantity',           factor: 'DEFRA Factor',             site: 'Description' }
                          };
                          const currentFields = fields[dataType] || fields.fuel;
                          const dateField = dataType === 'utility' ? 'Billing Period Start' : (dataType === 'scope3' ? 'Date' : 'Transaction Date');

                          return (
                            <tr key={dataIndex} className="flagged-row">
                              <td>{row[dateField] || 'N/A'}</td>
                              <td>
                                <input 
                                  type="text"
                                  value={row[currentFields.site] || ''} 
                                  onChange={(e) => handleInputChange(dataIndex, currentFields.site, e.target.value)}
                                  onBlur={() => validateRow(dataIndex)}
                                  className="edit-input"
                                  placeholder="Enter site/vehicle name"
                                />
                              </td>
                              <td className="error-cell">{row.review_reason}</td>
                              <td>
                                <select 
                                  value={row[currentFields.type] || ''} 
                                  onChange={(e) => handleInputChange(dataIndex, currentFields.type, e.target.value)}
                                  onBlur={() => validateRow(dataIndex)}
                                  className="edit-input"
                                >
                                  <option value="Unknown">Select Category...</option>
                                  {dataType === 'utility' ? (
                                    <>
                                      <option value="Electricity">Electricity</option>
                                      <option value="Natural Gas">Natural Gas</option>
                                    </>
                                  ) : dataType === 'scope3' ? (
                                    <>
                                      <option value="Flight (Short Haul)">Flight (Short Haul)</option>
                                      <option value="Flight (Long Haul)">Flight (Long Haul)</option>
                                      <option value="Rail (National)">Rail (National)</option>
                                      <option value="Hotel Stay">Hotel Stay</option>
                                      <option value="Mixed Waste">Mixed Waste</option>
                                      <option value="Recycled Waste">Recycled Waste</option>
                                    </>
                                  ) : (
                                    <>
                                      <option value="Diesel">Diesel</option>
                                      <option value="Petrol">Petrol</option>
                                      <option value="AdBlue">AdBlue</option>
                                    </>
                                  )}
                                </select>
                              </td>
                              <td>
                                <input 
                                  type="number" 
                                  step="0.01"
                                  value={row[currentFields.volume] === null ? '' : row[currentFields.volume]} 
                                  onChange={(e) => handleInputChange(dataIndex, currentFields.volume, e.target.value === '' ? null : parseFloat(e.target.value))}
                                  onBlur={() => validateRow(dataIndex)}
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
                  <button onClick={handleSaveToDatabase} disabled={loading || cleanData.length === 0} className="save-button">
                    💾 Save {cleanData.length} Verified Records to Database
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* HISTORY VIEW */}
        {activeTab === 'history' && (
          <div className="view-section">
            <h2>📈 Emissions Trends & History</h2>
            {loadingHistory ? <div className="loading-state">Loading...</div> : historyData.length === 0 ? 
              <div className="empty-state">No historical data found yet.</div> : (
              <>
                <div className="chart-section">
                  <h3>Monthly Emissions Trend</h3>
                  <ResponsiveContainer width="100%" height={350}>
                    <LineChart data={trendData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="month" />
                      <YAxis label={{ value: 'Tonnes CO2e', angle: -90, position: 'insideLeft' }} tickFormatter={(value) => `${value}t`} />
                      <Tooltip formatter={(value) => [`${value} tonnes CO2e`, 'Emissions']} />
                      <Line type="monotone" dataKey="tonnes" stroke="#2563eb" strokeWidth={3} dot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="data-table">
                  <h3>Recent Transaction History</h3>
                  <table>
                    <thead>
                      <tr><th>Date</th><th>Asset / Facility</th><th>Energy Source</th><th>Consumption</th><th>Emissions (kgCO2e)</th></tr>
                    </thead>
                    <tbody>
                      {[...historyData].reverse().slice(0, 15).map((row, index) => {
                        const assetName = row.assets?.name || row.metadata?.asset_name || row.metadata?.vehicle_registration || 'N/A';
                        const fuelType = row.metadata?.fuel_type || 'N/A';
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
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        )}

        {/* TEAM MANAGEMENT VIEW */}
        {activeTab === 'team' && (
          <TeamManagement organization={organization} userRole={userRole} />
        )}
        
        {/* ASSETS VIEW */}
        {activeTab === 'assets' && (
          <AssetManager organization={organization} />
        )}
      </div>
    </div>
  );
}

// Main App Component with Routing
export default function App() {
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

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/cookies" element={<CookiePolicy />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/about" element={<AboutUs />} />
        <Route path="/carbon-reduction-plan" element={<CarbonReductionPlan />} />
        
        {/* Protected Routes - Only accessible when logged in */}
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        
        {/* Redirect any unknown routes */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      
      {/* Cookie Banner - visible on all pages */}
      <CookieBanner />
    </BrowserRouter>
  );
}