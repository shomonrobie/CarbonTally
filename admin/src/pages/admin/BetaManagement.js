// D:\carbon_ledger\admin\src\pages\admin\BetaManagement.js
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  FaEnvelope, 
  FaUserPlus, 
  FaCheckCircle, 
  FaClock, 
  FaTimesCircle,
  FaSync,
  FaTrash,
  FaSearch,
  FaFilter,
  FaDownload,
  FaEye,
  FaEyeSlash
} from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';

const BetaManagement = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedEmails, setSelectedEmails] = useState([]);
  const [showDebug, setShowDebug] = useState(false);
  const API_URL = process.env.REACT_APP_API_URL || 'https://carbontally-api.onrender.com';

  // Fetch w  aitlist data
  const { data: waitlist, isLoading, refetch } = useQuery({
    queryKey: ['betaWaitlist'],
    queryFn: async () => {
      let query = supabase
        .from('waitlist')
        .select('*')
        .order('created_at', { ascending: false });

      if (filterStatus !== 'all') {
        query = query.eq('status', filterStatus);
      }

      if (searchTerm) {
        query = query.or(`email.ilike.%${searchTerm}%,company_name.ilike.%${searchTerm}%`);
      }

      const { data, error } = await query;
      if (error) throw error;
      return data || [];
    },
  });

  // Fetch email logs
  const { data: emailLogs } = useQuery({
    queryKey: ['emailLogs'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('email_logs')
        .select('*')
        .eq('type', 'beta_confirmation')
        .order('created_at', { ascending: false })
        .limit(100);
      
      if (error) throw error;
      return data || [];
    },
  });

  // Send beta invite mutation
  const sendInviteMutation = useMutation({
    mutationFn: async ({ email, betaCode }) => {
      const response = await fetch(`${API_URL}/api/waitlist/invite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, beta_code: betaCode })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send invite');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('Beta invite sent successfully!');
      queryClient.invalidateQueries(['betaWaitlist']);
      queryClient.invalidateQueries(['emailLogs']);
    },
    onError: (error) => {
      toast.error(`Failed to send invite: ${error.message}`);
    },
  });

  // Add unsubscribe mutation
  const unsubscribeMutation = useMutation({
    mutationFn: async (email) => {
      const response = await fetch(`${API_URL}/api/waitlist/unsubscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to unsubscribe');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('Successfully unsubscribed!');
      queryClient.invalidateQueries(['betaWaitlist']);
    },
    onError: (error) => {
      toast.error(`Failed to unsubscribe: ${error.message}`);
    },
  });

  // Add resubscribe mutation
  const resubscribeMutation = useMutation({
    mutationFn: async (email) => {
      const response = await fetch(`${API_URL}/api/waitlist/resubscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to resubscribe');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('Successfully resubscribed!');
      queryClient.invalidateQueries(['betaWaitlist']);
    },
    onError: (error) => {
      toast.error(`Failed to resubscribe: ${error.message}`);
    },
  });


  // Generate beta code
  const generateBetaCode = () => {
    return `BETA-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
  };

  const handleSendInvite = (email) => {
    const betaCode = generateBetaCode();
    sendInviteMutation.mutate({ email, betaCode });
  };

  const handleResendConfirmation = (email) => {
    resendConfirmationMutation.mutate(email);
  };

  const getEmailStatus = (email) => {
    if (!emailLogs) return { sent: false, error: null };
    const log = emailLogs.find(log => log.email === email);
    if (!log) return { sent: false, error: null };
    return { sent: log.status === 'sent', error: log.error_message };
  };

  const getStatusBadge = (status) => {
    const badges = {
      'pending': <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-700">⏳ Pending</span>,
      'invited': <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-700">📨 Invited</span>,
      'active': <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">✅ Active</span>,
      'rejected': <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-700">❌ Rejected</span>,
    };
    return badges[status] || <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-700">{status}</span>;
  };

  const getEmailStatusBadge = (email) => {
    const status = getEmailStatus(email);
    if (!status.sent && !status.error) {
      return <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-500">⏳ Pending</span>;
    }
    if (status.sent) {
      return <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">✅ Sent</span>;
    }
    return <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-700 cursor-help" title={status.error}>❌ Failed</span>;
  };

  // Stats
  const stats = {
    total: waitlist?.length || 0,
    pending: waitlist?.filter(w => w.status === 'pending').length || 0,
    invited: waitlist?.filter(w => w.status === 'invited').length || 0,
    active: waitlist?.filter(w => w.status === 'active').length || 0,
    emailsSent: emailLogs?.filter(log => log.status === 'sent').length || 0,
    emailsFailed: emailLogs?.filter(log => log.status === 'failed').length || 0,
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading beta management...</p>
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
            <h1 className="text-2xl font-bold text-gray-900">🧪 Beta Management</h1>
            <p className="text-gray-600">Manage beta access requests and invitations</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowDebug(!showDebug)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
            >
              {showDebug ? <FaEyeSlash /> : <FaEye />}
              {showDebug ? 'Hide Debug' : 'Show Debug'}
            </button>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
            >
              <FaSync className={isLoading ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Signups</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600 text-xl">
              <FaUserPlus />
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Pending</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
            </div>
            <div className="w-12 h-12 bg-yellow-50 rounded-lg flex items-center justify-center text-yellow-600 text-xl">
              <FaClock />
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Invited</p>
              <p className="text-2xl font-bold text-blue-600">{stats.invited}</p>
            </div>
            <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600 text-xl">
              <FaEnvelope />
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Beta Users</p>
              <p className="text-2xl font-bold text-green-600">{stats.active}</p>
            </div>
            <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center text-green-600 text-xl">
              <FaCheckCircle />
            </div>
          </div>
        </div>
      </div>

      {/* Email Delivery Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">📧 Emails Sent</span>
            <span className="text-lg font-bold text-green-600">{stats.emailsSent}</span>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">❌ Emails Failed</span>
            <span className="text-lg font-bold text-red-600">{stats.emailsFailed}</span>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">📊 Success Rate</span>
            <span className="text-lg font-bold text-primary-600">
              {stats.emailsSent + stats.emailsFailed > 0 
                ? `${Math.round((stats.emailsSent / (stats.emailsSent + stats.emailsFailed)) * 100)}%`
                : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* Debug Panel */}
      {showDebug && (
        <div className="bg-gray-900 text-gray-300 rounded-xl p-6 mb-8 font-mono text-sm">
          <h3 className="text-green-400 font-bold mb-4">🔍 Debug Information</h3>
          <div className="space-y-2">
            <p><span className="text-gray-500">Total Waitlist:</span> {waitlist?.length || 0}</p>
            <p><span className="text-gray-500">Email Logs:</span> {emailLogs?.length || 0}</p>
            <p><span className="text-gray-500">Last Updated:</span> {new Date().toLocaleString()}</p>
            <details className="mt-2">
              <summary className="cursor-pointer text-blue-400 hover:text-blue-300">View Email Logs</summary>
              <pre className="mt-2 p-4 bg-gray-800 rounded-lg overflow-x-auto max-h-60 text-xs">
                {JSON.stringify(emailLogs?.slice(0, 5) || [], null, 2)}
              </pre>
            </details>
          </div>
        </div>
      )}

      {/* Search and Filter */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-8">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by email or company..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
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
              <option value="invited">📨 Invited</option>
              <option value="active">✅ Active</option>
              <option value="rejected">❌ Rejected</option>
            </select>
            <button
              onClick={() => {
                setSearchTerm('');
                setFilterStatus('all');
              }}
              className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {waitlist?.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center text-gray-500">
                    No beta requests found
                  </td>
                </tr>
              ) : (
                waitlist?.map((entry) => (
                  <tr key={entry.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <span className="font-medium text-gray-900">{entry.email}</span>
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {entry.company_name || '-'}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(entry.status)}
                    </td>
                    <td className="px-6 py-4">
                      {getEmailStatusBadge(entry.email)}
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {entry.source || '-'}
                    </td>
                    <td className="px-6 py-4 text-gray-500 text-sm">
                      {new Date(entry.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                    <div className="flex gap-2 flex-wrap">
                      {entry.status === 'pending' && (
                        <button
                          onClick={() => handleSendInvite(entry.email)}
                          disabled={sendInviteMutation.isPending}
                          className="px-3 py-1 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                        >
                          {sendInviteMutation.isPending ? '⏳' : '📨 Invite'}
                        </button>
                      )}
                      {(entry.status === 'invited' || entry.status === 'pending') && (
                        <button
                          onClick={() => handleResendConfirmation(entry.email)}
                          disabled={resendConfirmationMutation.isPending}
                          className="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                        >
                          🔄 Resend
                        </button>
                      )}
                      {entry.status !== 'unsubscribed' && (
                        <button
                          onClick={() => {
                            if (window.confirm(`Unsubscribe ${entry.email} from the waitlist?`)) {
                              unsubscribeMutation.mutate(entry.email);
                            }
                          }}
                          className="px-3 py-1 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
                        >
                          Unsubscribe
                        </button>
                      )}
                      {entry.status === 'unsubscribed' && (
                        <button
                          onClick={() => {
                            resubscribeMutation.mutate(entry.email);
                          }}
                          className="px-3 py-1 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors"
                        >
                          Resubscribe
                        </button>
                      )}
                      {getEmailStatus(entry.email).error && (
                        <span 
                          className="px-2 py-1 text-sm text-red-600 cursor-help"
                          title={getEmailStatus(entry.email).error}
                        >
                          ⚠️
                        </span>
                      )}
                    </div>
                  </td>

                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default BetaManagement;