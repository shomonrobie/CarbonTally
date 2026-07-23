// D:\carbon_ledger\admin\src\components\admin\ReviewWorkflow.js
import React, { useState, useEffect } from 'react';
import { FaTimes, FaSave, FaHistory, FaUserCheck, FaClock, FaFilePdf, FaImage } from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import { startReview, submitReview, getReviewAuditTrail, reassignReview } from '../../services/reviewService';
import toast from 'react-hot-toast';

const ReviewWorkflow = ({ review, onClose, staffMembers, onRefresh }) => {
  const [loading, setLoading] = useState(false);
  const [auditTrail, setAuditTrail] = useState([]);
  const [showAudit, setShowAudit] = useState(false);
  const [formData, setFormData] = useState({
    date: '',
    volume: '',
    fuelType: '',
    site: '',
    notes: ''
  });
  const [staffNotes, setStaffNotes] = useState('');
  const [isStarted, setIsStarted] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setCurrentUser(user);
    };
    getUser();
    loadAuditTrail();
  }, []);

  const loadAuditTrail = async () => {
    try {
      const data = await getReviewAuditTrail(review.id);
      setAuditTrail(data);
    } catch (error) {
      console.error('Failed to load audit trail:', error);
    }
  };

  const handleStartWork = async () => {
    if (!currentUser) return;
    setLoading(true);
    try {
      await startReview(review.id, currentUser.id);
      setIsStarted(true);
      toast.success('Review started!');
      onRefresh();
    } catch (error) {
      toast.error(`Failed to start: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!currentUser) return;
    
    // Validate required fields
    if (!formData.date || !formData.volume || !formData.fuelType) {
      toast.error('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      await submitReview(
        review.id,
        currentUser.id,
        {
          date: formData.date,
          volume: parseFloat(formData.volume),
          fuel_type: formData.fuelType,
          site: formData.site,
          ...formData
        },
        staffNotes
      );
      toast.success('Review completed successfully!');
      onClose();
      onRefresh();
    } catch (error) {
      toast.error(`Failed to submit: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReassign = async (newStaffId) => {
    if (!currentUser) return;
    setLoading(true);
    try {
      await reassignReview(review.id, newStaffId, currentUser.id);
      toast.success('Review reassigned!');
      onRefresh();
      onClose();
    } catch (error) {
      toast.error(`Failed to reassign: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-7xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              {review.file_type === 'PDF' ? <FaFilePdf className="text-red-500" /> : <FaImage className="text-blue-500" />}
              {review.file_name}
            </h2>
            <div className="flex items-center gap-4 mt-1">
              <span className="text-sm text-gray-500">Status: {review.status}</span>
              <span className="text-sm text-gray-500">Priority: {review.priority === 1 ? 'High' : review.priority === 2 ? 'Medium' : 'Low'}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowAudit(!showAudit)}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors flex items-center gap-1"
            >
              <FaHistory /> Audit Trail
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <FaTimes />
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex flex-col lg:flex-row h-[calc(100%-80px)] overflow-hidden">
          {/* Left Panel - PDF/Image Preview */}
          <div className="lg:w-1/2 p-4 border-r border-gray-200 overflow-auto">
            <div className="bg-gray-100 rounded-lg h-full min-h-[400px] flex items-center justify-center">
              {review.file_url ? (
                review.file_type === 'PDF' ? (
                  <iframe
                    src={review.file_url}
                    className="w-full h-full min-h-[500px] rounded-lg"
                    title="PDF Preview"
                  />
                ) : (
                  <img
                    src={review.file_url}
                    alt="Document preview"
                    className="max-h-full object-contain rounded-lg"
                  />
                )
              ) : (
                <div className="text-center text-gray-400">
                  <FaFilePdf className="text-6xl mx-auto mb-4" />
                  <p>Preview not available</p>
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - Data Entry Form */}
          <div className="lg:w-1/2 p-6 overflow-auto">
            <div className="space-y-6">
              {/* Status & Actions */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${review.status === 'completed' ? 'text-green-600' : 'text-gray-600'}`}>
                    Status: {review.status}
                  </span>
                </div>
                <div className="flex gap-2">
                  {review.status === 'assigned' && !isStarted && (
                    <button
                      onClick={handleStartWork}
                      disabled={loading}
                      className="px-4 py-2 text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
                    >
                      <FaClock className="inline mr-1" />
                      Start Work
                    </button>
                  )}
                  {(review.status === 'in_progress' || isStarted) && (
                    <button
                      onClick={handleSubmit}
                      disabled={loading}
                      className="px-4 py-2 text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                    >
                      <FaSave className="inline mr-1" />
                      Submit Review
                    </button>
                  )}
                  {review.status === 'assigned' && (
                    <select
                      onChange={(e) => handleReassign(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      disabled={loading}
                    >
                      <option value="">Reassign to...</option>
                      {staffMembers?.map((staff) => (
                        <option key={staff.user_id} value={staff.user_id}>
                          {staff.first_name} {staff.last_name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>

              {/* Data Entry Form */}
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-700">Data Entry</h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                    disabled={review.status === 'completed' || loading}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Volume <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.volume}
                    onChange={(e) => setFormData({ ...formData, volume: e.target.value })}
                    placeholder="Enter volume (e.g., 45.2)"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                    disabled={review.status === 'completed' || loading}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Fuel/Energy Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={formData.fuelType}
                    onChange={(e) => setFormData({ ...formData, fuelType: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                    disabled={review.status === 'completed' || loading}
                  >
                    <option value="">Select fuel type...</option>
                    <option value="Diesel">Diesel</option>
                    <option value="Petrol">Petrol</option>
                    <option value="AdBlue">AdBlue</option>
                    <option value="Electricity">Electricity</option>
                    <option value="Natural Gas">Natural Gas</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Site/Facility
                  </label>
                  <input
                    type="text"
                    value={formData.site}
                    onChange={(e) => setFormData({ ...formData, site: e.target.value })}
                    placeholder="Enter site or facility name"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                    disabled={review.status === 'completed' || loading}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Staff Notes
                  </label>
                  <textarea
                    value={staffNotes}
                    onChange={(e) => setStaffNotes(e.target.value)}
                    placeholder="Add notes about this review..."
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none resize-none"
                    disabled={review.status === 'completed' || loading}
                  />
                </div>
              </div>

              {/* Auto-extraction result preview */}
              {review.auto_extraction_result && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Auto-Extraction Results</h4>
                  <pre className="text-xs text-gray-600 overflow-auto max-h-40">
                    {JSON.stringify(review.auto_extraction_result, null, 2)}
                  </pre>
                </div>
              )}

              {/* Audit Trail */}
              {showAudit && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg max-h-60 overflow-auto">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Audit Trail</h4>
                  {auditTrail.length === 0 ? (
                    <p className="text-sm text-gray-500">No audit entries yet</p>
                  ) : (
                    <div className="space-y-2">
                      {auditTrail.map((entry) => (
                        <div key={entry.id} className="text-sm border-b border-gray-200 pb-2">
                          <div className="flex justify-between">
                            <span className="font-medium">
                              {entry.action} {entry.assignee && `to ${entry.assignee.email}`}
                            </span>
                            <span className="text-gray-500 text-xs">
                              {new Date(entry.created_at).toLocaleString()}
                            </span>
                          </div>
                          <div className="text-gray-600 text-xs">
                            By: {entry.performer?.email || 'Unknown'}
                          </div>
                          {entry.note && (
                            <div className="text-gray-500 text-xs mt-1">{entry.note}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewWorkflow;