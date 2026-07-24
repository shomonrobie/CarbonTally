// D:\carbon_ledger\admin\src\pages\admin\GlossaryManagement.js
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FaPlus,
  FaEdit,
  FaTrash,
  FaSearch,
  FaSave,
  FaTimes,
  FaBook,
  FaList,
  FaExclamationTriangle,
} from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'https://carbontally-api.onrender.com';

const GlossaryManagement = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [editingTerm, setEditingTerm] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    term: '',
    definition: '',
    category: '',
    example: '',
    related_terms: '',
  });

  // Fetch glossary terms
  const { data: terms, isLoading, refetch, error: fetchError } = useQuery({
    queryKey: ['glossary'],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_URL}/api/glossary`);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('API Error:', response.status, errorText);
          throw new Error(`API returned ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        if (data.success) {
          return data.data || [];
        }
        throw new Error(data.detail || 'Failed to fetch glossary');
      } catch (err) {
        console.error('Fetch error:', err);
        throw err;
      }
    },
    retry: 2,
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (newTerm) => {
      const response = await fetch(`${API_URL}/api/glossary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTerm),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create term');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('Term created successfully!');
      queryClient.invalidateQueries(['glossary']);
      setShowForm(false);
      resetForm();
    },
    onError: (error) => {
      toast.error(`Failed to create: ${error.message}`);
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, ...term }) => {
      const response = await fetch(`${API_URL}/api/glossary/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(term),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update term');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('Term updated successfully!');
      queryClient.invalidateQueries(['glossary']);
      setEditingTerm(null);
      setShowForm(false);
      resetForm();
    },
    onError: (error) => {
      toast.error(`Failed to update: ${error.message}`);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const response = await fetch(`${API_URL}/api/glossary/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete term');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('Term deleted successfully!');
      queryClient.invalidateQueries(['glossary']);
    },
    onError: (error) => {
      toast.error(`Failed to delete: ${error.message}`);
    },
  });

  const resetForm = () => {
    setFormData({
      term: '',
      definition: '',
      category: '',
      example: '',
      related_terms: '',
    });
  };

  const handleEdit = (term) => {
    setEditingTerm(term);
    setFormData({
      term: term.term,
      definition: term.definition,
      category: term.category || '',
      example: term.example || '',
      related_terms: term.related_terms ? term.related_terms.join(', ') : '',
    });
    setShowForm(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const termData = {
      term: formData.term.trim(),
      definition: formData.definition.trim(),
      category: formData.category.trim() || null,
      example: formData.example.trim() || null,
      related_terms: formData.related_terms
        ? formData.related_terms.split(',').map(s => s.trim()).filter(Boolean)
        : null,
    };

    if (editingTerm) {
      updateMutation.mutate({ id: editingTerm.id, ...termData });
    } else {
      createMutation.mutate(termData);
    }
  };

  const handleDelete = (id, term) => {
    if (window.confirm(`Delete glossary term "${term}"?`)) {
      deleteMutation.mutate(id);
    }
  };

  const filteredTerms = terms?.filter(t =>
    t.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.definition.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Show error state
  if (fetchError) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <FaExclamationTriangle className="text-4xl text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-800 mb-2">Failed to Load Glossary</h3>
          <p className="text-red-600 mb-4">{fetchError.message || 'Please check your connection and try again.'}</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading glossary...</p>
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
            <h1 className="text-2xl font-bold text-gray-900">📚 Glossary Management</h1>
            <p className="text-gray-600">Manage carbon accounting terms and definitions</p>
          </div>
          <button
            onClick={() => {
              setEditingTerm(null);
              resetForm();
              setShowForm(true);
            }}
            className="px-4 py-2 text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
          >
            <FaPlus /> Add Term
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600">
              <FaBook />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Terms</p>
              <p className="text-xl font-bold text-gray-900">{terms?.length || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center text-green-600">
              <FaList />
            </div>
            <div>
              <p className="text-sm text-gray-500">Categories</p>
              <p className="text-xl font-bold text-gray-900">
                {new Set(terms?.map(t => t.category).filter(Boolean)).size || 0}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center text-purple-600">
              <FaSearch />
            </div>
            <div>
              <p className="text-sm text-gray-500">Search Results</p>
              <p className="text-xl font-bold text-gray-900">{filteredTerms?.length || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {editingTerm ? 'Edit Glossary Term' : 'Add New Glossary Term'}
            </h2>
            <button
              onClick={() => {
                setShowForm(false);
                setEditingTerm(null);
                resetForm();
              }}
              className="text-gray-400 hover:text-gray-600"
            >
              <FaTimes />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Term *
                </label>
                <input
                  type="text"
                  value={formData.term}
                  onChange={(e) => setFormData({ ...formData, term: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <input
                  type="text"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  placeholder="e.g., Scope, Reporting, Methodology"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Definition *
              </label>
              <textarea
                value={formData.definition}
                onChange={(e) => setFormData({ ...formData, definition: e.target.value })}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none resize-vertical"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Example
              </label>
              <textarea
                value={formData.example}
                onChange={(e) => setFormData({ ...formData, example: e.target.value })}
                rows={2}
                placeholder="e.g., A company with 10 delivery vans would track diesel consumption under Scope 1."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none resize-vertical"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Related Terms (comma-separated)
              </label>
              <input
                type="text"
                value={formData.related_terms}
                onChange={(e) => setFormData({ ...formData, related_terms: e.target.value })}
                placeholder="e.g., Scope 1, Direct Emissions, Greenhouse Gas"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={createMutation.isPending || updateMutation.isPending}
                className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                <FaSave />
                {editingTerm ? 'Update Term' : 'Create Term'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingTerm(null);
                  resetForm();
                }}
                className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Search */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
        <div className="relative">
          <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search glossary terms..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
          />
        </div>
      </div>

      {/* Terms Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Term
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Definition
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredTerms?.length === 0 ? (
                <tr>
                  <td colSpan="4" className="px-6 py-12 text-center text-gray-500">
                    No glossary terms found
                  </td>
                </tr>
              ) : (
                filteredTerms?.map((term) => (
                  <tr key={term.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <span className="font-medium text-gray-900">{term.term}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-gray-600 line-clamp-2">
                        {term.definition}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {term.category ? (
                        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
                          {term.category}
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(term)}
                          className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        >
                          <FaEdit />
                        </button>
                        <button
                          onClick={() => handleDelete(term.id, term.term)}
                          className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
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

      {/* Footer Stats */}
      <div className="mt-4 text-sm text-gray-500">
        Showing {filteredTerms?.length || 0} of {terms?.length || 0} terms
      </div>
    </div>
  );
};

export default GlossaryManagement;