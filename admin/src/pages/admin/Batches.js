import React from 'react';

const Batches = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">📁 Batch Processing</h1>
        <p className="text-gray-600">Manage and monitor batch uploads</p>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="flex items-center justify-between mb-6">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="Search batches..."
                className="input-field max-w-xs"
              />
              <select className="input-field max-w-xs">
                <option value="all">All Status</option>
                <option value="processing">Processing</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>

          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-4">📁</div>
            <p>Batch management coming soon</p>
            <p className="text-sm">This module will allow you to monitor batch uploads and their status</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Batches;