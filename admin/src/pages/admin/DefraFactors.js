import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  FaPlus, 
  FaEdit, 
  FaTrash, 
  FaDownload, 
  FaUpload,
  FaSearch,
  FaFilter,
  FaFileImport,
  FaFileExport,
  FaHistory
} from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';
import DefraFactorModal from '../../components/admin/DefraFactorModal';
import ImportDefraModal from '../../components/admin/ImportDefraModal';

const DefraFactors = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [yearFilter, setYearFilter] = useState('all');
  const [selectedFactor, setSelectedFactor] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;
  const queryClient = useQueryClient();

  // Fetch DEFRA factors
  const { data: factorsData, isLoading, refetch } = useQuery({
    queryKey: ['defraFactors', yearFilter, searchTerm, currentPage],
    queryFn: async () => {
      let query = supabase
        .from('defra_conversion_factors')
        .select('*', { count: 'exact' })
        .order('reporting_year', { ascending: false })
        .order('activity_type', { ascending: true });

      if (yearFilter !== 'all') {
        query = query.eq('reporting_year', parseInt(yearFilter));
      }

      if (searchTerm) {
        query = query.ilike('activity_type', `%${searchTerm}%`);
      }

      const start = (currentPage - 1) * pageSize;
      const end = start + pageSize - 1;
      query = query.range(start, end);

      const { data, error, count } = await query;
      if (error) throw error;
      return { data, count };
    },
  });

  // Get available years
  const { data: yearsData } = useQuery({
    queryKey: ['defraYears'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('defra_conversion_factors')
        .select('reporting_year')
        .order('reporting_year', { ascending: false });

      if (error) throw error;
      const years = [...new Set(data.map(item => item.reporting_year))];
      return years;
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const { error } = await supabase
        .from('defra_conversion_factors')
        .delete()
        .eq('id', id);
      if (error) throw error;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['defraFactors']);
      toast.success('DEFRA factor deleted successfully!');
    },
    onError: (error) => {
      toast.error('Failed to delete: ' + error.message);
    },
  });

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this factor? This action cannot be undone.')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  const handleEdit = (factor) => {
    setSelectedFactor(factor);
    setIsModalOpen(true);
  };

  const handleAdd = () => {
    setSelectedFactor(null);
    setIsModalOpen(true);
  };

  const handleExport = () => {
    // Export current view data
    const exportData = factorsData?.data || [];
    if (exportData.length === 0) {
      toast.error('No data to export');
      return;
    }

    // Create CSV
    const headers = ['Activity Type', 'Reporting Year', 'CO2e Multiplier', 'Created At'];
    const csvRows = [headers.join(',')];
    
    exportData.forEach(row => {
      const values = [
        `"${row.activity_type}"`,
        row.reporting_year,
        row.co2e_multiplier,
        row.created_at
      ];
      csvRows.push(values.join(','));
    });

    const csvString = csvRows.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `defra_factors_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    toast.success('Export successful!');
  };

  const totalPages = Math.ceil((factorsData?.count || 0) / pageSize);

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">📊 DEFRA Conversion Factors</h1>
            <p className="text-gray-600">
              Manage UK Government GHG conversion factors for emissions calculations
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleAdd}
              className="btn-primary flex items-center gap-2"
            >
              <FaPlus /> Add Factor
            </button>
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <FaUpload /> Import
            </button>
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
            >
              <FaDownload /> Export
            </button>
          </div>
        </div>
      </div>

      {/* Compliance Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <div className="text-blue-600 text-xl">ℹ️</div>
          <div>
            <h4 className="font-medium text-blue-900">UK GDPR Compliance Note</h4>
            <p className="text-sm text-blue-700">
              All emission calculations must use the correct DEFRA factors for the reporting year. 
              Factors should be updated annually when UK Government releases new conversion factors.
              All changes are logged for audit purposes.
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search activity types..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
              />
            </div>
          </div>

          <select
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
          >
            <option value="all">All Years</option>
            {yearsData?.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>

          <div className="text-sm text-gray-500 flex items-center">
            Showing {factorsData?.data?.length || 0} of {factorsData?.count || 0} factors
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Activity Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reporting Year
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  CO2e Multiplier
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                    </div>
                  </td>
                </tr>
              ) : factorsData?.data?.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-gray-500">
                    No DEFRA factors found. Import or add factors to get started.
                  </td>
                </tr>
              ) : (
                factorsData?.data?.map((factor) => (
                  <tr key={factor.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {factor.activity_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      <span className="badge badge-info">{factor.reporting_year}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-mono font-medium">
                      {factor.co2e_multiplier}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {factor.created_at ? new Date(factor.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleEdit(factor)}
                          className="p-1 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          title="Edit"
                        >
                          <FaEdit />
                        </button>
                        <button
                          onClick={() => handleDelete(factor.id)}
                          className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="Delete"
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

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, factorsData?.count || 0)} of {factorsData?.count || 0} results
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <span className="px-3 py-1 bg-primary-50 text-primary-600 rounded-lg">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <DefraFactorModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedFactor(null);
        }}
        factor={selectedFactor}
        onSuccess={() => {
          queryClient.invalidateQueries(['defraFactors']);
          queryClient.invalidateQueries(['defraYears']);
        }}
      />

      <ImportDefraModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={() => {
          queryClient.invalidateQueries(['defraFactors']);
          queryClient.invalidateQueries(['defraYears']);
        }}
      />
    </div>
  );
};

export default DefraFactors;