import React from 'react';

const Users = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">👥 User Management</h1>
        <p className="text-gray-600">Manage system users and their roles</p>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="flex items-center justify-between mb-6">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="Search users..."
                className="input-field max-w-xs"
              />
              <select className="input-field max-w-xs">
                <option value="all">All Roles</option>
                <option value="admin">Admin</option>
                <option value="staff">Staff</option>
                <option value="user">User</option>
              </select>
            </div>
            <button className="btn-primary">
              + Add User
            </button>
          </div>

          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-4">👥</div>
            <p>User management coming soon</p>
            <p className="text-sm">This module will allow you to manage users, roles, and permissions</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Users;