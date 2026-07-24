// src/App.js
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/layout/Layout';
import Login from './pages/Login';

// Admin Pages
import Dashboard from './pages/admin/Dashboard';
import Reviews from './pages/admin/Reviews';
import Users from './pages/admin/Users';
import Organizations from './pages/admin/Organizations';
import Batches from './pages/admin/Batches';
import Analytics from './pages/admin/Analytics';
import Settings from './pages/admin/Settings';
import DefraFactors from './pages/admin/DefraFactors';
import Customers from './pages/admin/Customers';
import ManualReviewQueue from './pages/admin/ManualReviewQueue';
import ExtractionErrorReview from './pages/admin/ExtractionErrorReview';
import BetaManagement from './pages/admin/BetaManagement';
import ReviewAssignment from './pages/admin/ReviewAssignment';
import GlossaryManagement from './pages/admin/GlossaryManagement';

// Staff Pages
import StaffDashboard from './pages/staff/StaffDashboard';

// Protected Route Component - Staff Only
const ProtectedRoute = ({ children }) => {
  const { user, loading, isStaff } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user || !isStaff) {
    return <Navigate to="/login" replace />;
  }

  return children;
};
// src/App.js
const AppRoutes = () => {
  const { user, isStaff } = useAuth();

  // 1. Unauthenticated Gateway
  if (!user || !isStaff) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  // 2. Authenticated Admin/Staff Dashboard Portal
  return (
    <Layout>
      <Routes>
        {/* Admin Routes (Removed redundant /admin prefix) */}
        <Route path="/" element={<Dashboard />} />
        <Route path="/reviews" element={<Reviews />} />
        <Route path="/users" element={<Users />} />
        <Route path="/organizations" element={<Organizations />} />
        <Route path="/batches" element={<Batches />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/defra" element={<DefraFactors />} />
        <Route path="/customers" element={<Customers />} />
        <Route path="/errors" element={<ExtractionErrorReview />} />
        <Route path="/beta" element={<BetaManagement />} />
        <Route path="/review-assignment" element={<ReviewAssignment />} />
        <Route path="/glossary-management" element={<GlossaryManagement />} />
        
        {/* Staff Routes */}
        <Route path="/staff/dashboard" element={<StaffDashboard />} />
        
        {/* Default fallback for authenticated staff */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
};

function App() {
  console.log('🚀 Admin App rendering!');
  
  const [testLoaded, setTestLoaded] = React.useState(false);
  React.useEffect(() => {
    console.log('✅ Admin App mounted successfully!');
    setTestLoaded(true);
  }, []);
  
  if (!testLoaded) {
    return <div>Loading App...</div>;
  }

  return (
    <AuthProvider>
      <BrowserRouter basename="/admin">
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;