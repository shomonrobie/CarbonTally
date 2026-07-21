import React, { useState } from 'react';
import { FaTimes, FaCheck, FaDownload, FaClock, FaExclamationTriangle } from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';

const ReviewModal = ({ isOpen, onClose, review, onApprove, onReject, refetch }) => {
  const [staffNotes, setStaffNotes] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen || !review) return null;

  const handleSaveNote = async () => {
    if (!staffNotes.trim()) {
      toast.error('Please enter some notes');
      return;
    }

    setLoading(true);
    try {
      const { error } = await supabase
        .from('manual_review_queue')
        .update({ staff_notes: staffNotes })
        .eq('id', review.id);

      if (error) throw error;
      toast.success('Notes saved successfully!');
      refetch();
    } catch (error) {
      toast.error('Failed to save notes: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!staffNotes.trim()) {
      toast.error('Please add notes before approving');
      return;
    }
    await onApprove(review.id);
    onClose();
  };

  const handleReject = async () => {
    if (!staffNotes.trim()) {
      toast.error('Please add notes before rejecting');
      return;
    }
    await onReject(review.id);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        {/* Backdrop */}
        <div className="fixed inset-0 bg-black/50" onClick={onClose}></div>

        {/* Modal */}
        <div className="relative bg-white rounded-xl shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
            <div>
              <h2 className="text-xl font-bold text-gray-900">✏️ Review Document</h2>
              <p className="text-sm text-gray-500">{review.file_name || 'Untitled'}</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <FaTimes />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Document Preview */}
              <div className="space-y-4">
                <div className="bg-gray-100 rounded-lg p-4 flex items-center justify-center h-64">
                  <div className="text-center">
                    <div className="text-4xl mb-2">📄</div>
                    <p className="text-gray-500">Document Preview</p>
                    <p className="text-sm text-gray-400">{review.file_name}</p>
                    <button className="mt-2 text-primary-600 hover:text-primary-700 text-sm font-medium">
                      <FaDownload className="inline mr-1" />
                      Download
                    </button>
                  </div>
                </div>

                {/* Customer Notes */}
                {review.customer_notes && (
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
                    <h4 className="text-sm font-medium text-blue-900 mb-1">💬 Customer Notes</h4>
                    <p className="text-sm text-blue-700">{review.customer_notes}</p>
                  </div>
                )}
              </div>

              {/* Extraction Results */}
              <div className="space-y-4">
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                    <h4 className="font-medium text-gray-900">📊 Extraction Results</h4>
                  </div>
                  <div className="p-4">
                    {review.auto_extraction_result ? (
                      <div className="space-y-3">
                        {Object.entries(review.auto_extraction_result).map(([key, value]) => (
                          <div key={key} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                            <span className="text-sm text-gray-600">{key.replace('_', ' ').toUpperCase()}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-gray-900">{String(value)}</span>
                              <span className="badge badge-success">95%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">No extraction data available</p>
                    )}
                  </div>
                </div>

                {/* Issues */}
                {review.extraction_issues && review.extraction_issues.length > 0 && (
                  <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                    <h4 className="text-sm font-medium text-yellow-800 flex items-center gap-2">
                      <FaExclamationTriangle />
                      Issues Found
                    </h4>
                    <ul className="mt-2 space-y-1">
                      {review.extraction_issues.map((issue, index) => (
                        <li key={index} className="text-sm text-yellow-700 flex items-start gap-2">
                          <span className="text-yellow-500">•</span>
                          {issue.message || issue}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Staff Notes */}
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📝 Staff Notes
              </label>
              <div className="flex gap-2">
                <textarea
                  value={staffNotes}
                  onChange={(e) => setStaffNotes(e.target.value)}
                  placeholder="Enter your review notes here..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none resize-none h-20"
                />
                <button
                  onClick={handleSaveNote}
                  disabled={loading}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors h-20"
                >
                  {loading ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>

            {/* Auto-extraction summary */}
            {review.extraction_summary && (
              <div className="mt-4 grid grid-cols-3 gap-4">
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <p className="text-sm text-green-600">Confidence</p>
                  <p className="text-lg font-bold text-green-700">
                    {(review.extraction_summary.confidence_score * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <p className="text-sm text-blue-600">Fields Extracted</p>
                  <p className="text-lg font-bold text-blue-700">
                    {review.extraction_summary.extracted_successfully || 0}/{review.extraction_summary.total_fields || 0}
                  </p>
                </div>
                <div className="bg-yellow-50 rounded-lg p-3 text-center">
                  <p className="text-sm text-yellow-600">Needs Review</p>
                  <p className="text-lg font-bold text-yellow-700">
                    {review.extraction_summary.needs_manual_review || 0}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <FaClock />
              <span>Estimated completion: 24 hours</span>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleReject}
                disabled={loading}
                className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
              >
                <FaTimes className="inline mr-2" />
                Reject
              </button>
              <button
                onClick={handleApprove}
                disabled={loading}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                <FaCheck className="inline mr-2" />
                Approve & Save
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewModal;