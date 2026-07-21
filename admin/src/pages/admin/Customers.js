import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { 
  FaUsers, 
  FaBuilding, 
  FaBoxes, 
  FaLeaf, 
  FaCalendarAlt,
  FaEye,
  FaSync,
  FaCrown,
  FaUserPlus,
  FaChartLine
} from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';
import CustomerDetailModal from '../../components/admin/CustomerDetailModal';
import StatCard from '../../components/admin/StatCard';

const Customers = () => {
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const queryClient = useQueryClient();

  // Fetch customers using the admin function
  const { data: customers, isLoading, refetch } = useQuery({
    queryKey: ['adminCustomers'],
    queryFn: async () => {
      const { data, error } = await supabase.rpc('get_admin_customer_overview');
      
      if (error) {
        console.error('Error fetching customers:', error);
        toast.error('Failed to load customers: ' + error.message);
        throw error;
      }
      
      return data || [];
    },
  });

  // Calculate summary statistics
  const summaryStats = {
    totalOrganizations: customers?.length || 0,
    totalMembers: customers?.reduce((sum, c) => sum + (c.member_count || 0), 0) || 0,
    totalFacilities: customers?.reduce((sum, c) => sum + (c.facility_count || 0), 0) || 0,
    totalEmissions: customers?.reduce((sum, c) => sum + (c.total_emissions_kg_co2e || 0), 0) || 0,
    totalAssets: customers?.reduce((sum, c) => sum + (c.asset_count || 0), 0) || 0,
  };

  const handleViewDetails = (customer) => {
    setSelectedCustomer(customer);
    setIsModalOpen(true);
  };

  const handleRefresh = () => {
    refetch();
    toast.success('Data refreshed');
  };

  // Stats cards
  const statCards = [
    {
      title: 'Total Organizations',
      value: summaryStats.totalOrganizations,
      icon: FaBuilding,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Total Members',
      value: summaryStats.totalMembers,
      icon: FaUsers,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'Total Facilities',
      value: summaryStats.totalFacilities,
      icon: FaBoxes,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      title: 'Total Assets',
      value: summaryStats.totalAssets,
      icon: FaBoxes,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
    },
    {
      title: 'Total Emissions',
      value: `${summaryStats.totalEmissions.toLocaleString()} kg CO2e`,
      icon: FaLeaf,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
  ];

  // Get subscription tier color
  const getTierColor = (tier) => {
    const tiers = {
      pro: 'badge-success',
      premium: 'badge-info',
      standard: 'badge-warning',
      free: 'badge-gray',
    };
    return tiers[tier?.toLowerCase()] || 'badge-gray';
  };

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">👥 Customers & Organizations</h1>
            <p className="text-gray-600">Manage and monitor all organizations using CarbonTally</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <FaSync className={isLoading ? 'animate-spin' : ''} />
              Refresh
            </button>
            <button className="btn-primary flex items-center gap-2">
              <FaUserPlus />
              Add Organization
            </button>
          </div>
        </div>
      </div>

      {/* GDPR Compliance Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <div className="text-blue-600 text-xl">🔒</div>
          <div>
            <h4 className="font-medium text-blue-900">GDPR Compliant Data</h4>
            <p className="text-sm text-blue-700">
              All customer data is handled in accordance with UK GDPR regulations. 
              Personal data is encrypted and access is restricted to authorized personnel only.
              All actions are logged for audit purposes.
            </p>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        {statCards.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* Customers Table */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900">Organization List</h3>
            <p className="text-sm text-gray-500">
              {customers?.length || 0} organizations · {summaryStats.totalMembers} total members
            </p>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Search organizations..."
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none text-sm"
            />
          </div>
        </div>
        <div className="card-body p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading organizations...</p>
              </div>
            </div>
          ) : customers?.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">🏢</div>
              <p className="text-gray-500">No organizations found</p>
              <p className="text-sm text-gray-400">Organizations will appear here once they sign up</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Organization
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Members
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Facilities
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Assets
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total Emissions
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tier
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Joined
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {customers?.map((customer) => (
                    <tr key={customer.organization_id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {customer.organization_name}
                          </p>
                          {customer.company_number && (
                            <p className="text-xs text-gray-500">
                              Co. #{customer.company_number}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="badge badge-info">
                          <FaUsers className="inline mr-1 text-xs" />
                          {customer.member_count || 0}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="badge badge-info">
                          <FaBuilding className="inline mr-1 text-xs" />
                          {customer.facility_count || 0}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="badge badge-info">
                          <FaBoxes className="inline mr-1 text-xs" />
                          {customer.asset_count || 0}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm font-medium text-green-600">
                            {customer.total_emissions_kg_co2e?.toLocaleString() || 0} kg
                          </p>
                          <p className="text-xs text-gray-500">
                            {(customer.total_emissions_kg_co2e / 1000 || 0).toFixed(2)} tonnes
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`badge ${getTierColor(customer.subscription_tier)}`}>
                          <FaCrown className="inline mr-1 text-xs" />
                          {customer.subscription_tier || 'Free'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-gray-600">
                            {customer.joined_at ? new Date(customer.joined_at).toLocaleDateString() : 'N/A'}
                          </p>
                          {customer.last_activity && (
                            <p className="text-xs text-gray-400">
                              Last active: {new Date(customer.last_activity).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => handleViewDetails(customer)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="View Details"
                        >
                          <FaEye />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Customer Detail Modal */}
      <CustomerDetailModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedCustomer(null);
        }}
        customer={selectedCustomer}
      />
    </div>
  );
};

export default Customers;