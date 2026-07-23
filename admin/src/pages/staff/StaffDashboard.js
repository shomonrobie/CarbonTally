// D:\carbon_ledger\admin\src\pages\staff\StaffDashboard.js
import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FaClock, FaCheckCircle, FaUserCheck, FaFileAlt } from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import ReviewWorkflow from '../../components/admin/ReviewWorkflow';
import { getStaffProfile } from '../../services/reviewService';
import toast from 'react-hot-toast';

const StaffDashboard = () => {
  const [selectedReview, setSelectedReview] = useState(null);
  const [showWorkflow, setShowWorkflow] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setCurrentUser(user);
    };
    getUser();
  }, []);

  // Fetch reviews assigned to current user
  // In StaffDashboard.js - Update the review query
  const { data: myReviews, isLoading, refetch } = useQuery({
    queryKey: ['myReviews', currentUser?.id],
    queryFn: async () => {
        if (!currentUser) return [];
        
        // ✅ Remove the organization relation
        const { data, error } = await supabase
        .from('manual_review_queue')
        .select('*')  // Select all columns, no relations
        .eq('assigned_to', currentUser.id)
        .order('priority', { ascending: false })
        .order('created_at', { ascending: false });

        if (error) throw error;
        return data || [];
    },
    enabled: !!currentUser,
    });

  // Fetch staff profile
  const { data: staffProfile } = useQuery({
    queryKey: ['staffProfile', currentUser?.id],
    queryFn: () => getStaffProfile(currentUser?.id),
    enabled: !!currentUser,
  });

  const getStatusBadge = (status) => {
    const badges = {
      'pending': <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-700">⏳ Pending</span>,
      'assigned': <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-700">📌 Assigned</span>,
      'in_progress': <span className="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-700">🔄 In Progress</span>,
      'completed': <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">✅ Completed</span>,
    };
    return badges[status] || <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-700">{status}</span>;
  };

  const handleStartWork = (review) => {
    setSelectedReview(review);
    setShowWorkflow(true);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your tasks...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">👋 My Dashboard</h1>
        <p className="text-gray-600">Welcome back, {staffProfile?.first_name || 'Staff'}! Here are your assigned reviews.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Assigned</p>
              <p className="text-2xl font-bold text-blue-600">
                {myReviews?.filter(r => r.status === 'assigned').length || 0}
              </p>
            </div>
            <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600">
              <FaUserCheck />
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">In Progress</p>
              <p className="text-2xl font-bold text-purple-600">
                {myReviews?.filter(r => r.status === 'in_progress').length || 0}
              </p>
            </div>
            <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center text-purple-600">
              <FaClock />
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Completed</p>
              <p className="text-2xl font-bold text-green-600">
                {myReviews?.filter(r => r.status === 'completed').length || 0}
              </p>
            </div>
            <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center text-green-600">
              <FaCheckCircle />
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Reviews</p>
              <p className="text-2xl font-bold text-gray-700">
                {staffProfile?.total_reviews_completed || 0}
              </p>
            </div>
            <div className="w-10 h-10 bg-gray-50 rounded-lg flex items-center justify-center text-gray-600">
              <FaFileAlt />
            </div>
          </div>
        </div>
      </div>

      {/* My Reviews Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-700">My Assigned Reviews</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Organization</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {myReviews?.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                    No reviews assigned to you yet
                  </td>
                </tr>
              ) : (
                myReviews?.map((review) => (
                  <tr key={review.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <span className="font-medium text-gray-900">{review.file_name}</span>
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {review.organization?.name || 'N/A'}
                    </td>
                    <td className="px-6 py-4">
                      {review.priority === 1 ? '🔴 High' : review.priority === 2 ? '🟠 Medium' : '🟢 Low'}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(review.status)}
                    </td>
                    <td className="px-6 py-4 text-gray-500 text-sm">
                      {new Date(review.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      {(review.status === 'assigned' || review.status === 'in_progress') && (
                        <button
                          onClick={() => handleStartWork(review)}
                          className="px-3 py-1 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
                        >
                          {review.status === 'assigned' ? 'Start Review' : 'Continue'}
                        </button>
                      )}
                      {review.status === 'completed' && (
                        <span className="text-sm text-green-600">✅ Completed</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Workflow Modal */}
      {showWorkflow && selectedReview && (
        <ReviewWorkflow
          review={selectedReview}
          onClose={() => {
            setShowWorkflow(false);
            refetch();
          }}
          staffMembers={[]}
          onRefresh={() => {
            refetch();
          }}
        />
      )}
    </div>
  );
};

export default StaffDashboard;