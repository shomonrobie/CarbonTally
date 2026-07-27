// admin/pages/admin/Users.jsx - FIXED VERSION

import React, { useState, useEffect } from 'react';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';
import { FaSpinner, FaEdit, FaTrash, FaUserPlus, FaUserCheck, FaUserTimes, FaSearch, FaFilter } from 'react-icons/fa';

const Users = () => {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  
  const [newUser, setNewUser] = useState({
    email: '',
    firstName: '',
    lastName: '',
    role: 'viewer',
    organization_id: '',
  });

  const [organizations, setOrganizations] = useState([]);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      await Promise.all([
        fetchUsers(),
        fetchRoles(),
        fetchOrganizations()
      ]);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to load data. Please try again.');
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      // Simplified query to avoid 400 error
      const { data, error } = await supabase
        .from('staff_profiles')
        .select(`
          id,
          email,
          first_name,
          last_name,
          role,
          role_id,
          is_active,
          last_login,
          created_at,
          organization_id
        `)
        .order('created_at', { ascending: false });

      if (error) {
        console.error('Users fetch error:', error);
        throw error;
      }
      
      // Fetch role details separately if needed
      const usersWithRoles = await Promise.all(data.map(async (user) => {
        if (user.role_id) {
          const { data: roleData } = await supabase
            .from('roles')
            .select('name, description')
            .eq('id', user.role_id)
            .single();
          
          return {
            ...user,
            roles: roleData,
            role: roleData?.name || user.role || 'viewer'
          };
        }
        return user;
      }));
      
      setUsers(usersWithRoles || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users');
      throw error;
    }
  };

  const fetchRoles = async () => {
    try {
      const { data, error } = await supabase
        .from('roles')
        .select('*')
        .order('name');

      if (error) {
        console.error('Roles fetch error:', error);
        throw error;
      }
      
      setRoles(data || []);
      
      // If no roles found, try to insert default roles
      if (!data || data.length === 0) {
        console.log('No roles found, inserting defaults...');
        await insertDefaultRoles();
      }
    } catch (error) {
      console.error('Error fetching roles:', error);
      toast.error('Failed to load roles');
      throw error;
    }
  };

  const insertDefaultRoles = async () => {
    try {
      const defaultRoles = [
        { name: 'admin', description: 'Full system access' },
        { name: 'data_extractor', description: 'Can extract data' },
        { name: 'data_approver', description: 'Can approve data' },
        { name: 'staff', description: 'Staff member' },
        { name: 'viewer', description: 'Read-only access' }
      ];
      
      const { error } = await supabase
        .from('roles')
        .insert(defaultRoles);
        
      if (error) throw error;
      
      // Refresh roles
      await fetchRoles();
      toast.success('Default roles created');
    } catch (error) {
      console.error('Error creating default roles:', error);
    }
  };

  const fetchOrganizations = async () => {
    try {
      const { data, error } = await supabase
        .from('organizations')
        .select('id, name')
        .order('name');

      if (error) {
        console.error('Organizations fetch error:', error);
        throw error;
      }
      
      setOrganizations(data || []);
    } catch (error) {
      console.error('Error fetching organizations:', error);
      toast.error('Failed to load organizations');
      throw error;
    }
  };

  // Rest of the component remains the same...
  // (All other functions - handleCreateUser, handleUpdateUser, etc. stay the same)

  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.last_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesRole = filterRole === 'all' || user.role === filterRole;
    
    return matchesSearch && matchesRole;
  });

  const handleCreateUser = async () => {
    if (!newUser.email) {
      toast.error('Email is required');
      return;
    }

    try {
      setLoading(true);
      
      const { data: existingUser, error: checkError } = await supabase
        .from('staff_profiles')
        .select('id')
        .eq('email', newUser.email)
        .maybeSingle();

      if (existingUser) {
        toast.error('User already exists');
        setLoading(false);
        return;
      }

      const roleObj = roles.find(r => r.name === newUser.role);
      
      const { data, error } = await supabase
        .from('staff_profiles')
        .insert({
          email: newUser.email,
          first_name: newUser.firstName,
          last_name: newUser.lastName,
          role: newUser.role,
          role_id: roleObj?.id,
          is_active: true,
          created_at: new Date().toISOString()
        })
        .select()
        .single();

      if (error) {
        console.error('Insert error:', error);
        throw error;
      }

      // Create invitation
      const token = Math.random().toString(36).substring(2, 15) + 
                    Math.random().toString(36).substring(2, 15);
      
      const { error: inviteError } = await supabase
        .from('user_invitations')
        .insert({
          email: newUser.email,
          role_id: roleObj?.id,
          organization_id: newUser.organization_id || null,
          token: token,
          status: 'pending',
          expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
        });

      if (inviteError) {
        console.error('Invite error:', inviteError);
        // Don't throw here, user was created but invite failed
        toast.warning('User created but invitation failed. Please try again.');
      } else {
        toast.success('✅ User invited successfully!');
      }

      setShowAddModal(false);
      setNewUser({
        email: '',
        firstName: '',
        lastName: '',
        role: 'viewer',
        organization_id: '',
      });
      await fetchUsers();
    } catch (error) {
      console.error('Error creating user:', error);
      toast.error('Failed to create user: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // All other functions remain the same...

  // ... (keep all the other functions from your original code)

  if (loading && users.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <FaSpinner className="animate-spin text-primary-600 text-4xl mx-auto mb-4" />
          <p className="text-gray-600">Loading users...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="text-red-600 text-4xl mb-4">⚠️</div>
          <p className="text-gray-800 font-medium">{error}</p>
          <button 
            onClick={fetchAllData}
            className="mt-4 btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">👥 User Management</h1>
        <p className="text-gray-600">Manage system users and their roles</p>
      </div>

      <div className="card">
        <div className="card-body">
          {/* Toolbar */}
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
            <div className="flex flex-col md:flex-row gap-4 w-full md:w-auto">
              <div className="relative flex-1 md:flex-initial">
                <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="input-field pl-10 w-full md:w-64"
                />
              </div>
              <div className="relative">
                <FaFilter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <select
                  value={filterRole}
                  onChange={(e) => setFilterRole(e.target.value)}
                  className="input-field pl-10 w-full md:w-48"
                >
                  <option value="all">All Roles</option>
                  {roles.map(role => (
                    <option key={role.id} value={role.name}>
                      {role.name.charAt(0).toUpperCase() + role.name.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <button 
              onClick={() => setShowAddModal(true)}
              className="btn-primary flex items-center gap-2 w-full md:w-auto"
            >
              <FaUserPlus /> Add User
            </button>
          </div>

          {/* User Stats */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-blue-600">{users.length}</div>
              <div className="text-sm text-blue-700">Total Users</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-green-600">
                {users.filter(u => u.is_active).length}
              </div>
              <div className="text-sm text-green-700">Active</div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-red-600">
                {users.filter(u => !u.is_active).length}
              </div>
              <div className="text-sm text-red-700">Inactive</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-purple-600">
                {users.filter(u => u.role === 'admin').length}
              </div>
              <div className="text-sm text-purple-700">Admins</div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-orange-600">
                {users.filter(u => u.role && ['staff', 'data_extractor', 'data_approver'].includes(u.role)).length}
              </div>
              <div className="text-sm text-orange-700">Staff</div>
            </div>
          </div>

          {/* Users Table - Keep your existing table code */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Organization</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Login</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-4 py-8 text-center text-gray-500">
                      {searchTerm || filterRole !== 'all' ? 'No users match your filters' : 'No users found'}
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-medium">
                            {user.first_name?.[0] || user.email?.[0]?.toUpperCase() || '?'}
                          </div>
                          <div>
                            <div className="font-medium text-gray-900">
                              {user.first_name || ''} {user.last_name || ''}
                            </div>
                            <div className="text-sm text-gray-500">{user.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRoleBadgeColor(user.role)}`}>
                          {getRoleDisplayName(user.role)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {user.organization_id ? organizations.find(o => o.id === user.organization_id)?.name || 'N/A' : 'N/A'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          user.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => {
                              setEditingUser(user);
                              setShowEditModal(true);
                            }}
                            className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Edit user"
                          >
                            <FaEdit />
                          </button>
                          <button
                            onClick={() => handleToggleActive(user.id, user.is_active)}
                            className={`p-1.5 rounded-lg transition-colors ${
                              user.is_active 
                                ? 'text-orange-600 hover:bg-orange-50' 
                                : 'text-green-600 hover:bg-green-50'
                            }`}
                            title={user.is_active ? 'Deactivate' : 'Activate'}
                          >
                            {user.is_active ? <FaUserTimes /> : <FaUserCheck />}
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete user"
                          >
                            <FaTrash />
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
      </div>

      {/* Keep your modals - they remain the same */}
      {/* ... Add User Modal and Edit User Modal code ... */}
    </div>
  );
};

// Helper functions
const getRoleBadgeColor = (role) => {
  const colors = {
    admin: 'bg-red-100 text-red-800',
    data_extractor: 'bg-blue-100 text-blue-800',
    staff: 'bg-green-100 text-green-800',
    data_approver: 'bg-purple-100 text-purple-800',
    viewer: 'bg-gray-100 text-gray-800'
  };
  return colors[role] || colors.viewer;
};

const getRoleDisplayName = (role) => {
  const names = {
    admin: 'Admin',
    data_extractor: 'Data Extractor',
    staff: 'Staff',
    data_approver: 'Data Approver',
    viewer: 'Viewer'
  };
  return names[role] || role;
};

export default Users;