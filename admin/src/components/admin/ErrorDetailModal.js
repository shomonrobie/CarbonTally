// src/components/admin/ErrorDetailModal.js
import React from 'react';
import { FaTimes, FaExclamationTriangle, FaExclamationCircle, FaInfoCircle, FaCopy } from 'react-icons/fa';

const ErrorDetailModal = ({ isOpen, onClose, error }) => {
  if (!isOpen || !error) return null;

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return <FaExclamationCircle className="text-red-500 text-2xl" />;
      case 'warning': return <FaExclamationTriangle className="text-yellow-500 text-2xl" />;
      case 'info': return <FaInfoCircle className="text-blue-500 text-2xl" />;
      default: return <FaInfoCircle className="text-gray-500 text-2xl" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50';
      case 'warning': return 'border-yellow-500 bg-yellow-50';
      case 'info': return 'border-blue-500 bg-blue-50';
      default: return 'border-gray-300 bg-gray-50';
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
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
            <div className="flex items-center gap-3">
              {getSeverityIcon(error.severity)}
              <div>
                <h2 className="text-xl font-bold text-gray-900">Error Details</h2>
                <p className="text-sm text-gray-500">{error.field || 'Extraction Error'}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <FaTimes />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 space-y-4">
            {/* Message */}
            <div className={`p-4 rounded-lg border ${getSeverityColor(error.severity)}`}>
              <p className="text-sm font-medium">{error.message}</p>
            </div>

            {/* Metadata */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Severity</p>
                <p className="text-sm font-medium capitalize">{error.severity}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Type</p>
                <p className="text-sm font-mono">{error.type || 'N/A'}</p>
              </div>
              {error.field && (
                <div className="col-span-2">
                  <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Field</p>
                  <p className="text-sm font-mono">{error.field}</p>
                </div>
              )}
              {error.value !== undefined && (
                <div className="col-span-2">
                  <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Value</p>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">{String(error.value)}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Technical Details */}
            {error.technical_details && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Technical Details</p>
                  <button
                    onClick={() => copyToClipboard(error.technical_details)}
                    className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    <FaCopy className="text-xs" />
                    Copy
                  </button>
                </div>
                <div className="bg-gray-900 rounded-lg p-3 overflow-x-auto">
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap break-words">
                    {error.technical_details}
                  </pre>
                </div>
              </div>
            )}

            {/* Full Error Data */}
            <details>
              <summary className="text-sm font-medium text-gray-700 cursor-pointer hover:text-gray-900">
                Full Error Data
              </summary>
              <div className="mt-2 bg-gray-900 rounded-lg p-3 overflow-x-auto max-h-60">
                <pre className="text-xs text-gray-300 whitespace-pre-wrap break-words">
                  {JSON.stringify(error, null, 2)}
                </pre>
              </div>
            </details>
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

export default ErrorDetailModal;