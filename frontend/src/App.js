// App.js - Fully Refactored with Correct API Endpoints

import React, { useState, useEffect, useMemo } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, Link } from 'react-router-dom';
import { supabase } from './supabaseClient';
import Login from './Login';
import * as XLSX from 'xlsx';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './App.css';
import './css/realtime.css';
import './public/demos/demos.css'; // D21 — shared demo base styles (public demos)
import TeamManagement from './TeamManagement';
import AssetManager from './AssetManager';
import CookieBanner from './CookieBanner';
import PrivacyPolicy from './PrivacyPolicy';
import PricingPage from './PricingPage';
import CookiePolicy from './CookiePolicy';
import TermsPage from './TermsPage';
import LandingPage from './LandingPage';
import CarbonReductionPlan from './CarbonReductionPlan';
import AboutUs from './AboutUs';
import PlatformPage from './public/PlatformPage';
import ServicesPage from './public/ServicesPage';
import ProcessingServicesPage from './public/ProcessingPage';
import ConsultantsPage from './public/ConsultantsPage';
import ContactPage from './public/ContactPage';
import FaqPage from './public/FaqPage';
import AssistantWidget from './public/assistant/AssistantWidget';
import BulkUpload from './BulkUpload';
import RecentProcessedData from './RecentProcessedData';
import PDFIngestionPortal from './PDFIngestionPortal';
import toast from 'react-hot-toast';
import OnboardingWizard from './OnboardingWizard';
import CompanyNamePrompt from './CompanyNamePrompt';
import AuthCallback from './AuthCallback';
import BetaSignup from './BetaSignup';
import SelfServiceSignup from './SelfServiceSignup';
import OnboardingPage from './OnboardingPage';
import BetaLogin from './BetaLogin';
import Glossary from './Glossary';
import MagicLink from './MagicLink';
import OrganizationMetadata from './OrganizationMetadata';
import DocumentStatus from './DocumentStatus';
import UploadManager from './UploadManager';
import ManualEntryStandalone from './components/ManualEntryStandalone';
import { ReferenceDataProvider } from './context/ReferenceDataContext';
import ChatWidget from './components/chat/ChatWidget';
import ReportsPage from './v3/reports/ReportsPage';
import ReportDetailPage from './v3/reports/ReportDetailPage';
import AdminPage from './v3/admin/AdminPage';
import BillingPage from './v3/customer/BillingPage';
import ConsultantPage from './v3/consultant/ConsultantPage';
import OperationsPage from './v3/ops/OperationsPage';
import DashboardPage from './v3/customer/DashboardPage';
import EmissionsPage from './v3/customer/EmissionsPage';
import DocumentsPage from './v3/customer/DocumentsPage';
import ProcessingPage from './v3/customer/ProcessingPage';
import ReviewPage from './v3/customer/ReviewPage';
import ReviewDetailPage from './v3/customer/ReviewDetailPage';
import IssuesPage from './v3/customer/IssuesPage';
import ExistingDataDiscoveryPage from './v3/customer/ExistingDataDiscoveryPage';
import MessagingPage from './v3/customer/MessagingPage';
import NotificationsPage from './v3/NotificationsPage';
import RoleRoute from './v3/components/RoleRoute';
import V3Layout from './v3/components/V3Layout';

// ✅ Import Realtime
import { 
  RealtimeProviderWrapper,
  useRealtime,
  useNotifications,
  useDocumentStatus,
  useMessageCount
} from './context/RealtimeContext';

// API Base URL
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

// ============================================
// ✅ FIXED: fetchWithAuth - Adds /api prefix automatically
// ============================================

const fetchWithAuth = async (endpoint, options = {}) => {
  const token = await getToken();
  
  // Ensure endpoint starts with /api
  let url = endpoint;
  if (!url.startsWith('/api')) {
    url = `/api${url.startsWith('/') ? url : '/' + url}`;
  }
  
  const fullUrl = `${API_URL}${url}`;
  console.log('📡 Fetching:', fullUrl);
  
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

// ============================================
// REALTIME NOTIFICATION BELL COMPONENT
// ============================================

function NotificationBell() {
  const { isConnected } = useRealtime();
  const { notifications, unreadCount, markAsRead, markAllAsRead, clearAll } = useNotifications();
  const [isOpen, setIsOpen] = useState(false);

  const handleNotificationClick = (notification) => {
    if (!notification.is_read) {
      markAsRead(notification.id);
    }
    setIsOpen(false);
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'relative',
          padding: '0.5rem',
          borderRadius: '50%',
          border: 'none',
          backgroundColor: 'transparent',
          cursor: 'pointer',
          transition: 'background-color 0.2s',
        }}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f1f5f9'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
      >
        <span style={{ fontSize: '1.25rem' }}>🔔</span>
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute',
            top: '-4px',
            right: '-4px',
            backgroundColor: '#ef4444',
            color: 'white',
            fontSize: '0.65rem',
            fontWeight: '700',
            padding: '2px 6px',
            borderRadius: '50%',
            minWidth: '18px',
            textAlign: 'center',
          }}>
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
        {!isConnected && (
          <span style={{
            position: 'absolute',
            bottom: '-2px',
            right: '-2px',
            width: '10px',
            height: '10px',
            backgroundColor: '#f59e0b',
            borderRadius: '50%',
            border: '2px solid white',
          }} />
        )}
      </button>

      {isOpen && (
        <div style={{
          position: 'absolute',
          top: 'calc(100% + 8px)',
          right: 0,
          width: '380px',
          maxHeight: '480px',
          backgroundColor: 'white',
          borderRadius: '12px',
          boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
          zIndex: 1000,
          overflow: 'hidden',
        }}>
          <div style={{
            padding: '0.75rem 1rem',
            borderBottom: '1px solid #e2e8f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#f8fafc',
          }}>
            <span style={{ fontWeight: '600', fontSize: '0.95rem' }}>
              Notifications {unreadCount > 0 && `(${unreadCount} unread)`}
            </span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  style={{
                    padding: '0.25rem 0.75rem',
                    fontSize: '0.75rem',
                    backgroundColor: '#e2e8f0',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                  }}
                >
                  Mark all read
                </button>
              )}
              <button
                onClick={() => { clearAll(); setIsOpen(false); }}
                style={{
                  padding: '0.25rem 0.75rem',
                  fontSize: '0.75rem',
                  backgroundColor: '#fee2e2',
                  color: '#dc2626',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Clear all
              </button>
            </div>
          </div>

          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {notifications.length === 0 ? (
              <div style={{
                padding: '2rem 1rem',
                textAlign: 'center',
                color: '#94a3b8',
                fontSize: '0.9rem',
              }}>
                No notifications yet
              </div>
            ) : (
              notifications.slice(0, 50).map((notification) => (
                <div
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  style={{
                    padding: '0.75rem 1rem',
                    borderBottom: '1px solid #f1f5f9',
                    cursor: 'pointer',
                    backgroundColor: notification.is_read ? 'white' : '#f0fdf4',
                    transition: 'background-color 0.15s',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f8fafc'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 
                    notification.is_read ? 'white' : '#f0fdf4'
                  }
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '0.9rem', color: '#0f172a' }}>
                        {notification.title}
                      </div>
                      <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.2rem' }}>
                        {notification.message}
                      </div>
                      {notification.type && (
                        <span style={{
                          fontSize: '0.65rem',
                          backgroundColor: '#e2e8f0',
                          padding: '0.1rem 0.5rem',
                          borderRadius: '12px',
                          color: '#475569',
                          marginTop: '0.25rem',
                          display: 'inline-block',
                        }}>
                          {notification.type}
                        </span>
                      )}
                    </div>
                    {!notification.is_read && (
                      <span style={{
                        width: '8px',
                        height: '8px',
                        backgroundColor: '#22c55e',
                        borderRadius: '50%',
                        flexShrink: 0,
                        marginTop: '4px',
                      }} />
                    )}
                  </div>
                  <div style={{
                    fontSize: '0.65rem',
                    color: '#94a3b8',
                    marginTop: '0.25rem',
                  }}>
                    {new Date(notification.created_at).toLocaleString()}
                  </div>
                </div>
              ))
            )}
          </div>

          {notifications.length > 0 && (
            <div style={{
              padding: '0.5rem 1rem',
              borderTop: '1px solid #e2e8f0',
              textAlign: 'center',
              backgroundColor: '#f8fafc',
            }}>
              <Link
                to="/notifications"
                style={{
                  fontSize: '0.85rem',
                  color: '#3b82f6',
                  textDecoration: 'none',
                }}
                onClick={() => setIsOpen(false)}
              >
                View all notifications →
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================
// REALTIME STATUS INDICATOR
// ============================================

function RealtimeStatus() {
  const { isConnected, onlineStaff } = useRealtime();
  
  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: '0.5rem',
      fontSize: '0.8rem',
      color: '#64748b',
    }}>
      <span style={{
        display: 'inline-block',
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        backgroundColor: isConnected ? '#22c55e' : '#ef4444',
        transition: 'background-color 0.3s',
      }} />
      <span>Live</span>
      {onlineStaff.length > 0 && (
        <span style={{ marginLeft: '0.5rem', color: '#94a3b8' }}>
          • {onlineStaff.length} online
        </span>
      )}
    </div>
  );
}

// ============================================
// MAIN DASHBOARD COMPONENT
// ============================================

function Dashboard({ user }){
  
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
  
  // Realtime hooks
  const { isConnected, onlineStaff } = useRealtime();
  const { notifications, unreadCount, markAsRead, markAllAsRead, clearAll } = useNotifications();
  const { documents: realtimeDocuments, statusCounts } = useDocumentStatus();
  const unreadMessageCount = useMessageCount();

  // Auth & Organization State
  const [session, setSession] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [showCompanyPrompt, setShowCompanyPrompt] = useState(false);
  const [isNewUser, setIsNewUser] = useState(false);
  
  // UI State
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showBulkUpload, setShowBulkUpload] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState('');
  const [docStats, setDocStats] = useState(null);

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
  const [reportDropdownOpen, setReportDropdownOpen] = useState(false);
  const [showManualEntry, setShowManualEntry] = useState(false);

  // ============================================
  // ✅ FIXED: ORGANIZATION FUNCTIONS
  // ============================================

  const fetchOrganization = async (userId) => {
    try {
      console.log('🔍 Fetching organization for user:', userId);
      
      const response = await fetchWithAuth(`/api/organizations/members/user/${userId}`);
      
      if (!response.ok) {
        console.log('ℹ️ User is not a member of any organization');
        return null;
      }
      
      const data = await response.json();
      console.log('📦 Organization data:', data);
      
      if (data?.primary_organization) {
        console.log('✅ Found organization:', data.primary_organization.name);
        setOrganization(data.primary_organization);
        setUserRole(data.role || 'admin');
        return data.primary_organization;
      }
      
      if (data?.organization) {
        console.log('✅ Found organization (legacy):', data.organization.name);
        setOrganization(data.organization);
        setUserRole(data.role || 'admin');
        return data.organization;
      }
      
      return null;
    } catch (error) {
      console.error('❌ Error fetching organization:', error);
      return null;
    }
  };

  const createOrganizationFromMetadata = async (user) => {
    try {
      const companyName = user.user_metadata.company_name;
      console.log('🏢 Creating organization from metadata:', companyName);
      
      const response = await fetchWithAuth('/api/organizations', {
        method: 'POST',
        body: JSON.stringify({
          name: companyName,
          created_by: user.id,
          settings: { currency: 'GBP', country: 'UK' }
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create organization');
      }

      const org = await response.json();
      setOrganization(org);
      setUserRole('admin');
      setShowCompanyPrompt(false);
      await loadOrganizationData(org.id);
      toast.success(`✅ Welcome ${org.name}!`);
      
      return org;
    } catch (error) {
      console.error('❌ Error creating organization:', error);
      toast.error('Failed to create organization');
      return null;
    }
  };

  // ============================================
  // ✅ FIXED: DATA FETCHING FUNCTIONS
  // ============================================

  // ✅ GET /api/organizations/{org_id}/assets/stats
  const fetchDashboardStats = async (orgId) => {
    try {
      // ✅ Use Supabase directly
      const { data, error } = await supabase
        .from('emissions_logs')
        .select('calculated_kg_co2e')
        .eq('organization_id', orgId);

      if (error) {
        console.error('❌ Supabase error:', error);
        throw new Error('Failed to fetch stats');
      }

      let totalEmissions = 0;
      if (data) {
        data.forEach(row => {
          totalEmissions += parseFloat(row.calculated_kg_co2e) || 0;
        });
      }

      setDashboardStats({
        totalEmissions: totalEmissions,
        totalTransactions: data?.length || 0
      });
      
    } catch (error) {
      console.error('❌ Error fetching stats:', error);
      setDashboardStats({ totalEmissions: 0, totalTransactions: 0 });
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

  // ✅ GET /api/emissions/{org_id}/emissions
  const fetchEmissionHistory = async () => {
  if (!organization) {
    console.log("⏳ Waiting for organization...");
    return;
  }

  setLoadingHistory(true);
    try {
      // ✅ Use Supabase directly - bypass API
      const { data, error } = await supabase
        .from('emissions_logs')
        .select(`
          id,
          start_date,
          end_date,
          raw_quantity,
          calculated_kg_co2e,
          metadata,
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
        `)
        .eq('organization_id', organization.id)
        .order('start_date', { ascending: false })
        .limit(10000);

      if (error) {
        console.error('❌ Supabase error:', error);
        throw new Error('Failed to fetch emission history');
      }

      setHistoryData(data || []);
      console.log(`✅ Emission history fetched: ${data?.length || 0} records`);
      
    } catch (err) {
      console.error("❌ Error fetching emission history:", err);
      setHistoryData([]);
    } finally {
      setLoadingHistory(false);
    }
  };


  // ✅ GET /api/documents/stats/{org_id}
  const fetchDocumentStats = async () => {
    if (!organization?.id) return;
    
    try {
      // ✅ Use Supabase directly
      const { data, error } = await supabase
        .from('organization_files')
        .select('status')
        .eq('organization_id', organization.id)
        .eq('is_active', true);

      if (error) {
        console.error('❌ Supabase error:', error);
        throw new Error('Failed to fetch document stats');
      }

      // Initialize counts
      const status_counts = {
        'uploaded': 0,
        'processing': 0,
        'staff_review': 0,
        'ready_for_review': 0,
        'approved': 0,
        'rejected': 0
      };

      let total = 0;
      if (data) {
        data.forEach(item => {
          const status = item.status || 'uploaded';
          if (status in status_counts) {
            status_counts[status] += 1;
          }
          total += 1;
        });
      }

      setDocStats({
        stats: status_counts,
        total: total,
        pending_review: status_counts.ready_for_review + status_counts.staff_review
      });
      
    } catch (error) {
      console.error('❌ Error fetching document stats:', error);
      setDocStats(null);
    }
  };

  // ============================================
  // LOAD ORGANIZATION DATA
  // ============================================

  const loadOrganizationData = async (orgId) => {
    console.log('📊 Loading organization data for:', orgId);
    
    try {
      await Promise.all([
        fetchDashboardStats(orgId),
        fetchAssets(orgId),
        fetchFacilities(orgId),
        fetchEmissionHistory(),
        fetchDocumentStats()
      ]);
      console.log('✅ Organization data loaded successfully');
    } catch (error) {
      console.error('❌ Error loading organization data:', error);
    }
  };

  // ============================================
  // EFFECTS
  // ============================================

  useEffect(() => {
    const checkUserStatus = async () => {
      try {
        setLoading(true);
        const { data: { user } } = await supabase.auth.getUser();
        
        if (user) {
          
          setCurrentUser(user);
          console.log('👤 Current User:', user.email);
          console.log('👤 User ID:', user.id);
          console.log('User data:', {
            full_name: user?.user_metadata?.full_name,
            name: user?.user_metadata?.name,
            email: user?.email,
            user_metadata: user?.user_metadata
          });
  
          console.log('👤 Current User is:', currentUser);
          console.log('👤 Checking user status:', user.email);
          setIsNewUser(user.created_at === user.last_sign_in_at);
          
          if (!user.user_metadata?.company_name) {
            console.log('📝 User needs company setup');
            setShowCompanyPrompt(true);
          } else {
            console.log('✅ User has company setup:', user.user_metadata.company_name);
            setShowCompanyPrompt(false);
            
            const org = await fetchOrganization(user.id);
            
            if (org) {
              console.log('✅ Found existing organization:', org.name);
              await loadOrganizationData(org.id);
            } else {
              console.log('ℹ️ User has company_name but no organization found');
              setShowCompanyPrompt(true);
            }
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

  useEffect(() => {
    if (organization) {
      fetchEmissionHistory();
      fetchDocumentStats();
    }
  }, [organization]);

  // ============================================
  // COMPUTED DATA
  // ============================================

  const availableYears = useMemo(() => {
    if (!historyData || historyData.length === 0) return [];
    
    const years = new Set();
    historyData.forEach(row => {
      if (row.start_date) {
        const yearStr = typeof row.start_date === 'string' 
          ? row.start_date.substring(0, 4) 
          : row.start_date.getFullYear().toString();
        const year = parseInt(yearStr);
        if (!isNaN(year) && year > 2000) years.add(year);
      }
    });
    return Array.from(years).sort((a, b) => b - a);
  }, [historyData]);

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

  // ============================================
  // FILE HANDLING
  // ============================================

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) return;

    const isPDF = selectedFile.type === 'application/pdf' || 
                  selectedFile.name.toLowerCase().endsWith('.pdf');
    const isImage = selectedFile.type.startsWith('image/');

    if (isPDF || isImage) {
      setPdfFile(selectedFile);
      setShowPDFPortal(true);
      setFile(null);
      toast.info('📄 Opening document in PDF portal...');
    } else {
      setFile(selectedFile);
      setPdfFile(null);
      setShowPDFPortal(false);
      toast.info('📊 CSV file ready for upload');
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
      setError('Error processing file: ' + err.message);
      toast.error('❌ Failed to process CSV');
    } finally { 
      setLoading(false); 
    }
  };

  // ============================================
  // DATA PROCESSING
  // ============================================

  const getFieldConfig = (type) => FIELD_CONFIGS[type] || FIELD_CONFIGS.fuel;

  const calculateEmissions = (row, fieldConfig) => {
    const volume = parseFloat(row[fieldConfig.volume]);
    const factor = parseFloat(row[fieldConfig.factor]);
    if (!isNaN(volume) && !isNaN(factor)) {
      return parseFloat((volume * factor).toFixed(2));
    }
    return 0;
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

      const recordsToSave = cleanData.map(row => {
        const rawName = row[fieldConfig.site];
        const matchedAsset = assets.find(a => a.name.toUpperCase() === rawName?.toUpperCase());
        
        return {
          organization_id: organization.id,
          asset_id: matchedAsset ? matchedAsset.id : null,
          defra_factor_id: row['DEFRA Factor ID'] || null,
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
            defra_factor_year: row['DEFRA Factor Year'] || null,
            original_filename: result.filename,
            auto_mapped: !!matchedAsset
          }
        };
      });

      const token = await getToken();
      const response = await fetch(`${API_URL}/api/emissions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          organization_id: organization.id,
          records: recordsToSave
        })
      });

      if (!response.ok) throw new Error('Failed to save data');

      toast.success(`✅ Successfully saved ${cleanData.length} records!`);
      
      await fetchEmissionHistory();
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
  // EXPORT & LOGOUT
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
                  <th>Category</th>
                  <th>Consumption</th>
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
                          onChange={(e) => {
                            const newData = [...data];
                            newData[index][fields.type] = e.target.value;
                            setData(newData);
                            validateRow(index);
                          }}
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
                          onChange={(e) => {
                            const newData = [...data];
                            newData[index][fields.volume] = e.target.value === '' ? null : parseFloat(e.target.value);
                            setData(newData);
                          }}
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
          >
            ⬆️ Upload Your First File
          </button>
        </div>
      )}

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
          <RealtimeStatus />
          <NotificationBell />
          
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
                minWidth: '300px',
                overflow: 'hidden'
              }}>
                <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid #f1f5f9', backgroundColor: '#f8fafc' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase' }}>
                    Generate Report for {selectedYear}
                  </span>
                </div>
                
                {[
                  { type: 'SECR', label: '🇬🇧 Enhanced SECR Report', desc: 'With narratives & YoY comparison' },
                  { type: 'CSRD', label: '🇪🇺 Enhanced CSRD Report', desc: 'With methodology & analysis' },
                  { type: 'ISSB', label: '🌍 Enhanced ISSB Report', desc: 'With trend analysis & narratives' },
                  { type: 'AUDITOR_EXCEL', label: '📊 Auditor Data Export (Excel)', desc: 'Granular GHG Protocol mapping' }
                ].map((report) => (
                  <button
                    key={report.type}
                    onClick={async () => {
                      setReportDropdownOpen(false);
                      setLoading(true);
                      try {
                        const isExcel = report.type === 'AUDITOR_EXCEL';
                        const endpoint = isExcel ? '/api/generate-sustainability-report' : '/api/generate-enhanced-report';
                        const token = await getToken();
                        
                        const response = await fetch(`${API_URL}${endpoint}`, {
                          method: 'POST',
                          headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                          },
                          body: JSON.stringify({
                            organization_id: organization.id,
                            reporting_year: selectedYear,
                            report_type: report.type,
                            include_narratives: true
                          })
                        });
                        
                        const result = await response.json();
                        
                        if (result.status === 'success') {
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
                          a.download = result.filename || `Enhanced_${report.type}_Report_${selectedYear}.pdf`;
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
        
        <div className="card">
          <h3>📄 Documents</h3>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', background: '#f1f5f9', padding: '0.15rem 0.5rem', borderRadius: '12px' }}>
              📤 {docStats?.uploaded || statusCounts?.pending || 0}
            </span>
            <span style={{ fontSize: '0.85rem', background: '#fef3c7', padding: '0.15rem 0.5rem', borderRadius: '12px' }}>
              ⏳ {docStats?.processing || statusCounts?.processing || 0}
            </span>
            <span style={{ fontSize: '0.85rem', background: '#dbeafe', padding: '0.15rem 0.5rem', borderRadius: '12px' }}>
              📝 {docStats?.ready_for_review || statusCounts?.extracted || 0}
            </span>
            <span style={{ fontSize: '0.85rem', background: '#dcfce7', padding: '0.15rem 0.5rem', borderRadius: '12px' }}>
              ✅ {docStats?.approved || statusCounts?.approved || 0}
            </span>
            <span style={{ fontSize: '0.85rem', background: '#fee2e2', padding: '0.15rem 0.5rem', borderRadius: '12px' }}>
              ❌ {docStats?.rejected || statusCounts?.rejected || 0}
            </span>
          </div>
          <div className="subtext" style={{ marginTop: '0.5rem' }}>
            <button
              onClick={() => setActiveTab('documents')}
              style={{
                background: 'none',
                border: 'none',
                color: '#3b82f6',
                cursor: 'pointer',
                fontSize: '0.85rem',
                textDecoration: 'underline',
                padding: 0
              }}
            >
              View all documents →
            </button>
          </div>
        </div>
      </div>
      
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
            ⚠️ No emissions data found. Please upload data to generate SECR reports.
          </p>
        </div>
      )}
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
                <Line type="monotone" dataKey="tonnes" stroke="#2b6cb0" strokeWidth={3} dot={{ r: 6 }} />
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

  // ============================================
  // MAIN RENDER
  // ============================================
  const { user: realtimeUser } = useRealtime(); // You need to add user to RealtimeContext

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-top">
          <div className="header-left">
            <h1>🌱 CarbonTally</h1>
          </div>
          
          <div className="header-right">
            <div className="user-info">
              <div className="user-details">
                <span className="company-name">{organization?.name || 'Organization'}</span>
                <span className="user-name">
                  {user?.user_metadata?.full_name || user?.user_metadata?.name || user?.email || 'User'}
                </span>
              </div>
              <div className="user-avatar">
                {(user?.user_metadata?.full_name || user?.email || 'U').charAt(0).toUpperCase()}
              </div>
            </div>
            
            <NotificationBell />
            <RealtimeStatus />
            <button onClick={handleLogout} className="logout-button">Logout</button>
          </div>
        </div>
        
        {/* ✅ ChatWidget - using user prop */}
        {organization && user && (
          <ChatWidget 
            organization={organization}
            user={user}
          />
        )}
        
        <nav className={`main-nav ${isMenuOpen ? 'menu-open' : ''}`}>
          <button 
            className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`} 
            onClick={() => { setActiveTab('dashboard'); setIsMenuOpen(false); }}
          >
            📊 Dashboard
          </button>
          <button 
            className={`nav-btn ${activeTab === 'upload' ? 'active' : ''}`} 
            onClick={() => { setActiveTab('upload'); setIsMenuOpen(false); }}
          >
            ⬆️ Upload Data
          </button>
          <button 
            className={`nav-btn ${activeTab === 'documents' ? 'active' : ''}`} 
            onClick={() => { setActiveTab('documents'); setIsMenuOpen(false); }}
          >
            📄 Documents
          </button>
          <button 
            className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`} 
            onClick={() => { 
              setActiveTab('history'); 
              if (organization) fetchEmissionHistory();
              setIsMenuOpen(false);
            }}
          >
            📈 History & Trends
          </button>
          <button 
            className={`nav-btn ${activeTab === 'reports' ? 'active' : ''}`} 
            onClick={() => { setActiveTab('reports'); setIsMenuOpen(false); navigate('/reports'); }}
          >
            📑 Reports (V3)
          </button>
          <button 
            className={`nav-btn ${activeTab === 'org-admin' ? 'active' : ''}`} 
            onClick={() => { setActiveTab('org-admin'); setIsMenuOpen(false); navigate('/organization'); }}
          >
            🏛️ Organization (V3)
          </button>
          <button 
            className={`nav-btn ${activeTab === 'consultant' ? 'active' : ''}`} 
            onClick={() => { setActiveTab('consultant'); setIsMenuOpen(false); navigate('/consultant'); }}
          >
            🧑‍💼 Consultant (V3)
          </button>
          {userRole === 'admin' && (
            <>
              <button 
                className={`nav-btn ${activeTab === 'team' ? 'active' : ''}`} 
                onClick={() => { setActiveTab('team'); setIsMenuOpen(false); }}
              >
                👥 Team Management
              </button>
            </>
          )}
          <button 
            className={`nav-btn ${activeTab === 'assets' ? 'active' : ''}`} 
            onClick={() => { setActiveTab('assets'); setIsMenuOpen(false); }}
          >
            🏢 Assets
          </button>
          <button 
            className={`nav-btn ${activeTab === 'org-data' ? 'active' : ''}`} 
            onClick={() => { setActiveTab('org-data'); setIsMenuOpen(false); }}
          >
            📊 Org Data
          </button>
          <button 
            className={`nav-btn ${activeTab === 'manual-entry' ? 'active' : ''}`} 
            onClick={() => { 
              setActiveTab('manual-entry');
              setShowManualEntry(true);
              setIsMenuOpen(false);
            }}
          >
            ✏️ Manual Entry
          </button>
          
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
              toast.success("✅ Data approved and saved!");
              setShowPDFPortal(false);
              setPdfFile(null);
              setFile(null);
              setActiveTab('history');
              if (organization) {
                fetchEmissionHistory();
                fetchDashboardStats(organization.id);
              }
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
                <UploadManager 
                  organization={organization}
                  onUploadComplete={(data) => {
                    console.log('Upload complete:', data);
                    fetchEmissionHistory();
                    fetchDashboardStats(organization.id);
                  }}
                />
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
        
        {activeTab === 'documents' && (
          <DocumentStatus organization={organization} />
        )}

        {activeTab === 'history' && renderHistory()}

        {activeTab === 'team' && (
          <TeamManagement organization={organization} userRole={userRole} />
        )}

        {activeTab === 'assets' && (
          <AssetManager organization={organization} />
        )}
        
        {activeTab === 'org-data' && (
          <OrganizationMetadata organization={organization} userRole={userRole} />
        )}  
      
        {activeTab === 'manual-entry' && showManualEntry && (
          <div className="view-section" style={{ padding: 0, margin: 0 }}>
            <ManualEntryStandalone
              organization={organization}
              onComplete={() => {
                setShowManualEntry(false);
                setActiveTab('dashboard');
                fetchEmissionHistory();
                fetchDashboardStats(organization.id);
                toast.success('✅ Data entered successfully!');
              }}
              onCancel={() => {
                setShowManualEntry(false);
                setActiveTab('dashboard');
              }}
            />
          </div>
        )}
      </div>
      {console.log('🔍 Rendering ChatWidget check - organization:', organization, 'user:', currentUser)}

      {organization && currentUser && (
        <>
          {console.log('✅ ChatWidget should render now')}
          <ChatWidget 
            organization={organization}
            user={currentUser}
          />
        </>
      )}
      {/* If not rendering, show why */}
      {(!organization || !currentUser) && (
        console.log('❌ ChatWidget not rendering (in app.js) - missing :', {
          organization: !!organization,
          user: !!currentUser
        })
      )}
      {showOnboarding && onboardingChecked && (
        <OnboardingWizard
          userId={session?.user?.id}
          onComplete={() => setShowOnboarding(false)}
          onSkip={() => setShowOnboarding(false)}
        />
      )}
    </div>
  );
}

// ============================================
// MAIN APP - ✅ Properly placed at top level
// ============================================

export default function App() {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        console.log('🚀 Initializing auth...');
        const { data: { session: initialSession }, error } = await supabase.auth.getSession();
        
        if (error) console.error('❌ Error getting session:', error);
        
        if (initialSession) {
          console.log('👤 Session found for:', initialSession.user.email);
          setSession(initialSession);
          setUser({
            id: initialSession.user.id,
            email: initialSession.user.email,
            organization_id: initialSession.user.user_metadata?.organization_id,
            isStaff: initialSession.user.user_metadata?.is_staff || false,
            accessToken: initialSession.access_token,
            refreshToken: initialSession.refresh_token,
          });
        }
      } catch (error) {
        console.error('❌ Auth initialization error:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event === 'SIGNED_IN') {
          setSession(session);
          setUser({
            id: session.user.id,
            email: session.user.email,
            organization_id: session.user.user_metadata?.organization_id,
            isStaff: session.user.user_metadata?.is_staff || false,
            accessToken: session.access_token,
            refreshToken: session.refresh_token,
          });
        } else if (event === 'SIGNED_OUT') {
          setSession(null);
          setUser(null);
        }
        setLoading(false);
      }
    );

    return () => subscription.unsubscribe();
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
      <ReferenceDataProvider>
        <RealtimeProviderWrapper user={user}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/privacy" element={<PrivacyPolicy />} />
            <Route path="/cookies" element={<CookiePolicy />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/about" element={<AboutUs />} />
            <Route path="/platform" element={<PlatformPage />} />
            <Route path="/services" element={<ServicesPage />} />
            <Route path="/processing-services" element={<ProcessingServicesPage />} />
            <Route path="/consultants" element={<ConsultantsPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/faq" element={<FaqPage />} />
            <Route path="/carbon-reduction-plan" element={<CarbonReductionPlan />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="/signup" element={<SelfServiceSignup />} />
            <Route path="/beta/signup" element={<BetaSignup />} />
            <Route path="/beta-login" element={<BetaLogin />} />
            <Route path="/glossary" element={<Glossary />} />
            <Route path="/auth/magic" element={<MagicLink />} />
            <Route path="/onboarding" element={
              <ProtectedRoute>
                <OnboardingPage />
              </ProtectedRoute>
            } />
            <Route path="/dashboard/*" element={<Navigate to="/home" replace />} />
            <Route path="/home" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <DashboardPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/emissions" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <EmissionsPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/documents" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <DocumentsPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/processing" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <ProcessingPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/review" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <ReviewPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/review/:itemId" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <ReviewDetailPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/existing-data" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <ExistingDataDiscoveryPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/messaging" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <MessagingPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/issues" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <IssuesPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/notifications" element={
              <ProtectedRoute>
                <V3Layout>
                  <NotificationsPage />
                </V3Layout>
              </ProtectedRoute>
            } />
            <Route path="/reports" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <ReportsPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/reports/:id" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <ReportDetailPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/billing" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <BillingPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/organization" element={
              <ProtectedRoute>
                <RoleRoute requireOrg>
                  <V3Layout>
                    <AdminPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/consultant" element={
              <ProtectedRoute>
                <RoleRoute requireConsultant>
                  <V3Layout>
                    <ConsultantPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="/ops" element={
              <ProtectedRoute>
                <RoleRoute requireStaff>
                  <V3Layout>
                    <OperationsPage />
                  </V3Layout>
                </RoleRoute>
              </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <CookieBanner />
          {/* Public CarbonTally Assistant — deterministic local knowledge module
              (no AI provider, no credentials, no network). */}
          <AssistantWidget />
        </RealtimeProviderWrapper>
      </ReferenceDataProvider>
    </BrowserRouter>
  );
}