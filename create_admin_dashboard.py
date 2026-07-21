#!/usr/bin/env python3
"""
CarbonTally Admin Dashboard - Project Structure Generator
This script creates the complete folder structure and stub files for the admin dashboard.
"""

import os
from pathlib import Path
import sys

# Define the project structure
PROJECT_STRUCTURE = {
    "public": {
        "files": [
            "index.html",
            "favicon.ico"
        ]
    },
    "src": {
        "files": [
            "index.js",
            "index.css",
            "App.js",
            "supabaseClient.js"
        ],
        "folders": {
            "context": {
                "files": [
                    "AuthContext.js"
                ]
            },
            "components": {
                "folders": {
                    "admin": {
                        "files": [
                            "StatCard.js",
                            "ActivityChart.js",
                            "ReviewStatusChart.js",
                            "RecentActivity.js",
                            "ReviewModal.js"
                        ]
                    },
                    "layout": {
                        "files": [
                            "Layout.js",
                            "Sidebar.js",
                            "TopBar.js"
                        ]
                    }
                }
            },
            "pages": {
                "files": [
                    "Login.js"
                ],
                "folders": {
                    "admin": {
                        "files": [
                            "Dashboard.js",
                            "Reviews.js",
                            "Users.js",
                            "Organizations.js",
                            "Batches.js",
                            "Analytics.js",
                            "Settings.js"
                        ]
                    }
                }
            },
            "utils": {
                "files": [
                    "helpers.js"
                ]
            }
        }
    }
}

# Root level files
ROOT_FILES = [
    "package.json",
    "tailwind.config.js",
    ".env",
    "README.md"
]

# Stub content for files
FILE_STUBS = {
    "package.json": """{
  "name": "carbontally-admin",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "@supabase/supabase-js": "^2.39.0",
    "@tanstack/react-query": "^5.12.2",
    "axios": "^1.6.2",
    "chart.js": "^4.4.1",
    "date-fns": "^2.30.0",
    "react": "^18.2.0",
    "react-chartjs-2": "^5.2.0",
    "react-dom": "^18.2.0",
    "react-hook-form": "^7.48.2",
    "react-hot-toast": "^2.4.1",
    "react-icons": "^4.12.0",
    "react-router-dom": "^6.20.1",
    "react-select": "^5.8.0",
    "react-table": "^7.8.0",
    "react-toastify": "^9.1.3",
    "recharts": "^2.10.3"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "devDependencies": {
    "react-scripts": "5.0.1",
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}""",
    "tailwind.config.js": """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        secondary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
      },
    },
  },
  plugins: [],
}""",
    ".env": """REACT_APP_SUPABASE_URL=https://pvwiojoyaqywtydzcpbg.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key-here
REACT_APP_SUPABASE_SERVICE_KEY=your-service-key-here
REACT_APP_API_URL=http://localhost:8000""",
    "README.md": """# CarbonTally Admin Dashboard

## Setup Instructions

### Prerequisites
- Node.js (v16 or higher)
- npm or yarn

### Installation
1. Clone the repository
2. Run `npm install` to install dependencies
3. Copy `.env.example` to `.env` and update with your Supabase credentials
4. Run `npm start` to start the development server

### Features
- Document review management
- User management
- Organization management
- GDPR compliance
- Analytics and reporting

### Tech Stack
- React 18
- Tailwind CSS
- Supabase
- React Query
- Recharts
- React Router v6""",
    "src/index.js": """import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);""",
    "src/index.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-gray-50 text-gray-900 antialiased;
  }
}

@layer components {
  .sidebar-link {
    @apply flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-primary-50 hover:text-primary-600 rounded-lg transition-all duration-200;
  }
  
  .sidebar-link.active {
    @apply bg-primary-50 text-primary-600 font-medium;
  }
  
  .stat-card {
    @apply bg-white rounded-xl shadow-sm p-6 border border-gray-100 hover:shadow-md transition-shadow duration-200;
  }
  
  .stat-card .stat-icon {
    @apply w-12 h-12 rounded-lg flex items-center justify-center text-2xl;
  }
  
  .btn-primary {
    @apply px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200 font-medium;
  }
  
  .btn-secondary {
    @apply px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors duration-200 font-medium;
  }
  
  .btn-danger {
    @apply px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200 font-medium;
  }
  
  .input-field {
    @apply w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all duration-200;
  }
  
  .card {
    @apply bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden;
  }
  
  .card-header {
    @apply px-6 py-4 border-b border-gray-100 bg-gray-50/50;
  }
  
  .card-body {
    @apply p-6;
  }
  
  .badge {
    @apply px-2.5 py-0.5 rounded-full text-xs font-medium;
  }
  
  .badge-success {
    @apply bg-green-100 text-green-800;
  }
  
  .badge-warning {
    @apply bg-yellow-100 text-yellow-800;
  }
  
  .badge-danger {
    @apply bg-red-100 text-red-800;
  }
  
  .badge-info {
    @apply bg-blue-100 text-blue-800;
  }
  
  .badge-gray {
    @apply bg-gray-100 text-gray-800;
  }
}""",
    "src/supabaseClient.js": """import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Admin helper to check if user is admin or staff
export const isAdminOrStaff = async (userId) => {
  if (!userId) return false;
  
  try {
    // Check if user is in staff_profiles table
    const { data: staffData, error: staffError } = await supabase
      .from('staff_profiles')
      .select('role')
      .eq('id', userId)
      .single();
    
    if (staffData) {
      return { isStaff: true, role: staffData.role };
    }
    
    // Check if user is an admin in any organization
    const { data: orgData, error: orgError } = await supabase
      .from('organization_members')
      .select('role')
      .eq('user_id', userId)
      .eq('role', 'admin')
      .limit(1);
    
    if (orgData && orgData.length > 0) {
      return { isStaff: false, role: 'admin' };
    }
    
    return { isStaff: false, role: 'user' };
  } catch (error) {
    console.error('Error checking admin status:', error);
    return { isStaff: false, role: 'user' };
  }
};""",
    "src/App.js": """import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
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
      </Routes>
    </Layout>
  );
};

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;"""
}

# Default stub for JavaScript files
JS_FILE_STUB = """import React from 'react';

const {{COMPONENT_NAME}} = () => {
  return (
    <div>
      <h1>{{COMPONENT_NAME}}</h1>
      <p>This component is ready for implementation.</p>
    </div>
  );
};

export default {{COMPONENT_NAME}};"""

def create_file_with_stub(file_path, file_name):
    """Create a file with appropriate stub content"""
    # Determine if this is a React component file
    is_component = file_name.endswith('.js') and not file_name.endswith('.css')
    is_root_file = file_name in FILE_STUBS
    
    if is_root_file:
        content = FILE_STUBS[file_name]
    elif is_component:
        # Extract component name from filename
        component_name = file_name.replace('.js', '')
        content = JS_FILE_STUB.replace('{{COMPONENT_NAME}}', component_name)
    else:
        content = ""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def create_directory(path):
    """Create a directory if it doesn't exist"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {path}")
        return True
    except Exception as e:
        print(f"❌ Error creating directory {path}: {e}")
        return False

def create_file(path, file_name):
    """Create a file with appropriate content"""
    try:
        file_path = path / file_name
        if file_path.exists():
            print(f"⚠️  File already exists: {file_path}")
            return
        
        # Determine if this is a file with special content
        if file_name in FILE_STUBS:
            content = FILE_STUBS[file_name]
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        elif file_name.endswith('.js'):
            # React component file
            component_name = file_name.replace('.js', '')
            content = JS_FILE_STUB.replace('{{COMPONENT_NAME}}', component_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            # Empty file
            file_path.touch()
        
        print(f"✅ Created file: {file_path}")
    except Exception as e:
        print(f"❌ Error creating file {file_name}: {e}")

def build_structure(base_path, structure):
    """Recursively build the folder structure"""
    for name, content in structure.items():
        # Check if this is a file entry
        if name == "files":
            for file_name in content:
                create_file(base_path, file_name)
            continue
        
        # This is a folder
        folder_path = base_path / name
        if create_directory(folder_path):
            # Process sub-items
            if isinstance(content, dict):
                build_structure(folder_path, content)

def main():
    """Main execution function"""
    # Get the current working directory
    current_dir = Path.cwd()
    project_root = current_dir / "carbontally-admin"
    
    print("=" * 60)
    print("🌱 CarbonTally Admin Dashboard - Project Generator")
    print("=" * 60)
    print(f"📂 Project will be created at: {project_root}")
    print()
    
    # Create root directory
    if create_directory(project_root):
        # Create root level files
        for root_file in ROOT_FILES:
            create_file(project_root, root_file)
        
        # Build the folder structure
        build_structure(project_root, PROJECT_STRUCTURE)
        
        print()
        print("=" * 60)
        print("✅ Project structure created successfully!")
        print()
        print("📋 Next steps:")
        print("  1. cd carbontally-admin")
        print("  2. npm install")
        print("  3. Update .env with your Supabase credentials")
        print("  4. npm start")
        print("=" * 60)
    else:
        print("❌ Failed to create project root directory")
        sys.exit(1)

if __name__ == "__main__":
    main()