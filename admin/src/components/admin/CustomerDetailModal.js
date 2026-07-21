// src/components/admin/CustomerDetailModal.js
import React from 'react';
import { FaTimes, FaUsers, FaBuilding, FaBoxes, FaLeaf, FaCrown, FaCalendarAlt, FaChartLine } from 'react-icons/fa';

const CustomerDetailModal = ({ isOpen, onClose, customer }) => {
  if (!isOpen || !customer) return null;

  const getTierColor = (tier) => {
    const tiers = {
      pro: 'text-green-600 bg-green-50',
      premium: 'text-blue-600 bg-blue-50',
      standard: 'text-yellow-600 bg-yellow-50',
      free: 'text-gray-600 bg-gray-50',
    };
    return tiers[tier?.toLowerCase()] || 'text-gray-600 bg-gray-50';
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        {/* Backdrop */}
        <div className="fixed inset-0 bg-black/50" onClick={onClose}></div>

        {/* Modal */}
        <div className="relative bg-white rounded-xl shadow-xl max-w-2xl w-full">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <div>
              <h2 className="text-xl font-bold text-gray-900">🏢 Organization Details</h2>
              <p className="text-sm text-gray-500">{customer.organization_name}</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <FaTimes />
            </button>
          </div>

          {/* Body */}
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Organization Info */}
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-500">Organization Name</h4>
                  <p className="text-lg font-semibold text-gray-900">{customer.organization_name}</p>
                </div>

                {customer.company_number && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Company Number</h4>
                    <p className="text-sm text-gray-600">{customer.company_number}</p>
                  </div>
                )}

                <div>
                  <h4 className="text-sm font-medium text-gray-500">Organization ID</h4>
                  <p className="text-sm font-mono text-gray-600 bg-gray-50 p-2 rounded-lg">
                    {customer.organization_id}
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-500">Subscription Tier</h4>
                  <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg text-sm font-medium ${getTierColor(customer.subscription_tier)}`}>
                    <FaCrown />
                    {(customer.subscription_tier || 'Free').toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Statistics */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-blue-50 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-blue-600">
                      <FaUsers />
                      <span className="text-sm font-medium">Members</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">{customer.member_count || 0}</p>
                  </div>

                  <div className="bg-purple-50 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-purple-600">
                      <FaBuilding />
                      <span className="text-sm font-medium">Facilities</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">{customer.facility_count || 0}</p>
                  </div>

                  <div className="bg-indigo-50 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-indigo-600">
                      <FaBoxes />
                      <span className="text-sm font-medium">Assets</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">{customer.asset_count || 0}</p>
                  </div>

                  <div className="bg-green-50 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-green-600">
                      <FaLeaf />
                      <span className="text-sm font-medium">Emissions</span>
                    </div>
                    <p className="text-lg font-bold text-gray-900">
                      {(customer.total_emissions_kg_co2e || 0).toLocaleString()} kg
                    </p>
                    <p className="text-xs text-gray-500">
                      {(customer.total_emissions_kg_co2e / 1000 || 0).toFixed(2)} tonnes
                    </p>
                  </div>
                </div>

                <div className="border-t border-gray-100 pt-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Joined</span>
                    <span className="text-sm text-gray-900">
                      {customer.joined_at ? new Date(customer.joined_at).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                  {customer.last_activity && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">Last Activity</span>
                      <span className="text-sm text-gray-900">
                        {new Date(customer.last_activity).toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* GDPR Notice */}
            <div className="mt-6 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-xs text-blue-700 flex items-center gap-2">
                <span>🔒</span>
                Data is handled in compliance with UK GDPR regulations.
                All personal data is encrypted and access is logged.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end px-6 py-4 border-t border-gray-200 bg-gray-50">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomerDetailModal;