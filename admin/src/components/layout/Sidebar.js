import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  FaHome, 
  FaClipboardList, 
  FaUsers, 
  FaBuilding, 
  FaFolderOpen, 
  FaChartBar, 
  FaCog,
  FaSignOutAlt,
  FaChevronLeft,
  FaChevronRight,
  FaBook 
} from 'react-icons/fa';
import { FaCalculator } from 'react-icons/fa';
import { FaBug } from 'react-icons/fa';

const Sidebar = ({ open, setOpen }) => {
  const { signOut, user, staffRole } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await signOut();
    navigate('/login');
  };

  const menuItems = [
    { path: '/admin', icon: FaHome, label: 'Dashboard' },
    { path: '/admin/reviews', icon: FaClipboardList, label: 'Reviews' },
    { path: '/admin/users', icon: FaUsers, label: 'Users' },
    { path: '/admin/organizations', icon: FaBuilding, label: 'Organizations' },
    { path: '/admin/batches', icon: FaFolderOpen, label: 'Batches' },
    { path: '/admin/analytics', icon: FaChartBar, label: 'Analytics' },
    { path: '/admin/settings', icon: FaCog, label: 'Settings' },
    { path: '/admin/defra', icon: FaCalculator, label: 'DEFRA Factors' },
    { path: '/admin/customers', icon: FaUsers, label: 'Customers' },
    { path: '/admin/reviews', icon: FaClipboardList, label: 'Review Queue' },
    { path: '/admin/errors', icon: FaBug, label: 'Extraction Errors' },
    { path: '/admin/beta', icon: FaBug, label: 'Beta Management' },
    { path: '/admin/review-assignment', icon: FaUsers, label: 'Review Assignment' },
    { path: '/admin/GlossaryManagement', icon: FaBook, label: 'Glossary Management' },

  ];

  return (
    <>
      {/* Mobile backdrop */}
      {!open && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setOpen(true)}
        />
      )}
      
      <aside 
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          bg-white border-r border-gray-200
          transition-all duration-300 ease-in-out
          ${open ? 'w-64' : 'w-20'}
          flex flex-col
        `}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌱</span>
            {open && (
              <span className="font-bold text-lg text-gray-800">CarbonTally</span>
            )}
          </div>
          <button
            onClick={() => setOpen(!open)}
            className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {open ? <FaChevronLeft /> : <FaChevronRight />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-1">
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `
                flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                ${isActive 
                  ? 'bg-primary-50 text-primary-600 font-medium' 
                  : 'text-gray-600 hover:bg-gray-50'
                }
                ${!open && 'justify-center'}
              `}
              title={!open ? item.label : ''}
            >
              <item.icon className="text-xl" />
              {open && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* User & Logout */}
        <div className="border-t border-gray-200 p-4">
          {open ? (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-medium">
                {user?.email?.[0]?.toUpperCase() || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700 truncate">
                  {user?.email || 'User'}
                </p>
                <p className="text-xs text-gray-500">
                  {staffRole || 'User'}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex justify-center">
              <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-medium">
                {user?.email?.[0]?.toUpperCase() || 'U'}
              </div>
            </div>
          )}
          
          <button
            onClick={handleLogout}
            className={`
              w-full mt-3 flex items-center gap-3 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors
              ${!open && 'justify-center'}
            `}
            title={!open ? 'Logout' : ''}
          >
            <FaSignOutAlt />
            {open && <span>Logout</span>}
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;