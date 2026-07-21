import React, { useState, useEffect, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  FaSync,
  FaDownload,
  FaSearch,
  FaFilter,
  FaTimes,
  FaEye,
  FaCode,
  FaExclamationTriangle,
  FaExclamationCircle,
  FaInfoCircle,
  FaCheckCircle,
  FaFilePdf,
  FaImage,
  FaClock,
  FaSort,
  FaSortUp,
  FaSortDown
} from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';
import ErrorDetailModal from '../../components/admin/ErrorDetailModal';

const ExtractionErrorReview = () => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterFileType, setFilterFileType] = useState('all');
  const [filterDataType, setFilterDataType] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');
  const [filterConfidence, setFilterConfidence] = useState('all');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedError, setSelectedError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Fetch queue items
  const { data: queue, isLoading, refetch } = useQuery({
    queryKey: ['extractionErrors'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('manual_review_queue')
        .select('*')
        .eq('status', 'pending')
        .order('priority', { ascending: false })
        .order('created_at', { ascending: true });

      if (error) {
        console.error('Error fetching queue:', error);
        toast.error('Failed to load review queue');
        throw error;
      }

      return data || [];
    },
  });

  // Calculate stats
  const stats = useMemo(() => {
    if (!queue) return { total: 0, critical: 0, warning: 0, lowConfidence: 0, highPriority: 0 };

    let critical = 0;
    let warning = 0;
    let lowConfidence = 0;
    let highPriority = 0;

    queue.forEach(item => {
      const issues = item.auto_extraction_result?.extraction_issues || [];
      const summary = item.auto_extraction_result?.extraction_summary || {};
      
      issues.forEach(issue => {
        if (issue.severity === 'critical') critical++;
        if (issue.severity === 'warning') warning++;
      });

      if (summary.confidence_score && summary.confidence_score < 0.6) {
        lowConfidence++;
      }
      
      if (item.priority >= 1) {
        highPriority++;
      }
    });

    return {
      total: queue.length,
      critical,
      warning,
      lowConfidence,
      highPriority
    };
  }, [queue]);

  // Get unique data types
  const uniqueDataTypes = useMemo(() => {
    if (!queue) return [];
    const types = new Set(queue.map(item => item.data_type));
    return Array.from(types);
  }, [queue]);

  // Filter and sort queue
  const filteredQueue = useMemo(() => {
    if (!queue) return [];

    let filtered = [...queue];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(item =>
        item.file_name.toLowerCase().includes(query) ||
        (item.customer_notes && item.customer_notes.toLowerCase().includes(query)) ||
        item.id.toLowerCase().includes(query)
      );
    }

    // Severity filter
    if (filterSeverity !== 'all') {
      filtered = filtered.filter(item => {
        const issues = item.auto_extraction_result?.extraction_issues || [];
        return issues.some(issue => issue.severity === filterSeverity);
      });
    }

    // File type filter
    if (filterFileType !== 'all') {
      filtered = filtered.filter(item => item.file_type === filterFileType);
    }

    // Data type filter
    if (filterDataType !== 'all') {
      filtered = filtered.filter(item => item.data_type === filterDataType);
    }

    // Priority filter
    if (filterPriority !== 'all') {
      const priority = parseInt(filterPriority);
      filtered = filtered.filter(item => item.priority === priority);
    }

    // Confidence filter
    if (filterConfidence !== 'all') {
      filtered = filtered.filter(item => {
        const summary = item.auto_extraction_result?.extraction_summary || {};
        const score = summary.confidence_score || 0;
        
        switch (filterConfidence) {
          case 'high': return score >= 0.7;
          case 'medium': return score >= 0.4 && score < 0.7;
          case 'low': return score < 0.4;
          default: return true;
        }
      });
    }

    // Sorting
    filtered.sort((a, b) => {
      let aValue, bValue;

      switch (sortField) {
        case 'file_name':
          aValue = a.file_name.toLowerCase();
          bValue = b.file_name.toLowerCase();
          break;
        case 'created_at':
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
          break;
        case 'priority':
          aValue = a.priority;
          bValue = b.priority;
          break;
        case 'data_type':
          aValue = a.data_type.toLowerCase();
          bValue = b.data_type.toLowerCase();
          break;
        case 'confidence_score':
          aValue = a.auto_extraction_result?.extraction_summary?.confidence_score || 0;
          bValue = b.auto_extraction_result?.extraction_summary?.confidence_score || 0;
          break;
        default:
          aValue = a.created_at;
          bValue = b.created_at;
      }

      return sortDirection === 'asc' ? (aValue > bValue ? 1 : -1) : (aValue < bValue ? 1 : -1);
    });

    return filtered;
  }, [queue, searchQuery, filterSeverity, filterFileType, filterDataType, filterPriority, filterConfidence, sortField, sortDirection]);

  // Pagination
  const totalPages = Math.ceil((filteredQueue?.length || 0) / pageSize);
  const paginatedQueue = filteredQueue?.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setFilterSeverity('all');
    setFilterFileType('all');
    setFilterDataType('all');
    setFilterPriority('all');
    setFilterConfidence('all');
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return <FaExclamationCircle className="text-red-500" />;
      case 'warning': return <FaExclamationTriangle className="text-yellow-500" />;
      case 'info': return <FaInfoCircle className="text-blue-500" />;
      default: return <FaInfoCircle className="text-gray-500" />;
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

  const getPriorityLabel = (priority) => {
    switch (priority) {
      case 2: return { label: '🔥 Urgent', color: 'badge-danger' };
      case 1: return { label: '⚠️ High', color: 'badge-warning' };
      default: return { label: '📄 Normal', color: 'badge-info' };
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.7) return 'text-green-600 bg-green-50';
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const handleViewError = (issue) => {
    setSelectedError(issue);
    setIsModalOpen(true);
  };

  const exportToCSV = () => {
    if (!filteredQueue || filteredQueue.length === 0) {
      toast.error('No data to export');
      return;
    }

    const headers = ['File Name', 'Type', 'Data Type', 'Priority', 'Confidence Score', 'Critical Issues', 'Warnings', 'Created At'];
    const rows = filteredQueue.map(item => {
      const summary = item.auto_extraction_result?.extraction_summary || {};
      const issues = item.auto_extraction_result?.extraction_issues || [];
      const critical = issues.filter(i => i.severity === 'critical').length;
      const warnings = issues.filter(i => i.severity === 'warning').length;
      
      return [
        `"${item.file_name}"`,
        item.file_type,
        item.data_type,
        item.priority,
        (summary.confidence_score || 0).toFixed(2),
        critical,
        warnings,
        new Date(item.created_at).toLocaleString()
      ];
    });

    const csvContent = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `extraction_errors_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    toast.success('Export successful!');
  };

  const hasActiveFilters = searchQuery || filterSeverity !== 'all' || filterFileType !== 'all' || 
    filterDataType !== 'all' || filterPriority !== 'all' || filterConfidence !== 'all';

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">🔍 Extraction Error Review</h1>
            <p className="text-gray-600">Review and debug extraction errors from PDF and image files</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={exportToCSV}
              disabled={!filteredQueue || filteredQueue.length === 0}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <FaDownload />
              Export CSV
            </button>
            <button
              onClick={() => refetch()}
              disabled={isLoading}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <FaSync className={isLoading ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      {!isLoading && queue && queue.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-500">Total Files</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border-l-4 border-red-500 p-4">
            <p className="text-sm text-gray-500">Critical Errors</p>
            <p className="text-2xl font-bold text-red-600">{stats.critical}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border-l-4 border-yellow-500 p-4">
            <p className="text-sm text-gray-500">Warnings</p>
            <p className="text-2xl font-bold text-yellow-600">{stats.warning}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border-l-4 border-blue-500 p-4">
            <p className="text-sm text-gray-500">Low Confidence</p>
            <p className="text-2xl font-bold text-blue-600">{stats.lowConfidence}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border-l-4 border-yellow-500 p-4">
            <p className="text-sm text-gray-500">High Priority</p>
            <p className="text-2xl font-bold text-yellow-600">{stats.highPriority}</p>
          </div>
        </div>
      )}

      {/* Search and Filter Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap gap-3 items-center">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search by file name, ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <FaTimes />
                </button>
              )}
            </div>
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 rounded-lg border transition-colors flex items-center gap-2 ${
              showFilters ? 'bg-primary-50 border-primary-500 text-primary-600' : 'border-gray-300 hover:bg-gray-50'
            }`}
          >
            <FaFilter />
            Filters
            {hasActiveFilters && (
              <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
            )}
          </button>

          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
            >
              <FaTimes className="text-xs" />
              Clear All
            </button>
          )}
        </div>

        {/* Advanced Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                <select
                  value={filterSeverity}
                  onChange={(e) => setFilterSeverity(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="warning">Warning</option>
                  <option value="info">Info</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">File Type</label>
                <select
                  value={filterFileType}
                  onChange={(e) => setFilterFileType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                >
                  <option value="all">All Types</option>
                  <option value="PDF">PDF</option>
                  <option value="IMAGE">Image</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Data Type</label>
                <select
                  value={filterDataType}
                  onChange={(e) => setFilterDataType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                >
                  <option value="all">All Types</option>
                  {uniqueDataTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <select
                  value={filterPriority}
                  onChange={(e) => setFilterPriority(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                >
                  <option value="all">All Priorities</option>
                  <option value="2">🔥 Urgent</option>
                  <option value="1">⚠️ High</option>
                  <option value="0">📄 Normal</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Confidence</label>
                <select
                  value={filterConfidence}
                  onChange={(e) => setFilterConfidence(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                >
                  <option value="all">All Scores</option>
                  <option value="high">High (&gt;70%)</option>
                  <option value="medium">Medium (40-70%)</option>
                  <option value="low">Low (&lt;40%)</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-600">
          Showing {filteredQueue?.length || 0} of {queue?.length || 0} items
          {filteredQueue?.length !== queue?.length && ' (filtered)'}
        </p>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span>Sort by:</span>
          <button
            onClick={() => handleSort('file_name')}
            className={`flex items-center gap-1 hover:text-gray-700 ${sortField === 'file_name' ? 'text-primary-600 font-medium' : ''}`}
          >
            Name
            {sortField === 'file_name' && (sortDirection === 'asc' ? <FaSortUp /> : <FaSortDown />)}
          </button>
          <span className="text-gray-300">|</span>
          <button
            onClick={() => handleSort('created_at')}
            className={`flex items-center gap-1 hover:text-gray-700 ${sortField === 'created_at' ? 'text-primary-600 font-medium' : ''}`}
          >
            Date
            {sortField === 'created_at' && (sortDirection === 'asc' ? <FaSortUp /> : <FaSortDown />)}
          </button>
          <span className="text-gray-300">|</span>
          <button
            onClick={() => handleSort('priority')}
            className={`flex items-center gap-1 hover:text-gray-700 ${sortField === 'priority' ? 'text-primary-600 font-medium' : ''}`}
          >
            Priority
            {sortField === 'priority' && (sortDirection === 'asc' ? <FaSortUp /> : <FaSortDown />)}
          </button>
          <span className="text-gray-300">|</span>
          <button
            onClick={() => handleSort('confidence_score')}
            className={`flex items-center gap-1 hover:text-gray-700 ${sortField === 'confidence_score' ? 'text-primary-600 font-medium' : ''}`}
          >
            Confidence
            {sortField === 'confidence_score' && (sortDirection === 'asc' ? <FaSortUp /> : <FaSortDown />)}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading extraction errors...</p>
          </div>
        </div>
      ) : !queue || queue.length === 0 ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <div className="text-4xl mb-3">🎉</div>
          <p className="text-green-800 font-medium">All caught up!</p>
          <p className="text-green-600 text-sm">No pending manual reviews with extraction errors.</p>
        </div>
      ) : filteredQueue?.length === 0 ? (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <p className="text-blue-800 font-medium">No items match your current filters</p>
          <p className="text-blue-600 text-sm">Try adjusting your search or filters.</p>
        </div>
      ) : (
        <>
          {/* Queue Items */}
          <div className="space-y-4">
            {paginatedQueue?.map((item) => {
              const issues = item.auto_extraction_result?.extraction_issues || [];
              const summary = item.auto_extraction_result?.extraction_summary || {};
              const confidenceScore = summary.confidence_score || 0;
              const hasCritical = issues.some(i => i.severity === 'critical');
              const hasWarning = issues.some(i => i.severity === 'warning');
              const priorityInfo = getPriorityLabel(item.priority);

              return (
                <div
                  key={item.id}
                  className={`bg-white rounded-lg shadow-sm border-l-4 ${
                    hasCritical ? 'border-red-500' : hasWarning ? 'border-yellow-500' : 'border-blue-500'
                  } p-4 hover:shadow-md transition-shadow`}
                >
                  <div className="flex flex-wrap justify-between items-start gap-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-gray-900 truncate">
                        {item.file_name}
                      </h3>
                      <div className="flex flex-wrap gap-2 mt-1">
                        <span className={`badge ${item.file_type === 'PDF' ? 'badge-info' : 'badge-secondary'}`}>
                          {item.file_type === 'PDF' ? <FaFilePdf className="inline mr-1" /> : <FaImage className="inline mr-1" />}
                          {item.file_type}
                        </span>
                        <span className="badge badge-gray">{item.data_type}</span>
                        <span className={`badge ${priorityInfo.color}`}>{priorityInfo.label}</span>
                        <span className={`badge ${getConfidenceColor(confidenceScore)}`}>
                          Confidence: {(confidenceScore * 100).toFixed(0)}%
                        </span>
                        <span className="text-xs text-gray-400 flex items-center gap-1">
                          <FaClock className="text-xs" />
                          {new Date(item.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                    <button className="px-3 py-1.5 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors">
                      Review
                    </button>
                  </div>

                  {/* Summary Stats */}
                  {Object.keys(summary).length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-4 border-t border-gray-100 pt-3">
                      <div>
                        <p className="text-xs text-gray-500">Total Fields</p>
                        <p className="text-lg font-semibold">{summary.total_fields || 0}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">✅ Extracted</p>
                        <p className="text-lg font-semibold text-green-600">{summary.extracted_successfully || 0}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">⚠️ Needs Review</p>
                        <p className="text-lg font-semibold text-yellow-600">{summary.needs_manual_review || 0}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">❌ Failed</p>
                        <p className="text-lg font-semibold text-red-600">{summary.failed || 0}</p>
                      </div>
                    </div>
                  )}

                  {/* Issues List */}
                  {issues.length > 0 && (
                    <details className="mt-3">
                      <summary className="text-sm font-medium text-gray-700 cursor-pointer hover:text-gray-900 flex items-center gap-2">
                        <FaExclamationTriangle className="text-yellow-500" />
                        {issues.length} Issue{issues.length > 1 ? 's' : ''}
                      </summary>
                      <div className="mt-2 space-y-2">
                        {issues.map((issue, index) => (
                          <div
                            key={index}
                            className={`p-3 rounded-lg border-l-4 ${getSeverityColor(issue.severity)} flex justify-between items-start gap-2`}
                          >
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                {getSeverityIcon(issue.severity)}
                                <p className="text-sm font-medium">
                                  {issue.field ? `${issue.field}: ` : ''}{issue.message}
                                </p>
                              </div>
                              {issue.value && (
                                <p className="text-xs text-gray-500 mt-1">
                                  Value: <span className="font-mono bg-gray-100 px-1 py-0.5 rounded">{String(issue.value)}</span>
                                </p>
                              )}
                              {issue.technical_details && (
                                <p className="text-xs text-gray-400 mt-1 font-mono truncate">
                                  {issue.technical_details}
                                </p>
                              )}
                            </div>
                            <button
                              onClick={() => handleViewError(issue)}
                              className="text-blue-600 hover:text-blue-800 p-1 hover:bg-blue-50 rounded transition-colors flex-shrink-0"
                              title="View Details"
                            >
                              <FaEye />
                            </button>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}

                  {/* Raw Data */}
                  {item.auto_extraction_result && (
                    <details className="mt-3">
                      <summary className="text-sm font-medium text-gray-700 cursor-pointer hover:text-gray-900 flex items-center gap-2">
                        <FaCode className="text-gray-500" />
                        Raw Extraction Data
                      </summary>
                      <div className="mt-2 p-3 bg-gray-900 rounded-lg overflow-auto max-h-60">
                        <pre className="text-xs text-gray-300 whitespace-pre-wrap break-words">
                          {JSON.stringify(item.auto_extraction_result, null, 2)}
                        </pre>
                      </div>
                    </details>
                  )}
                </div>
              );
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, filteredQueue?.length || 0)} of {filteredQueue?.length || 0} results
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
        </>
      )}

      {/* Error Detail Modal */}
      <ErrorDetailModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedError(null);
        }}
        error={selectedError}
      />
    </div>
  );
};

export default ExtractionErrorReview;