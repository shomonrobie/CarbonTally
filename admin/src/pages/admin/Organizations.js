import React from 'react';

const Organizations = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">🏢 Organizations</h1>
        <p className="text-gray-600">Manage organizations and their settings</p>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="flex items-center justify-between mb-6">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="Search organizations..."
                className="input-field max-w-xs"
              />
              <select className="input-field max-w-xs">
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            <button className="btn-primary">
              + Add Organization
            </button>
          </div>

          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-4">🏢</div>
            <p>Organization management coming soon</p>
            <p className="text-sm">This module will allow you to manage organizations, their members, and settings</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Organizations;