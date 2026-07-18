import React, { useState, useEffect, useMemo } from 'react';
import { supabase } from './supabaseClient';
import Login from './Login';
import axios from 'axios';
import * as XLSX from 'xlsx';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './App.css';
import TeamManagement from './TeamManagement';
import AssetManager from './AssetManager';
import LandingPage from './LandingPage';

const DEFRA_FACTORS = { 
  // Scope 1
  'Diesel': 2.54, 'Petrol': 2.16, 'AdBlue': 0.0, 'Unknown Fuel': 0.0,
  // Scope 2
  'Electricity': 0.20712, 'Natural Gas': 0.18316, 'Unknown Utility': 0.0,
  // Scope 3 (Business Travel & Waste)
  'Flight (Short Haul)': 0.155, 
  'Flight (Long Haul)': 0.195, 
  'Rail (National)': 0.035, 
  'Hotel Stay': 10.5, 
  'Mixed Waste': 0.500, 
  'Recycled Waste': -0.050, 
  'Unknown Scope 3': 0.0 
};
// stripe.api_key = "sk_test_YOUR_SECRET_KEY_HERE" 
// FRONTEND_URL = "http://localhost:3000"

function App() {
  const [session, setSession] = useState(null);
  const [organization, setOrganization] = useState(null);
  
  // Navigation State
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Upload & Review State
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [data, setData] = useState([]);
  const [error, setError] = useState('');

  // Dashboard & History State
  const [dashboardStats, setDashboardStats] = useState({ totalEmissions: 0, totalTransactions: 0 });
  const [historyData, setHistoryData] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const [assets, setAssets] = useState([]);
  const [uploadType, setUploadType] = useState('fuel'); // 'fuel' or 'utility'
  const [facilities, setFacilities] = useState([]);
  const [showLogin, setShowLogin] = useState(false);
    const [subscriptionTier, setSubscriptionTier] = useState('free');
  // --- AUTH & ORG FETCHING ---
  useEffect(() => {
    const getOrgAndAssets = async (userId) => {
      const { data, error } = await supabase
        .from('organization_members')
        .select(`role, organization_id, organizations (id, name, company_number)`)
        .eq('user_id', userId).single();

      if (error) {
        console.error("Error fetching organization:", error); // <-- This uses the 'error' variable!
      }

      if (data && data.organizations) {
        setOrganization(data.organizations);
        setUserRole(data.role);
        fetchDashboardStats(data.organizations.id);
        
        const { data: assetData } = await supabase.from('assets').select('id, name');
        if (assetData) setAssets(assetData);
      }
              // --- ADD THIS TO FETCH FACILITIES ---
      const { data: facData, error: facError } = await supabase
          .from('facilities')
          .select('id, name');
        
        if (facError) {
          console.error("❌ Error fetching facilities:", facError);
        } else {
          console.log("✅ Facilities fetched:", facData); // Check F12 console to prove it's there!
          setFacilities(facData || []); // Ensures it's always an array, never null
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

  // --- DASHBOARD STATS (Fetches from DB so it survives reload) ---
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
      // Dynamically use the live API URL or fallback to localhost for local testing
      const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      
      const response = await axios.post(`${API_URL}/upload-csv`, formData, { 
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
  
    // 1. Runs on every keystroke (Updates math, but DOES NOT clear the error flag)
    // 1. Runs on every keystroke (Updates math, but DOES NOT clear the error flag)
  const handleInputChange = (index, field, value) => {
    const newData = [...data];
    const row = { ...newData[index] };
    row[field] = value;

    const dataType = result?.data_type || 'fuel';
    
    // Dynamically map field names based on upload type
    const fields = {
      fuel:    { type: 'Standardized Fuel',    volume: 'Volume (L)',         factor: 'DEFRA Factor (kgCO2e/L)',  site: 'Vehicle Registration' },
      utility: { type: 'Standardized Utility', volume: 'Consumption (kWh)',  factor: 'DEFRA Factor (kgCO2e/kWh)',site: 'Site Name' },
      scope3:  { type: 'Standardized Scope3',  volume: 'Quantity',           factor: 'DEFRA Factor',             site: 'Description' }
    };
    const currentFields = fields[dataType] || fields.fuel;

    // Update factor if they changed the type
    if (field === currentFields.type) {
      row[currentFields.factor] = DEFRA_FACTORS[value] || 0;
    }

    // Live math calculation
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

  // 2. Runs ONLY when the user clicks away (onBlur). This is what clears the error flag.
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

    // Strict validation rules
    const hasValidVolume = !isNaN(volume) && volume > 0;
    const hasValidType = row[currentFields.type] && !row[currentFields.type].toLowerCase().includes('unknown');
    
    // For Scope 3, 'N/A' is acceptable for description, but we still want to ensure it's not completely blank
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
  //const currentTotalEmissions = useMemo(() => data.reduce((sum, row) => sum + (parseFloat(row['Total kgCO2e']) || 0), 0).toFixed(2), [data]);
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
      
      // Unified field mapping for ALL 3 scopes
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
      
      // Refresh data and clean up
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

  // --- HISTORY & TRENDS LOGIC ---
  const fetchHistory = async () => {
    if (!organization) {
      console.log("⏳ Waiting for organization data to load before fetching history...");
      return; 
    }

    console.log("🚀 Fetching history for org:", organization.id);
    setLoadingHistory(true);
    
    // Explicitly join the assets table. RLS ensures we only get assets for THIS organization.
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
    // (Keep your existing export logic here, it works perfectly!)
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


    // 1. If no session AND we haven't clicked "Log In" yet, show the Landing Page
  if (!session && !showLogin) {
    return <LandingPage onGetStarted={() => setShowLogin(true)} />;
  }

  // 2. If no session BUT they clicked "Log In", show the Login component
  if (!session && showLogin) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <button 
          className="btn-secondary" 
          onClick={() => setShowLogin(false)} 
          style={{ marginBottom: '1rem' }}
        >
          Back to Home
        </button>
        <Login onLoginSuccess={() => setShowLogin(false)} />
      </div>
    );
  }

  // 3. If they ARE logged in, show the main App Dashboard
  return (
    <div className="App">
      <header className="App-header">
        <div className="header-top">
          <h1>CarbonTally</h1>
          <div className="user-menu">
            <span className="company-name">{organization?.name}</span>
            <button onClick={handleLogout} className="logout-button">Logout</button>
          </div>
        </div>
        
        <nav className="main-nav">
          <button className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>Dashboard</button>
          <button className={`nav-btn ${activeTab === 'upload' ? 'active' : ''}`} onClick={() => setActiveTab('upload')}>Upload Data</button>
          <button className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`} onClick={() => { setActiveTab('history'); if (organization) fetchHistory(); }}>History</button>
          
          {subscriptionTier === 'free' ? (
            <button className="nav-btn upgrade-btn" onClick={() => setActiveTab('billing')}>Upgrade to Pro</button>
          ) : (
            <button className={`nav-btn ${activeTab === 'upload_scope3' ? 'active' : ''}`} onClick={() => setActiveTab('upload_scope3')}>Scope 3</button>
          )}

          {userRole === 'admin' && <button className={`nav-btn ${activeTab === 'team' ? 'active' : ''}`} onClick={() => setActiveTab('team')}>Team</button>}
          {userRole === 'admin' && <button className={`nav-btn ${activeTab === 'assets' ? 'active' : ''}`} onClick={() => setActiveTab('assets')}>Assets</button>}
          {userRole === 'admin' && <button className={`nav-btn ${activeTab === 'billing' ? 'active' : ''}`} onClick={() => setActiveTab('billing')}>Billing</button>}
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
            <div className="empty-state-chart">
              <p> Tip: Go to <strong>Upload Data</strong> to process a new fuel card statement, or check <strong>History & Trends</strong> to see your month-over-month progress.</p>
            </div>
          </div>
        )}

        {/* UPLOAD & REVIEW VIEW */}
        {activeTab === 'upload' && (
          <div className="view-section">
            <div className="upload-section">
              <h2>Upload Data Statement</h2>
              
              {/* NEW: DATA TYPE SELECTOR */}
              <div className="upload-type-selector">
                <label className={`type-option ${uploadType === 'fuel' ? 'active' : ''}`}>
                  <input type="radio" name="uploadType" value="fuel" checked={uploadType === 'fuel'} onChange={() => setUploadType('fuel')} />
                  ⛽ Scope 1: Fuel Card (Litres)
                </label>
                <label className={`type-option ${uploadType === 'utility' ? 'active' : ''}`}>
                  <input type="radio" name="uploadType" value="utility" checked={uploadType === 'utility'} onChange={() => setUploadType('utility')} />
                   Scope 2: Utility Bill (kWh)
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
                          {flaggedData.map((row) => {
                            const dataIndex = data.indexOf(row);
                            const isUtility = result?.data_type === 'utility';
                            const isScope3 = result?.data_type === 'scope3';
                            
                            // Define fields safely INSIDE the map, BEFORE the return statement
                            const fields = {
                              fuel:    { type: 'Standardized Fuel',    volume: 'Volume (L)',         factor: 'DEFRA Factor (kgCO2e/L)',  site: 'Vehicle Registration', date: 'Transaction Date' },
                              utility: { type: 'Standardized Utility', volume: 'Consumption (kWh)',  factor: 'DEFRA Factor (kgCO2e/kWh)',site: 'Site Name',              date: 'Billing Period Start' },
                              scope3:  { type: 'Standardized Scope3',  volume: 'Quantity',           factor: 'DEFRA Factor',             site: 'Description',            date: 'Date' }
                            };
                            const currentFields = fields[result?.data_type || 'fuel'] || fields.fuel;

                            return (
                              <tr key={dataIndex} className="flagged-row">
                                {/* Column 1: Date */}
                                <td>{row[currentFields.date] || 'N/A'}</td>
                                
                                {/* Column 2: Site / Facility / Description */}
                                <td>
                                  <select 
                                    value={row[currentFields.site] === 'UNKNOWN_SITE' || row[currentFields.site] === 'UNKNOWN' || !row[currentFields.site] ? '' : row[currentFields.site]} 
                                    onChange={(e) => handleInputChange(dataIndex, currentFields.site, e.target.value)}
                                    onBlur={() => validateRow(dataIndex)}
                                    className="edit-input"
                                    style={{ marginBottom: '0.5rem', width: '100%' }}
                                  >
                                    <option value="">
                                      {isUtility ? 'Select Facility...' : isScope3 ? 'Select/Type Description...' : 'Select Vehicle...'}
                                    </option>
                                    {(isUtility ? facilities : assets).map(item => (
                                      <option key={item.id} value={item.name}>{item.name}</option>
                                    ))}
                                  </select>
                                  <input 
                                    type="text" 
                                    value={row[currentFields.site] === 'UNKNOWN_SITE' || row[currentFields.site] === 'UNKNOWN' || !row[currentFields.site] ? '' : row[currentFields.site]}
                                    onChange={(e) => handleInputChange(dataIndex, currentFields.site, e.target.value)}
                                    onBlur={() => validateRow(dataIndex)}
                                    className="edit-input"
                                    placeholder="Or type name manually..."
                                  />
                                </td>
                                
                                {/* Column 3: Issue */}
                                <td><span className="badge">{row['review_reason']}</span></td>
                                
                                {/* Column 4: Type Dropdown */}
                                <td>
                                  <select 
                                    value={row[currentFields.type]} 
                                    onChange={(e) => handleInputChange(dataIndex, currentFields.type, e.target.value)}
                                    onBlur={() => validateRow(dataIndex)}
                                    className="edit-input"
                                  >
                                    <option value="Unknown">Select Type...</option>
                                    {isUtility ? (
                                      <>
                                        <option value="Electricity">Electricity</option>
                                        <option value="Natural Gas">Natural Gas</option>
                                      </>
                                    ) : isScope3 ? (
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
                                
                                {/* Column 5: Volume Input */}
                                <td>
                                  <input 
                                    type="number" 
                                    step="0.01"
                                    value={row[currentFields.volume] === null || row[currentFields.volume] === undefined ? '' : row[currentFields.volume]} 
                                    onChange={(e) => handleInputChange(dataIndex, currentFields.volume, e.target.value === '' ? null : parseFloat(e.target.value))}
                                    onBlur={() => validateRow(dataIndex)}
                                    className="edit-input"
                                    placeholder={isUtility ? "e.g., 4500" : isScope3 ? "e.g., 1500" : "e.g., 45.2"}
                                  />
                                </td>
                                
                                {/* Column 6: Emissions */}
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
                     Save {cleanData.length} Verified Records to Database
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
                        // 1. Determine the Asset/Facility name safely
                        const assetName = row.assets?.name || row.metadata?.asset_name || row.metadata?.vehicle_registration || 'N/A';
                        
                        // 2. Determine the Energy Source (Fuel Type)
                        const fuelType = row.metadata?.fuel_type || 'N/A';
                        let unit = 'L';
                        if (fuelType === 'Electricity' || fuelType === 'Natural Gas') unit = 'kWh';
                        if (fuelType?.includes('Flight') || fuelType?.includes('Rail')) unit = 'passenger-km';
                        if (fuelType?.includes('Waste')) unit = 'kg';
                        if (fuelType === 'Hotel Stay') unit = 'nights';
                        
                       
                        return (
                          <tr key={index}>
                            {/* Column 1: Date */}
                            <td>{row.start_date}</td>
                            
                            {/* Column 2: Asset / Facility */}
                            <td>{assetName}</td>
                            
                            {/* Column 3: Energy Source (Diesel, Electricity, etc.) */}
                            <td>{fuelType}</td>
                            
                            {/* Column 4: Consumption */}
                            <td>{row.raw_quantity} {unit}</td>
                            
                            {/* Column 5: Emissions */}
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
        {activeTab === 'assets' && (
          <AssetManager organization={organization} />
        )}
      </div>
    </div>
  );
}

export default App;