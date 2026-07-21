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



// Protected Route Component
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

const AppRoutes = () => {
  const { user, isStaff } = useAuth();

  if (!user || !isStaff) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Layout>
      <Routes>
        <Route path="/admin" element={<Dashboard />} />
        <Route path="/admin/reviews" element={<Reviews />} />
        <Route path="/admin/users" element={<Users />} />
        <Route path="/admin/organizations" element={<Organizations />} />
        <Route path="/admin/batches" element={<Batches />} />
        <Route path="/admin/analytics" element={<Analytics />} />
        <Route path="/admin/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/admin" replace />} />
        <Route path="/admin/defra" element={<DefraFactors />} />
        <Route path="/admin/customers" element={<Customers />} />
        <Route path="/admin/reviews" element={<ManualReviewQueue />} />
        <Route path="/admin/errors" element={<ExtractionErrorReview />} />

      </Routes>
    </Layout>
  );
};
function App() {
  console.log('🚀 App is rendering!');
  
  // Add a simple test render
  const [testLoaded, setTestLoaded] = React.useState(false);
  React.useEffect(() => {
    console.log('✅ App mounted successfully!');
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