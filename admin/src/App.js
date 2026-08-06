// admin/src/App.js
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { RealtimeProvider } from './context/RealtimeContext'; // ✅ Add this
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
import ExtractionErrorReview from './pages/admin/ExtractionErrorReview';
import BetaManagement from './pages/admin/BetaManagement';
import GlossaryManagement from './pages/admin/GlossaryManagement';
import ManualReviewQueue from './pages/admin/ManualReviewQueue';
import StaffReviewQueue from './components/StaffReviewQueue';
import LogViewer from './components/LogViewer';
import AdminAssignment from './components/AdminAssignment';
import WorkHub from './pages/admin/WorkHub';

// Staff Pages
import StaffDashboard from './pages/staff/StaffDashboard';

// Secure Route Structural Guard Wrapper
const AdminProtectedLayout = () => {
  const { user, loading, isStaff } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Access Panel...</p>
        </div>
      </div>
    );
  }

  if (!user || !isStaff) {
    return <Navigate to="/admin/login" replace />;
  }

  return (
    <Layout>
      <Outlet />
    </Layout>
  );
};

const AppRoutes = () => {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/admin/login" element={<Login />} />

      <Route element={<AdminProtectedLayout />}>
        <Route path="/admin" element={<Dashboard />} />
        <Route path="/admin/reviews" element={<Reviews />} />
        <Route path="/admin/users" element={<Users />} />
        <Route path="/admin/organizations" element={<Organizations />} />
        <Route path="/admin/batches" element={<Batches />} />
        <Route path="/admin/analytics" element={<Analytics />} />
        <Route path="/admin/settings" element={<Settings />} />
        <Route path="/admin/defra" element={<DefraFactors />} />
        <Route path="/admin/customers" element={<Customers />} />
        <Route path="/admin/manual-review-queue" element={<ManualReviewQueue />} />
        <Route path="/admin/errors" element={<ExtractionErrorReview />} />
        <Route path="/admin/beta-management" element={<BetaManagement />} />
        <Route path="/admin/glossary-management" element={<GlossaryManagement />} />
        <Route path="/staff-dashboard" element={<StaffDashboard />} />
        <Route path="/admin/reviews-queue" element={<StaffReviewQueue />} />
        <Route path="/admin/log-viewer" element={<LogViewer />} />
        <Route path="/admin/assignments" element={<AdminAssignment />} />
        <Route path="/admin/work-hub" element={<WorkHub />} />

      </Route>

      <Route path="*" element={<Navigate to="/admin/login" replace />} />
    </Routes>
  );
};

function App() {
  console.log('🚀 Admin System Booted!');

  return (
    <AuthProvider>
      {/* ✅ Wrap with RealtimeProvider */}
      <RealtimeProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </RealtimeProvider>
    </AuthProvider>
  );
}

export default App;