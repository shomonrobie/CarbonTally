// D:\carbon_ledger\admin\src\pages\admin\ReviewAssignment.js
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  FaUserPlus, 
  FaCheckCircle, 
  FaClock, 
  FaUser, 
  FaFilePdf, 
  FaImage,
  FaEye,
  FaEdit,
  FaHistory,
  FaTimes,
  FaUserCheck,
  FaFileAlt,
  FaCalendarAlt
} from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import { 
  fetchStaffMembers, 
  assignReviewToStaff,
  startReview,
  submitReview,
  getReviewAuditTrail,
  reassignReview,
  getStaffProfile
} from '../../services/reviewService';
import toast from 'react-hot-toast';
import ReviewWorkflow from '../../components/admin/ReviewWorkflow';

const ReviewAssignment = () => {
  const queryClient = useQueryClient();
  const [selectedReview, setSelectedReview] = useState(null);
  const [showAssignmentModal, setShowAssignmentModal] = useState(false);
  const [showWorkflowModal, setShowWorkflowModal] = useState(false);
  const [selectedStaff, setSelectedStaff] = useState('');
  const [filterStatus, setFilterStatus] = useState('pending');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Fetch all pending/assigned reviews
  const { data: reviews, isLoading, refetch } = useQuery({
    queryKey: ['reviews', filterStatus],
    queryFn: async () => {
      let query = supabase
        .from('manual_review_queue')
        .select(`
          *,
          organization:organization_id (name),
          assigned_to_user:assigned_to (email),
          assigned_by_user:assigned_by (email),
          completed_by_user:completed_by (email)
        `)
        .order('priority', { ascending: false })
        .order('created_at', { ascending: false });

      if (filterStatus !== 'all') {
        query = query.eq('status', filterStatus);
      }

      if (searchTerm) {
        query = query.or(`file_name.ilike.%${searchTerm}%,customer_notes.ilike.%${searchTerm}%`);
      }

      const { data, error } = await query;
      if (error) throw error;
      return data || [];
    },
  });

  // Fetch staff members
 const { data: staffMembers } = useQuery({
    queryKey: ['staffMembers'],
    queryFn: async () => {
        // ✅ Remove the auth_users relation
        const { data, error } = await supabase
        .from('staff_profiles')
        .select('*')  // Just select all columns, no relation
        .eq('is_active', true)
        .order('first_name', { ascending: true });

        if (error) throw error;
        return data || [];
    },
    });

  // Assign review mutation
  const assignMutation = useMutation({
    mutationFn: ({ reviewId, staffUserId }) => 
      assignReviewToStaff(reviewId, staffUserId, supabase.auth.user()?.id),
    onSuccess: () => {
      toast.success('Review assigned successfully!');
      queryClient.invalidateQueries(['reviews']);
      setShowAssignmentModal(false);
      setSelectedStaff('');
    },
    onError: (error) => {
      toast.error(`Failed to assign: ${error.message}`);
    },
  });

  const getStatusBadge = (status) => {
    const badges = {
      'pending': <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-700">⏳ Pending</span>,
      'assigned': <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-700">📌 Assigned</span>,
      'in_progress': <span className="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-700">🔄 In Progress</span>,
      'completed': <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">✅ Completed</span>,
      'rejected': <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-700">❌ Rejected</span>,
    };
    return badges[status] || <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-700">{status}</span>;
  };

  const getPriorityBadge = (priority) => {
    if (priority === 1) {
      return <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-700">🔴 High</span>;
    } else if (priority === 2) {
      return <span className="px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-700">🟠 Medium</span>;
    }
    return <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-700">🟢 Low</span>;
  };

  const handleAssign = (reviewId) => {
    setSelectedReview(reviewId);
    setShowAssignmentModal(true);
  };

  const handleAssignSubmit = () => {
    if (!selectedStaff) {
      toast.error('Please select a staff member');
      return;
    }
    assignMutation.mutate({ 
      reviewId: selectedReview, 
      staffUserId: selectedStaff 
    });
  };

  const handleWorkflow = (review) => {
    setSelectedReview(review);
    setShowWorkflowModal(true);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading reviews...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">📋 Review Assignment</h1>
            <p className="text-gray-600">Assign and manage manual review tasks for staff</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => refetch()}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Pending</p>
              <p className="text-2xl font-bold text-yellow-600">
                {reviews?.filter(r => r.status === 'pending').length || 0}
              </p>
            </div>
            <div className="w-10 h-10 bg-yellow-50 rounded-lg flex items-center justify-center text-yellow-600">
              <FaClock />
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Assigned</p>
              <p className="text-2xl font-bold text-blue-600">
                {reviews?.filter(r => r.status === 'assigned').length || 0}
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
                {reviews?.filter(r => r.status === 'in_progress').length || 0}
              </p>
            </div>
            <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center text-purple-600">
              <FaEdit />
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Completed</p>
              <p className="text-2xl font-bold text-green-600">
                {reviews?.filter(r => r.status === 'completed').length || 0}
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
              <p className="text-sm text-gray-500">Total</p>
              <p className="text-2xl font-bold text-gray-700">{reviews?.length || 0}</p>
            </div>
            <div className="w-10 h-10 bg-gray-50 rounded-lg flex items-center justify-center text-gray-600">
              <FaFileAlt />
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-8">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="Search by file name or notes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-4 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            >
              <option value="all">All Status</option>
              <option value="pending">⏳ Pending</option>
              <option value="assigned">📌 Assigned</option>
              <option value="in_progress">🔄 In Progress</option>
              <option value="completed">✅ Completed</option>
              <option value="rejected">❌ Rejected</option>
            </select>
          </div>
        </div>
      </div>

      {/* Reviews Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Organization</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assigned To</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {reviews?.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center text-gray-500">
                    No reviews found
                  </td>
                </tr>
              ) : (
                reviews?.map((review) => (
                  <tr key={review.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {review.file_type === 'PDF' ? (
                          <FaFilePdf className="text-red-500" />
                        ) : (
                          <FaImage className="text-blue-500" />
                        )}
                        <span className="font-medium text-gray-900 truncate max-w-[150px]">
                          {review.file_name}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {review.organization?.name || 'N/A'}
                    </td>
                    <td className="px-6 py-4">
                      {getPriorityBadge(review.priority)}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(review.status)}
                    </td>
                    <td className="px-6 py-4">
                      {review.assigned_to_user?.email ? (
                        <span className="text-sm text-gray-700">
                          {review.assigned_to_user.email}
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400">Unassigned</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-gray-500 text-sm">
                      {new Date(review.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        {(review.status === 'pending' || review.status === 'assigned') && (
                          <button
                            onClick={() => handleAssign(review.id)}
                            className="px-3 py-1 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
                          >
                            <FaUserPlus className="inline mr-1" />
                            Assign
                          </button>
                        )}
                        <button
                          onClick={() => handleWorkflow(review)}
                          className="px-3 py-1 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                        >
                          <FaEye className="inline mr-1" />
                          View
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Assignment Modal */}
      {showAssignmentModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">Assign Review</h2>
              <button
                onClick={() => setShowAssignmentModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <FaTimes />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Staff Member
                </label>
                <select
                  value={selectedStaff}
                  onChange={(e) => setSelectedStaff(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                >
                  <option value="">Select a staff member...</option>
                  {staffMembers?.map((staff) => (
                    <option key={staff.user_id} value={staff.user_id}>
                      {staff.first_name} {staff.last_name} ({staff.email})
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2 pt-4">
                <button
                  onClick={handleAssignSubmit}
                  disabled={assignMutation.isPending}
                  className="flex-1 px-4 py-2 text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
                >
                  {assignMutation.isPending ? 'Assigning...' : 'Assign Review'}
                </button>
                <button
                  onClick={() => setShowAssignmentModal(false)}
                  className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Review Workflow Modal */}
      {showWorkflowModal && selectedReview && (
        <ReviewWorkflow
          review={selectedReview}
          onClose={() => setShowWorkflowModal(false)}
          staffMembers={staffMembers}
          onRefresh={() => {
            refetch();
            queryClient.invalidateQueries(['reviews']);
          }}
        />
      )}
    </div>
  );
};

export default ReviewAssignment;