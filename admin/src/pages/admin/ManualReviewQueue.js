import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FaEye,
  FaSync,
  FaFilePdf,
  FaImage,
  FaClock,
  FaExclamationTriangle,
  FaCheckCircle,
  FaArrowLeft,
  FaSave,
  FaLayerGroup,
  FaCalendarAlt,
  FaBuilding,
  FaCar,
  FaBolt
} from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';
import ReviewExtractionModal from '../../components/admin/ReviewExtractionModal';

const ManualReviewQueue = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedItem, setSelectedItem] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Fetch queue items
  const { data: queue, isLoading, refetch } = useQuery({
    queryKey: ['manualReviewQueue'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('manual_review_queue')
        .select('*')
        .eq('status', 'pending')
        .order('priority', { ascending: false })
        .order('created_at', { ascending: true });

      if (error) {
        console.error('Error fetching queue:', error);
        toast.error('Failed to load review queue');
        throw error;
      }

      return data || [];
    },
  });

  // Get priority label and color
  const getPriorityInfo = (priority) => {
    const priorities = {
      2: { label: '🔥 Urgent', color: 'badge-danger' },
      1: { label: '⚠️ High', color: 'badge-warning' },
      0: { label: '📄 Normal', color: 'badge-info' },
    };
    return priorities[priority] || priorities[0];
  };

  const getStatusInfo = (status) => {
    const statuses = {
      pending: { label: 'Pending', color: 'badge-warning' },
      in_progress: { label: 'In Progress', color: 'badge-info' },
      completed: { label: 'Completed', color: 'badge-success' },
      rejected: { label: 'Rejected', color: 'badge-danger' },
    };
    return statuses[status] || statuses.pending;
  };

  const handleReview = (item) => {
    setSelectedItem(item);
    setIsModalOpen(true);
  };

  const handleRefresh = () => {
    refetch();
    toast.success('Queue refreshed');
  };

  // Count items by priority
  const urgentCount = queue?.filter(item => item.priority === 2).length || 0;
  const highCount = queue?.filter(item => item.priority === 1).length || 0;
  const normalCount = queue?.filter(item => item.priority === 0).length || 0;

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">📋 Manual Review Queue</h1>
            <p className="text-gray-600">Review and process documents that require manual extraction</p>
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
          </div>
        </div>
      </div>

      {/* Priority Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-red-700 font-medium">Urgent</p>
              <p className="text-2xl font-bold text-red-600">{urgentCount}</p>
            </div>
            <FaExclamationTriangle className="text-2xl text-red-500" />
          </div>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-yellow-700 font-medium">High Priority</p>
              <p className="text-2xl font-bold text-yellow-600">{highCount}</p>
            </div>
            <FaClock className="text-2xl text-yellow-500" />
          </div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-700 font-medium">Normal</p>
              <p className="text-2xl font-bold text-blue-600">{normalCount}</p>
            </div>
            <FaCheckCircle className="text-2xl text-blue-500" />
          </div>
        </div>
      </div>

      {/* GDPR Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <div className="text-blue-600 text-xl">🔒</div>
          <div>
            <h4 className="font-medium text-blue-900">GDPR Compliance</h4>
            <p className="text-sm text-blue-700">
              All documents contain potentially sensitive data. Access is logged and restricted 
              to authorized personnel only. Customer data must be handled with care.
            </p>
          </div>
        </div>
      </div>

      {/* Queue Table */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900">Pending Reviews</h3>
            <p className="text-sm text-gray-500">
              {queue?.length || 0} items awaiting review
            </p>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Search files..."
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none text-sm"
            />
          </div>
        </div>
        <div className="card-body p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading queue...</p>
              </div>
            </div>
          ) : queue?.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">🎉</div>
              <p className="text-gray-500 font-medium">All caught up!</p>
              <p className="text-sm text-gray-400">No pending manual reviews at this time</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Document
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Data Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Priority
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Submitted
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {queue?.map((item) => {
                    const priorityInfo = getPriorityInfo(item.priority);
                    const statusInfo = getStatusInfo(item.status);
                    
                    return (
                      <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4">
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {item.file_name}
                            </p>
                            {item.batch_id && (
                              <p className="text-xs text-gray-500 flex items-center gap-1">
                                <FaLayerGroup className="text-xs" />
                                Batch: {item.customer_notes?.split('Batch upload: ')[1]?.split('. File:')[0] || 'Batch'}
                              </p>
                            )}
                            {item.customer_notes?.includes('📝 CUSTOMER NOTE:') && (
                              <p className="text-xs text-yellow-600 flex items-center gap-1 mt-1">
                                <FaExclamationTriangle className="text-xs" />
                                Has customer instructions
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`badge ${item.file_type === 'PDF' ? 'badge-info' : 'badge-secondary'}`}>
                            {item.file_type === 'PDF' ? (
                              <FaFilePdf className="inline mr-1" />
                            ) : (
                              <FaImage className="inline mr-1" />
                            )}
                            {item.file_type}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="badge badge-gray capitalize">
                            {item.data_type || 'Unknown'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`badge ${priorityInfo.color}`}>
                            {priorityInfo.label}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`badge ${statusInfo.color}`}>
                            {statusInfo.label}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div>
                            <p className="text-sm text-gray-600">
                              {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'N/A'}
                            </p>
                            <p className="text-xs text-gray-400">
                              {item.created_at ? new Date(item.created_at).toLocaleTimeString() : ''}
                            </p>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => handleReview(item)}
                            className="px-3 py-1.5 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2 ml-auto"
                          >
                            <FaEye className="text-xs" />
                            Review
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Review Modal */}
      {selectedItem && (
        <ReviewExtractionModal
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedItem(null);
            refetch();
          }}
          item={selectedItem}
        />
      )}
    </div>
  );
};

export default ManualReviewQueue;