import React, { useState, useEffect, useMemo } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, Link } from 'react-router-dom';
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
import RecentProcessedData from './RecentProcessedData';
import PDFIngestionPortal from './PDFIngestionPortal';
import toast from 'react-hot-toast';
import OnboardingWizard from './OnboardingWizard';
import MobileMenu from './components/MobileMenu';
import CompanyNamePrompt from './CompanyNamePrompt'; // We'll create this
import AuthCallback from './AuthCallback';

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

// Protected Route Component
function ProtectedRoute({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const getSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        setSession(session);
      } catch (error) {
        console.error('❌ Error getting session:', error);
      } finally {
        setLoading(false);
      }
    };

    getSession();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loader">Authenticating...</div>
      </div>
    );
  }
  
  if (!session) {
    // Redirect to login but preserve the intended URL
    return <Navigate to="/login" replace />;
  }
  
  return children;
}


function DashboardLayout({ children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {children}
      <footer className="footer-bottom-dashboard">
        <div className="footer-bottom-dashboard-content">
          <p>© {new Date().getFullYear()} CarbonTally (UK) Ltd. All rights reserved.</p>
          <div className="footer-legal-dashboard-links">
            <Link to="/privacy">Privacy Policy</Link>
            <Link to="/cookies">Cookie Policy</Link>
            <Link to="/terms">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Main Dashboard Component
function Dashboard() {
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);  

  // Toggle menu function with debug
  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  // Auth & Organization State
  const [session, setSession] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [showCompanyPrompt, setShowCompanyPrompt] = useState(false);
  const [isNewUser, setIsNewUser] = useState(false); // ✅ ADD THIS LINE

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
  // eslint-disable-next-line no-unused-vars
  const [facilities, setFacilities] = useState([]);

    // Year selector state
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [reportDropdownOpen, setReportDropdownOpen] = useState(false);

  useEffect(() => {
    const checkUserStatus = async () => {
      try {
        setLoading(true);
        const { data: { user } } = await supabase.auth.getUser();
        
        if (user) {
          console.log('👤 Checking user status:', user.email);
          
          // Check if this is a new user
          const isNew = user.created_at === user.last_sign_at;
          setIsNewUser(isNew);
          
          // Check if user has company_name
          const hasCompany = user.user_metadata?.company_name;
          
          if (!hasCompany) {
            // New user or user without company
            console.log('📝 User needs company setup');
            setShowCompanyPrompt(true);
          } else {
            // Existing user with company
            console.log('✅ User has company setup');
            setShowCompanyPrompt(false);
            await fetchOrgAndAssets(user.id);
          }
        }
      } catch (error) {
        console.error('❌ Error checking user status:', error);
      } finally {
        setLoading(false);
      }
    };
    
    checkUserStatus();
  }, []);


  const fetchOrgAndAssets = async (userId) => {
    try {
      console.log('🔍 Fetching organization and assets for user:', userId);
      
      // Fetch organization membership
      const { data: orgData, error: orgError } = await supabase
        .from('organization_members')
        .select(`
          role, 
          organization_id, 
          organizations (
            id, 
            name, 
            company_number,
            created_at,
            settings
          )
        `)
        .eq('user_id', userId)
        .single();

      if (orgError) {
        if (orgError.code === 'PGRST116') {
          // No organization found, check user metadata
          const { data: { user } } = await supabase.auth.getUser();
          if (user?.user_metadata?.company_name) {
            console.log('📝 User has company_name in metadata, creating organization...');
            await createOrganizationFromMetadata(user);
            return;
          }
          // No organization at all, show company prompt
          setShowCompanyPrompt(true);
          return;
        }
        throw orgError;
      }

      if (orgData?.organizations) {
        setOrganization(orgData.organizations);
        setUserRole(orgData.role);
        
        // Fetch dashboard stats
        await fetchDashboardStats(orgData.organizations.id);
        
        // Fetch assets
        await fetchAssets(orgData.organizations.id);
        
        // Fetch facilities
        const { data: facData, error: facError } = await supabase
          .from('facilities')
          .select('id, name, address, facility_type')
          .eq('organization_id', orgData.organizations.id);
        
        if (facError) {
          console.error('❌ Error fetching facilities:', facError);
        } else {
          setFacilities(facData || []);
        }
      }
    } catch (error) {
      console.error('❌ Error in fetchOrgAndAssets:', error);
    }
  };
const createOrganizationFromMetadata = async (user) => {
  try {
    const companyName = user.user_metadata.company_name;
    
    console.log('🏢 Creating organization from metadata:', companyName);
    
    // Create organization
    const { data: org, error: orgError } = await supabase
      .from('organizations')
      .insert({
        name: companyName,
        created_by: user.id,
        created_at: new Date().toISOString(),
        settings: {
          currency: 'GBP',
          country: 'UK'
        }
      })
      .select()
      .single();

    if (orgError) throw orgError;

    // Add user as admin member
    const { error: memberError } = await supabase
      .from('organization_members')
      .insert({
        organization_id: org.id,
        user_id: user.id,
        role: 'admin',
        joined_at: new Date().toISOString()
      });

    if (memberError) throw memberError;

    // Update user metadata with organization_id
    await supabase.auth.updateUser({
      data: { 
        organization_id: org.id,
        organization_name: org.name
      }
    });

    setOrganization(org);
    setUserRole('admin');
    setShowCompanyPrompt(false);
    
    console.log('✅ Organization created from metadata:', org.name);
    
    // Fetch assets for the new organization
    await fetchAssets(org.id);
    
    toast.success(`✅ Welcome ${org.name}!`);
    
  } catch (error) {
    console.error('❌ Error creating organization from metadata:', error);
    toast.error('Failed to create organization');
  }
};

  useEffect(() => {
    const handleNewUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      
      if (user) {
        // Check if this is a new Google user
        const isNewUser = user.created_at === user.last_sign_in_at;
        const provider = user.app_metadata?.provider || user.identities?.[0]?.provider;
        
        if (isNewUser && provider === 'google') {
          // This is a new user who signed up with Google
          console.log('🆕 New Google user registered:', user.email);
          
          // Check if they have company_name
          if (!user.user_metadata?.company_name) {
            setShowCompanyPrompt(true);
          }
        }
      }
    };
    
    handleNewUser();
  }, []);

  // Check if onboarding is needed
  useEffect(() => {
    const checkOnboarding = async () => {
      // Wait until we have the organization data
      if (!organization) {
        setOnboardingChecked(true);
        return;
      }

      console.log('🏢 Checking onboarding for organization:', organization.id);

      // Check if this organization has any facilities yet
      const { data: facilities, error } = await supabase
        .from('facilities')
        .select('id')
        .eq('organization_id', organization.id)
        .limit(1);

      if (error) {
        console.error('Error checking facilities:', error);
        setOnboardingChecked(true);
        return;
      }

      // If no facilities exist, trigger the onboarding wizard
      if (!facilities || facilities.length === 0) {
        console.log('🚀 No facilities found - showing onboarding');
        setShowOnboarding(true);
      } else {
        console.log('✅ Facilities found - skipping onboarding');
        setShowOnboarding(false);
      }

      setOnboardingChecked(true);
    };

    checkOnboarding();
  }, [organization]); // This will trigger when organization is set

  
  const handleSaveCompanyName = async (orgData) => {
    try {
      console.log('💾 Saving company for new user:', orgData.name);
      setLoading(true);
      
      const { data: { user } } = await supabase.auth.getUser();
      
      // 1. Update user metadata with company name
      const { data: updatedUser, error: updateError } = await supabase.auth.updateUser({
        data: { 
          company_name: orgData.name,
          organization_name: orgData.name,
          is_onboarded: false,
          onboarded_at: null
        }
      });
      
      if (updateError) throw updateError;
      
      // 2. Create organization
      const { data: org, error: orgError } = await supabase
        .from('organizations')
        .insert({
          name: orgData.name,
          created_by: user.id,
          created_at: new Date().toISOString(),
          settings: {
            currency: 'GBP',
            country: 'UK',
            reporting_start_date: new Date().toISOString()
          }
        })
        .select()
        .single();
        
      if (orgError) {
        if (orgError.code === '23505') {
          // Organization already exists, try to fetch it
          const { data: existingOrg } = await supabase
            .from('organizations')
            .select('*')
            .eq('name', orgData.name)
            .single();
            
          if (existingOrg) {
            setOrganization(existingOrg);
            setShowCompanyPrompt(false);
            toast.success('✅ Organization found!');
            setLoading(false);
            return;
          }
        }
        throw orgError;
      }
      
      // 3. Add user as admin member
      const { error: memberError } = await supabase
        .from('organization_members')
        .insert({
          organization_id: org.id,
          user_id: user.id,
          role: 'admin',
          joined_at: new Date().toISOString()
        });
      
      if (memberError) throw memberError;
      
      // 4. Update user metadata with organization_id
      await supabase.auth.updateUser({
        data: { 
          organization_id: org.id,
        }
      });
      
      // 5. Set state
      setOrganization(org);
      setUserRole('admin');
      setShowCompanyPrompt(false);
      setIsNewUser(false);
      
      console.log('✅ Company setup complete for:', orgData.name);
      toast.success(`🎉 Welcome ${orgData.name}! Let's set up your first facility.`);
      
      // 6. Fetch initial data
      await fetchDashboardStats(org.id);
      await fetchAssets(org.id);
      
      // 7. Check if onboarding is needed (will trigger via useEffect)
      
    } catch (error) {
      console.error('❌ Error saving company:', error);
      toast.error('❌ Failed to save company. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOnboardingComplete = async () => {
    try {
      // Update user metadata to mark onboarding as complete
      const { data: { user } } = await supabase.auth.getUser();
      await supabase.auth.updateUser({
        data: { 
          is_onboarded: true,
          onboarded_at: new Date().toISOString()
        }
      });
      
      setShowOnboarding(false);
      toast.success('🎉 Onboarding complete! You\'re ready to go.');
      
      // Refresh dashboard data
      if (organization) {
        await fetchDashboardStats(organization.id);
        await fetchAssets(organization.id);
        await fetchHistory();
      }
    } catch (error) {
      console.error('Error completing onboarding:', error);
      toast.error('Failed to complete onboarding');
    }
  };
  const fetchAssets = async (orgId) => {
    try {
      console.log('📦 Fetching assets for organization:', orgId);
      
      const { data, error } = await supabase
        .from('assets')
        .select(`
          id,
          name,
          type,
          description,
          facility_id,
          facilities (
            id,
            name
          )
        `)
        .eq('organization_id', orgId)
        .order('name', { ascending: true });

      if (error) throw error;
      
      setAssets(data || []);
      console.log(`✅ Found ${data?.length || 0} assets`);
      
      return data;
    } catch (error) {
      console.error('❌ Error fetching assets:', error);
      setAssets([]);
      return [];
    }
  };

  useEffect(() => {
    const checkUserOrganization = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      
      if (user) {
        // Check if user has company_name in metadata
        const hasCompanyName = user.user_metadata?.company_name;
        
        // Check if user has organization in organizations table
        if (!hasCompanyName) {
          // Show company name prompt for new Google users
          setShowCompanyPrompt(true);
        } else {
          // User already has organization
          setShowCompanyPrompt(false);
          // Fetch organization details
          await fetchOrgAndAssets(user.id);
        }
      }
    };
    
    checkUserOrganization();
  }, []);
  

  // Computed Data
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

  // Update clean/flagged data when data changes
  useEffect(() => {
    const flagged = data.filter(row => row.needs_review);
    const clean = data.filter(row => !row.needs_review);
    setFlaggedData(flagged);
    setCleanData(clean);
  }, [data]);

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (user && !user.user_metadata.company_name) {
        // Prompt user to add company name
        setShowCompanyPrompt(true);
      }
    };
    getUser();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (reportDropdownOpen && !event.target.closest('.dashboard-header')) {
        setReportDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [reportDropdownOpen]);

  // Fetch organization and assets on mount
  useEffect(() => {
    const fetchOrgAndAssets = async (userId) => {
      try {
        // Fetch organization
        const { data: orgData, error: orgError } = await supabase
          .from('organization_members')
          .select(`role, organization_id, organizations (id, name, company_number)`)
          .eq('user_id', userId)
          .single();

        if (orgError) throw orgError;

        if (orgData?.organizations) {
          setOrganization(orgData.organizations);
          setUserRole(orgData.role);
          await fetchDashboardStats(orgData.organizations.id);
          
          // Fetch assets
          const { data: assetData } = await supabase
            .from('assets')
            .select('id, name');
          if (assetData) setAssets(assetData);
        }

        // Fetch facilities
        const { data: facData, error: facError } = await supabase
          .from('facilities')
          .select('id, name');
        
        if (facError) {
          console.error("Error fetching facilities:", facError);
        } else {
          setFacilities(facData || []);
        }
      } catch (error) {
        console.error("Error fetching organization:", error);
      }
    };

    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session) fetchOrgAndAssets(session.user.id);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session) fetchOrgAndAssets(session.user.id);
    });

    return () => subscription.unsubscribe();
  }, []);

  

  // --- Data Fetching Functions ---
  const fetchDashboardStats = async (orgId) => {
    // First, get the total count
    const { count, error: countError } = await supabase
      .from('emissions_logs')
      .select('*', { count: 'exact', head: true })
      .eq('organization_id', orgId);
    
    if (countError) {
      console.error("❌ Count error:", countError);
      return;
    }
    
    console.log(`📊 Total records in database: ${count}`);
    
    // Now get all emissions data for the total
    let allData = [];
    let hasMore = true;
    let page = 0;
    const pageSize = 1000;
    
    while (hasMore) {
      const start = page * pageSize;
      const end = (page + 1) * pageSize - 1;
      
      const { data, error } = await supabase
        .from('emissions_logs')
        .select('calculated_kg_co2e')
        .eq('organization_id', orgId)
        .range(start, end);
      
      if (error) {
        console.error("❌ Fetch error:", error);
        break;
      }
      
      if (data && data.length > 0) {
        allData = [...allData, ...data];
        page++;
      }
      
      if (!data || data.length < pageSize) {
        hasMore = false;
      }
    }
    
    const total = allData.reduce((sum, row) => sum + (parseFloat(row.calculated_kg_co2e) || 0), 0);
    setDashboardStats({
      totalEmissions: total,
      totalTransactions: allData.length // Use the actual count from fetched data
    });
    
    console.log(`📊 Dashboard stats: ${allData.length} transactions, ${total} kgCO2e`);
  };

  useEffect(() => {
    if (organization) {
      console.log("📊 Organization loaded, fetching history...");
      fetchHistory();
    }
  }, [organization]); // Runs when organization is set

  const availableYears = useMemo(() => {
    console.log("🔄 Computing available years from historyData:", historyData?.length || 0, "records");
    
    if (!historyData || historyData.length === 0) {
      console.log("⚠️ No history data available");
      return [];
    }
    
    const years = new Set();
    historyData.forEach(row => {
      if (row.start_date) {
        // Handle both string and date objects
        let yearStr;
        if (typeof row.start_date === 'string') {
          yearStr = row.start_date.substring(0, 4);
        } else if (row.start_date instanceof Date) {
          yearStr = row.start_date.getFullYear().toString();
        }
        
        if (yearStr) {
          const year = parseInt(yearStr);
          if (!isNaN(year) && year > 2000) {
            years.add(year);
          }
        }
      }
    });
    
    const sortedYears = Array.from(years).sort((a, b) => b - a);
    console.log("📊 Available years from history:", sortedYears);
    return sortedYears;
  }, [historyData]);



  // Also update the selectedYear useEffect
  useEffect(() => {
    if (availableYears.length > 0) {
      // If current selected year is not in available years, use the first one
      if (!availableYears.includes(selectedYear)) {
        setSelectedYear(availableYears[0]);
      }
    }
  }, [availableYears]);
    // 👇 AUTO-SELECT MOST RECENT YEAR
  useEffect(() => {
    if (availableYears.length > 0 && !availableYears.includes(selectedYear)) {
      setSelectedYear(availableYears[0]);
    }
  }, [availableYears, selectedYear]);


  const fetchHistory = async () => {
    if (!organization) {
      console.log("⏳ Waiting for organization data to load before fetching history...");
      return; 
    }

    console.log("🚀 Fetching history for org:", organization.id);
    setLoadingHistory(true);
    
    try {
      let allData = [];
      let hasMore = true;
      let page = 0;
      const pageSize = 1000;
      
      while (hasMore) {
        const start = page * pageSize;
        const end = (page + 1) * pageSize - 1;
        
        console.log(`📄 Fetching page ${page + 1} (rows ${start} to ${end})...`);
        
        const { data, error, count } = await supabase
          .from('emissions_logs')
          .select(`
            start_date, 
            raw_quantity, 
            calculated_kg_co2e, 
            metadata,
            asset_id,
            defra_factor_id,
            assets (
              id,
              name
            ),
            defra_conversion_factors (
              id,
              activity_type,
              co2e_multiplier,
              reporting_year
            )
          `, { count: 'exact' })
          .eq('organization_id', organization.id)
          .order('start_date', { ascending: true })
          .range(start, end);
        
        if (error) {
          console.error("❌ History fetch error:", error);
          break;
        }
        
        if (data && data.length > 0) {
          allData = [...allData, ...data];
          console.log(`✅ Page ${page + 1}: ${data.length} records (total so far: ${allData.length})`);
          page++;
        }
        
        // If we got less than pageSize, we've reached the end
        if (!data || data.length < pageSize) {
          hasMore = false;
        }
      }
      
      console.log("✅ History fetched successfully:", allData?.length, "records total");
      
      if (allData && allData.length > 0) {
        // Log all distinct years found
        const years = new Set();
        const yearCounts = {};
        
        allData.forEach(row => {
          if (row.start_date) {
            const year = typeof row.start_date === 'string' 
              ? row.start_date.substring(0, 4) 
              : row.start_date.getFullYear().toString();
            years.add(year);
            yearCounts[year] = (yearCounts[year] || 0) + 1;
          }
        });
        
        console.log("📊 Years found in data:", Array.from(years).sort());
        console.log("📊 Records by year:", yearCounts);
      }
      
      setHistoryData(allData || []);
      setLoadingHistory(false);
      
    } catch (err) {
      console.error("❌ Error fetching history:", err);
      setLoadingHistory(false);
    }
  };
  // --- File Upload Functions ---
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    // Detect if it's a PDF or Image
    const isPDF = selectedFile.type === 'application/pdf' || selectedFile.name.toLowerCase().endsWith('.pdf');
    const isImage = selectedFile.type.startsWith('image/');

    if (isPDF || isImage) {
      // 🚀 Route to PDF/Image Portal
      setPdfFile(selectedFile);
      setShowPDFPortal(true);
      setFile(null); // Clear CSV file state
      setError('');
    } else {
      // 📊 Route to CSV/Excel Parser
      setFile(selectedFile);
      setPdfFile(null); // Clear PDF file state
      setShowPDFPortal(false);
      setError('');
    }
  };

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

  // --- Data Processing Functions ---
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

    // Auto-populate factor when type changes
    if (field === fieldConfig.type) {
      row[fieldConfig.factor] = DEFRA_FACTORS[value] || 0;
    }

    // Recalculate emissions
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
    // eslint-disable-next-line no-unused-vars
    const factor = parseFloat(row[fieldConfig.factor]);
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

      const recordsToSave = cleanData.map(row => {
        const rawName = row[fieldConfig.site];
        const matchedAsset = assets.find(a => a.name.toUpperCase() === rawName?.toUpperCase());
        
        return {
          organization_id: organization.id,
          asset_id: matchedAsset ? matchedAsset.id : null,
          defra_factor_id: null, 
          start_date: row[fieldConfig.date], 
          end_date: row[fieldConfig.date],
          raw_quantity: parseFloat(row[fieldConfig.volume]) || 0,
          calculated_kg_co2e: parseFloat(row['Total kgCO2e']) || 0,
          created_by_user_id: session.user.id,
          metadata: {
            scope: dataType === 'scope3' ? 'Scope 3' : (dataType === 'utility' ? 'Scope 2' : 'Scope 1'),
            asset_name: rawName,
            fuel_type: row[fieldConfig.type],
            defra_factor_used: row[fieldConfig.factor],
            original_filename: result.filename,
            auto_mapped: !!matchedAsset
          }
        };
      });

      const { error: saveError } = await supabase
        .from('emissions_logs')
        .insert(recordsToSave);

      if (saveError) throw saveError;

      toast.success(`✅ Successfully saved ${cleanData.length} records!`);
      
      await fetchHistory();
      await fetchDashboardStats(organization.id);
      
      // Reset upload state
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

  // --- Export Functions ---
  // eslint-disable-next-line no-unused-vars
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

  // --- Render Functions ---
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
      
      {/* DATA TYPE SELECTOR */}
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

      {/* UNIFIED DRAG & DROP ZONE */}
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
        
        {/* Hidden file input */}
        <input
          id="singleFileInput"
          type="file"
          accept=".csv,.xlsx,.pdf,.jpg,.jpeg,.png"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </div>

      {/* CLEAR FILE BUTTON */}
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
    {/* Welcome Banner for New Users */}
    {isNewUser && !showCompanyPrompt && !showOnboarding && (
      <div style={{
        background: 'linear-gradient(135deg, #10b981, #059669)',
        borderRadius: '12px',
        padding: '1.5rem 2rem',
        marginBottom: '2rem',
        color: 'white',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.25rem' }}>
            👋 Welcome to CarbonTally, {organization?.name || 'New User'}!
          </h3>
          <p style={{ margin: 0, opacity: 0.9, fontSize: '0.95rem' }}>
            Start tracking your carbon emissions by uploading your first data file.
          </p>
        </div>
        <button
          onClick={() => setActiveTab('upload')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: 'white',
            color: '#059669',
            border: 'none',
            borderRadius: '8px',
            fontWeight: '600',
            cursor: 'pointer',
            fontSize: '0.95rem',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            transition: 'transform 0.2s'
          }}
          onMouseEnter={(e) => e.target.style.transform = 'scale(1.05)'}
          onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
        >
          ⬆️ Upload Your First File
        </button>
      </div>
    )}

    {/* Onboarding Progress Card (shown during onboarding) */}
    {showOnboarding && (
      <div style={{
        backgroundColor: '#fef3c7',
        border: '1px solid #f59e0b',
        borderRadius: '12px',
        padding: '1rem 1.5rem',
        marginBottom: '1.5rem',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        flexWrap: 'wrap'
      }}>
        <span style={{ fontSize: '1.5rem' }}>🚀</span>
        <div style={{ flex: 1 }}>
          <p style={{ margin: 0, fontWeight: '600', color: '#92400e' }}>
            Complete your setup to get started!
          </p>
          <p style={{ margin: 0, fontSize: '0.9rem', color: '#78350f' }}>
            Add your first facility and asset to begin tracking emissions.
          </p>
        </div>
        <button
          onClick={() => setShowOnboarding(true)}
          style={{
            padding: '0.5rem 1.25rem',
            backgroundColor: '#f59e0b',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          Continue Setup →
        </button>
      </div>
    )}

    {/* Dashboard Header */}
    <div className="dashboard-header">
      <div>
        <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          Executive Overview
          {organization && (
            <span style={{
              fontSize: '0.8rem',
              backgroundColor: '#dbeafe',
              color: '#1e40af',
              padding: '0.25rem 0.75rem',
              borderRadius: '12px',
              fontWeight: '500'
            }}>
              {organization.name}
            </span>
          )}
        </h2>
        {historyData.length > 0 && (
          <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.9rem' }}>
            {historyData.length} total records • Last updated: {new Date().toLocaleDateString()}
          </p>
        )}
      </div>
      
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        {/* 1. SMART YEAR SELECTOR */}
        {availableYears.length > 0 ? (
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            style={{
              padding: '0.75rem 1rem',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              fontSize: '0.95rem',
              fontWeight: '600',
              cursor: 'pointer',
              backgroundColor: 'white',
              color: '#0f172a'
            }}
          >
            {availableYears.map((year) => (
              <option key={year} value={year}>
                {year} {year === availableYears[0] ? '(Latest)' : ''}
              </option>
            ))}
          </select>
        ) : (
          <div style={{ padding: '0.75rem 1rem', color: '#64748b', fontSize: '0.95rem' }}>
            No data available yet
          </div>
        )}
        
        {/* 2. REPORT GENERATION DROPDOWN */}
        <div style={{ position: 'relative' }}>
          <button 
            onClick={() => setReportDropdownOpen(!reportDropdownOpen)}
            disabled={loading || availableYears.length === 0}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: availableYears.length > 0 ? '#16a34a' : '#94a3b8',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontWeight: '600',
              cursor: loading || availableYears.length === 0 ? 'not-allowed' : 'pointer',
              fontSize: '0.95rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            {loading ? '⏳ Generating...' : '📥 Generate Reports'}
            <span style={{ fontSize: '0.8rem' }}>▼</span>
          </button>

          {/* Dropdown Menu */}
          {reportDropdownOpen && (
            <div style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: '0.5rem',
              backgroundColor: 'white',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              zIndex: 100,
              minWidth: '280px',
              overflow: 'hidden'
            }}>
              <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid #f1f5f9', backgroundColor: '#f8fafc' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase' }}>
                  Generate Report for {selectedYear}
                </span>
              </div>
              
              {[
                { type: 'SECR', label: '🇬🇧 SECR Compliance Report (PDF)', desc: 'UK Streamlined Energy & Carbon Reporting' },
                { type: 'CSRD', label: '🇪🇺 CSRD / ESRS Report (PDF)', desc: 'EU Corporate Sustainability Reporting' },
                { type: 'ISSB', label: '🌍 ISSB / IFRS S2 Report (PDF)', desc: 'International Climate Disclosures' },
                { type: 'AUDITOR_EXCEL', label: '📊 Auditor Data Export (Excel)', desc: 'Granular GHG Protocol mapping for Big 4' }
              ].map((report) => (
                <button
                  key={report.type}
                  onClick={async () => {
                    setReportDropdownOpen(false);
                    setLoading(true);
                    try {
                      const response = await fetch(`${process.env.REACT_APP_API_URL}/generate-sustainability-report`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                          organization_id: organization.id,
                          reporting_year: selectedYear,
                          report_type: report.type
                        })
                      });
                      
                      const result = await response.json();
                      
                      if (result.status === 'success') {
                        const isExcel = report.type === 'AUDITOR_EXCEL';
                        const mimeType = isExcel 
                          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
                          : 'application/pdf';
                        
                        const binaryString = window.atob(isExcel ? result.file_base64 : result.pdf_base64);
                        const bytes = new Uint8Array(binaryString.length);
                        for (let i = 0; i < binaryString.length; i++) {
                          bytes[i] = binaryString.charCodeAt(i);
                        }
                        
                        const blob = new Blob([bytes], { type: mimeType });
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = result.filename;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        
                        toast.success(`${report.type} Report for ${selectedYear} downloaded!`);
                      } else {
                        toast.error(result.detail || 'Failed to generate report');
                      }
                    } catch (error) {
                      console.error('Report generation error:', error);
                      toast.error('Failed to generate report');
                    } finally {
                      setLoading(false);
                    }
                  }}
                  style={{
                    width: '100%',
                    padding: '0.85rem 1rem',
                    backgroundColor: 'white',
                    border: 'none',
                    borderBottom: '1px solid #f1f5f9',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f8fafc'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
                >
                  <div style={{ fontWeight: '600', color: '#0f172a', fontSize: '0.95rem', marginBottom: '0.2rem' }}>
                    {report.label}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    {report.desc}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>

    {/* Summary Cards */}
    <div className="summary-cards">
      <div className="card highlight">
        <h3>Total Lifetime Emissions</h3>
        <div className="metric">{dashboardStats.totalEmissions.toLocaleString()} kgCO2e</div>
        <div className="subtext">{(dashboardStats.totalEmissions / 1000).toFixed(2)} tonnes CO2e</div>
        {historyData.length === 0 && (
          <div style={{ 
            marginTop: '0.5rem',
            fontSize: '0.8rem',
            color: '#94a3b8'
          }}>
            No data uploaded yet
          </div>
        )}
      </div>
      <div className="card">
        <h3>Total Transactions Logged</h3>
        <div className="metric">{dashboardStats.totalTransactions}</div>
        <div className="subtext">Across all uploaded batches</div>
        {dashboardStats.totalTransactions === 0 && (
          <button
            onClick={() => setActiveTab('upload')}
            style={{
              marginTop: '0.75rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#16a34a',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              fontWeight: '500'
            }}
          >
            Upload your first file
          </button>
        )}
      </div>
    </div>
    
    {/* Show available years or a message */}
    {availableYears.length > 0 ? (
      <div style={{ 
        marginTop: '1rem', 
        padding: '0.75rem 1rem', 
        backgroundColor: '#f0fdf4', 
        borderRadius: '8px',
        border: '1px solid #bbf7d0'
      }}>
        <p style={{ margin: 0, color: '#166534', fontSize: '0.9rem' }}>
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
          ⚠️ No emissions data found. 
          {dashboardStats.totalTransactions > 0 ? ' Data exists but years not detected.' : ' Please upload data to generate SECR reports.'}
        </p>
      </div>
    )}
    
    {/* Quick Action Cards for New Users */}
    {historyData.length === 0 && !showOnboarding && (
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem',
        marginTop: '1.5rem'
      }}>
        <div style={{
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '12px',
          padding: '1.5rem',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
        onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
        onClick={() => setActiveTab('upload')}
        >
          <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📄</div>
          <h4 style={{ margin: '0 0 0.25rem 0', color: '#0f172a' }}>Upload Data</h4>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>
            Upload your first fuel or utility statement
          </p>
        </div>

        <div style={{
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '12px',
          padding: '1.5rem',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
        onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
        onClick={() => setActiveTab('assets')}
        >
          <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🏢</div>
          <h4 style={{ margin: '0 0 0.25rem 0', color: '#0f172a' }}>Manage Assets</h4>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>
            Add vehicles, meters, and equipment
          </p>
        </div>

        <div style={{
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '12px',
          padding: '1.5rem',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
        onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
        onClick={() => setActiveTab('team')}
        >
          <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>👥</div>
          <h4 style={{ margin: '0 0 0.25rem 0', color: '#0f172a' }}>Invite Team</h4>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>
            Collaborate with your colleagues
          </p>
        </div>
      </div>
    )}

    {/* Tip Section */}
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
                </tr>
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
  );

  // --- Main Render ---
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
        
        <nav className={`main-nav ${isMenuOpen ? 'menu-open' : ''}`}>
          <button 
            className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`} 
            onClick={() => {
              setActiveTab('dashboard');
              setIsMenuOpen(false);
            }}
          >
            📊 Dashboard
          </button>
          <button 
            className={`nav-btn ${activeTab === 'upload' ? 'active' : ''}`} 
            onClick={() => {
              setActiveTab('upload');
              setIsMenuOpen(false);
            }}
          >
            ⬆️ Upload Data
          </button>
          <button 
            className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`} 
            onClick={() => { 
              setActiveTab('history'); 
              if (organization) fetchHistory();
              setIsMenuOpen(false);
            }}
          >
            📈 History & Trends
          </button>
          {userRole === 'admin' && (
            <button 
              className={`nav-btn ${activeTab === 'team' ? 'active' : ''}`} 
              onClick={() => {
                setActiveTab('team');
                setIsMenuOpen(false);
              }}
            >
              👥 Team Management
            </button>
          )}
          <button 
            className={`nav-btn ${activeTab === 'assets' ? 'active' : ''}`} 
            onClick={() => {
              setActiveTab('assets');
              setIsMenuOpen(false);
            }}
          >
            🏢 Assets
          </button>
          
          {/* Hamburger Toggle Button */}
          <button 
            className="hamburger-toggle"
            onClick={toggleMenu}
            aria-label={isMenuOpen ? "Close menu" : "Open menu"}
          >
            {isMenuOpen ? '✕' : '☰'}
          </button>
        </nav>
      </header>





      <div className="container">
        {activeTab === 'dashboard' && renderDashboard()}
        {/* PDF/IMAGE INGESTION PORTAL */}
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
      
      {/* Onboarding Wizard - Full Screen Overlay */}
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

export default function App() {
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState(null);

useEffect(() => {
  const initializeAuth = async () => {
    try {
      console.log('🚀 Initializing auth...');
      
      // Get initial session
      const { data: { session: initialSession }, error } = await supabase.auth.getSession();
      
      if (error) {
        console.error('❌ Error getting session:', error);
      }
      
      console.log('📊 Initial session:', initialSession ? 'Exists' : 'None');
      
      if (initialSession) {
        console.log('👤 Session found for:', initialSession.user.email);
        setSession(initialSession);
      } else {
        console.log('👤 No session found');
      }
    } catch (error) {
      console.error('❌ Auth initialization error:', error);
    } finally {
      setLoading(false);
      console.log('✅ Auth initialization complete');
    }
  };

  initializeAuth();

  // Listen for auth state changes
  const { data: { subscription } } = supabase.auth.onAuthStateChange(
    async (event, session) => {
      console.log('🔐 App auth event:', event);
      console.log('📊 App session:', session ? 'Exists' : 'None');
      
      if (event === 'SIGNED_IN') {
        console.log('✅ User signed in:', session?.user?.email);
        setSession(session);
      } else if (event === 'SIGNED_OUT') {
        console.log('👋 User signed out');
        setSession(null);
      } else if (event === 'TOKEN_REFRESHED') {
        console.log('🔄 Token refreshed');
      } else if (event === 'USER_UPDATED') {
        console.log('👤 User updated');
      }
      
      setLoading(false);
    }
  );

  return () => {
    subscription.unsubscribe();
  };
}, []);


  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loader">Loading...</div>
      </div>
    );
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
        <Route path="/auth/callback" element={<AuthCallback />} />


        <Route path="/dashboard/*" element={
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
