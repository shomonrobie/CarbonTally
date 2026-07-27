// ManualReviewQueue.js - JavaScript version (no TypeScript)

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  FaEye,
  FaSync,
  FaFilePdf,
  FaImage,
  FaClock,
  FaExclamationTriangle,
  FaCheckCircle,
  FaArrowLeft,
  FaSave,
  FaLayerGroup,
  FaCalendarAlt,
  FaBuilding,
  FaCar,
  FaBolt,
  FaTimes,
  FaChevronLeft,
  FaChevronRight,
  FaDownload,
  FaInfoCircle
} from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';

// Helper to safely display object data
const safeDisplay = (data) => {
  if (!data) return 'No data';
  if (typeof data === 'string') return data;
  if (typeof data === 'number') return data.toString();
  if (typeof data === 'boolean') return data ? 'Yes' : 'No';
  if (Array.isArray(data)) return `[${data.length} items]`;
  if (typeof data === 'object') {
    try {
      return JSON.stringify(data, null, 2);
    } catch {
      return '[Complex Object]';
    }
  }
  return String(data);
};

// Helper to format confidence score
const formatConfidence = (score) => {
  if (!score && score !== 0) return 'N/A';
  return `${Math.round(score * 100)}%`;
};

const ManualReviewQueue = () => {
  const navigate = useNavigate();
  
  // State
  const [selectedItem, setSelectedItem] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [formData, setFormData] = useState({
    billingStart: '',
    consumption: '',
    assetName: '',
    fuelType: '',
    staffNotes: '',
    reportingYear: ''
  });
  const [facilities, setFacilities] = useState([]);
  const [assets, setAssets] = useState([]);
  const [selectedFacilityId, setSelectedFacilityId] = useState('');
  const [batchInfo, setBatchInfo] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [showExtractionDetails, setShowExtractionDetails] = useState(false);
  const itemsPerPage = 10;

  // ✅ Auth Check (Strict gating)
  useEffect(() => {
    const checkAuth = async () => {
      const { data: { user }, error } = await supabase.auth.getUser();
      
      if (!user || user.email !== 'shomonrobie@gmail.com') {
        navigate('/sign-in');
      } else {
        setIsAuthenticated(true);
      }
    };
    checkAuth();
  }, [navigate]);

  // ✅ Fetch queue items
  const { data: queue, isLoading, refetch } = useQuery({
    queryKey: ['manualReviewQueue'],
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
    enabled: isAuthenticated,
  });

  // ✅ Filtered and paginated queue
  const filteredQueue = queue?.filter(item => 
    item.file_name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const totalPages = Math.ceil(filteredQueue.length / itemsPerPage);
  const paginatedQueue = filteredQueue.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // ✅ Fetch Facilities & Assets for Organization
  const fetchOrganizationAssets = async (orgId) => {
    const { data: facilitiesData, error: facError } = await supabase
      .from('facilities')
      .select('id, name')
      .eq('organization_id', orgId)
      .order('name');

    if (facError) {
      console.error('❌ Facilities fetch error:', facError);
      setFacilities([]);
      return;
    }

    const facilityList = facilitiesData || [];
    setFacilities(facilityList);

    const facilityIds = facilityList.map(f => f.id);
    
    if (facilityIds.length > 0) {
      const { data: assetsData, error: assetError } = await supabase
        .from('assets')
        .select('id, name, facility_id')
        .in('facility_id', facilityIds)
        .order('name');

      if (assetError) {
        console.error('❌ Assets fetch error:', assetError);
        setAssets([]);
      } else {
        setAssets(assetsData || []);
      }
    }
  };

  // ✅ Handle Claiming an Item
  const handleClaim = async (item) => {
    setSelectedItem(item);
    setSelectedFacilityId('');
    setFormData({
      billingStart: '',
      consumption: '',
      assetName: '',
      fuelType: '',
      staffNotes: '',
      reportingYear: ''
    });
    setShowExtractionDetails(false);

    if (item.organization_id) {
      await fetchOrganizationAssets(item.organization_id);
    }

    if (item.batch_id) {
      const { data } = await supabase
        .from('upload_batches')
        .select('batch_name, total_files, processed_files')
        .eq('id', item.batch_id)
        .single();
      
      if (data) {
        setBatchInfo({
          name: data.batch_name,
          total: data.total_files,
          completed: data.processed_files
        });
      }
    } else {
      setBatchInfo(null);
    }
  };

  // ✅ Handle Form Changes
  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // ✅ Populate form from auto-extraction result
  const populateFromAutoExtraction = () => {
    if (!selectedItem?.auto_extraction_result) return;
    
    const result = selectedItem.auto_extraction_result;
    const extractionResult = result.extraction_result || result;
    
    // Try to find data streams
    const dataStreams = extractionResult.data_streams || [];
    if (dataStreams.length > 0) {
      const firstStream = dataStreams[0];
      const fields = firstStream.extracted_fields || {};
      
      setFormData(prev => ({
        ...prev,
        billingStart: fields.billing_start?.value || fields.billingStart?.value || '',
        consumption: fields.consumption?.value || fields.total_consumption?.value || '',
        fuelType: fields.fuel_utility_type?.value || fields.fuelType?.value || fields.fuel_type?.value || '',
        assetName: fields.asset_name?.value || fields.assetName?.value || '',
        reportingYear: fields.reporting_year?.value || fields.reportingYear?.value || ''
      }));
    }
    
    toast.success('📋 Auto-extraction data loaded into form');
  };

  // ✅ Submit & Complete Review
  const handleSubmit = async () => {
    if (!selectedItem) {
      toast.error('No item selected');
      return;
    }

    // Validate required fields
    if (!formData.billingStart || !formData.consumption || !formData.assetName || !formData.fuelType) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      const { data: { user } } = await supabase.auth.getUser();
      
      // Step A: Update the queue item in the database
      const { error: updateError } = await supabase
        .from('manual_review_queue')
        .update({
          status: 'completed',
          manual_extraction_result: {
            billing_start: formData.billingStart,
            consumption: parseFloat(formData.consumption) || 0,
            asset_name: formData.assetName,
            fuel_utility_type: formData.fuelType,
            staff_notes: formData.staffNotes,
            reporting_year: formData.reportingYear || null
          },
          staff_notes: formData.staffNotes,
          completed_at: new Date().toISOString(),
          assigned_to: user?.id || null,
          completed_by: user?.id || null,
          review_time_seconds: 0
        })
        .eq('id', selectedItem.id);

      if (updateError) {
        toast.error(`Error updating queue: ${updateError.message}`);
        return;
      }

      // Step B: Approve and save to official emissions_logs
      try {
        const approvalResponse = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/approve-extraction`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            review_id: selectedItem.id,
            organization_id: selectedItem.organization_id,
            extraction_result: {
              billing_start: formData.billingStart,
              consumption: parseFloat(formData.consumption) || 0,
              fuel_utility_type: formData.fuelType,
              asset_name: formData.assetName
            },
            reporting_year: formData.reportingYear || null,
            approved_by_user_id: user?.id
          })
        });

        const approvalResult = await approvalResponse.json();
        if (approvalResult.status === 'success') {
          console.log(`✅ Emissions saved: ${approvalResult.calculated_kg_co2e} kgCO2e (Year: ${approvalResult.reporting_year})`);
        }
      } catch (approvalError) {
        console.error('Failed to save to emissions_logs:', approvalError);
      }

      // Step C: Handle Notifications (Batch vs Single)
      try {
        if (selectedItem.batch_id) {
          const { count, error: countError } = await supabase
            .from('manual_review_queue')
            .select('*', { count: 'exact', head: true })
            .eq('batch_id', selectedItem.batch_id)
            .eq('status', 'pending');

          if (!countError && count === 0) {
            await supabase
              .from('upload_batches')
              .update({ 
                status: 'completed', 
                completed_at: new Date().toISOString() 
              })
              .eq('id', selectedItem.batch_id);

            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/notify-batch-completion`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                batch_id: selectedItem.batch_id,
                organization_id: selectedItem.organization_id
              })
            });
            
            const result = await response.json();
            if (result.status === 'success') {
              toast.success('✅ Batch fully processed! Customer notified.');
            }
          } else {
            toast.success(`✅ File processed! (${count || 0} file(s) remaining in this batch)`);
          }
        } else {
          const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/notify-customer-manual-extraction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              review_id: selectedItem.id,
              organization_id: selectedItem.organization_id,
              file_name: selectedItem.file_name
            })
          });

          const result = await response.json();
          if (result.status === 'success') {
            toast.success('✅ Review completed! Customer notified.');
          } else {
            toast.success('✅ Review completed! (Data saved, email skipped)');
          }
        }
      } catch (notifyError) {
        console.error('Notification failed:', notifyError);
        toast.success('✅ Review completed! (Data saved, but email notification failed)');
      }

      // Step D: Reset and refresh
      handleBack();
      
    } catch (error) {
      console.error('Error submitting review:', error);
      toast.error('Failed to submit review. Please try again.');
    }
  };

  // ✅ Reset Selection
  const handleBack = () => {
    setSelectedItem(null);
    setBatchInfo(null);
    setSelectedFacilityId('');
    setFormData({
      billingStart: '',
      consumption: '',
      assetName: '',
      fuelType: '',
      staffNotes: '',
      reportingYear: ''
    });
    setShowExtractionDetails(false);
    refetch();
  };

  // ✅ Get priority label and color
  const getPriorityInfo = (priority) => {
    const priorities = {
      2: { label: '🔥 Urgent', color: 'bg-red-100 text-red-800 border-red-200' },
      1: { label: '⚠️ High', color: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
      0: { label: '📄 Normal', color: 'bg-blue-100 text-blue-800 border-blue-200' },
    };
    return priorities[priority] || priorities[0];
  };

  // ✅ Handle refresh
  const handleRefresh = () => {
    refetch();
    toast.success('Queue refreshed');
  };

  // ✅ Count items by priority
  const urgentCount = queue?.filter(item => item.priority === 2).length || 0;
  const highCount = queue?.filter(item => item.priority === 1).length || 0;
  const normalCount = queue?.filter(item => item.priority === 0).length || 0;

  // --- RENDER: Loading ---
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading queue...</p>
        </div>
      </div>
    );
  }

  // --- RENDER: Access Denied ---
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // --- RENDER: Manual Extraction Form (Split Screen) ---
  if (selectedItem) {
    // Extract auto-extraction data for display
    const autoResult = selectedItem.auto_extraction_result;
    const extractionResult = autoResult?.extraction_result || autoResult || {};
    const dataStreams = extractionResult.data_streams || [];
    const firstStream = dataStreams[0] || {};
    const extractedFields = firstStream.extracted_fields || {};
    const issues = autoResult?.extraction_issues || extractionResult?.issues || [];
    const summary = autoResult?.extraction_summary || extractionResult?.summary || {};
    const confidenceScore = summary?.confidence_score || extractionResult?.confidence_score || 0;

    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={handleBack}
              className="px-4 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2 border border-gray-300"
            >
              <FaArrowLeft /> Back to Queue
            </button>
            <div className="flex gap-2">
              <button
                onClick={populateFromAutoExtraction}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                <FaSync /> Load Auto-Data
              </button>
              <button
                onClick={handleSubmit}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
              >
                <FaCheckCircle /> Submit & Complete
              </button>
            </div>
          </div>

          {/* Main Content - Split Screen */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* LEFT: Document Viewer & Extraction Results */}
            <div className="space-y-4">
              {/* Document Info */}
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      {selectedItem.file_type === 'PDF' ? <FaFilePdf className="text-red-500" /> : <FaImage className="text-purple-500" />}
                      {selectedItem.file_name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Type: {selectedItem.file_type} | 
                      Priority: {getPriorityInfo(selectedItem.priority).label}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedItem.customer_notes?.includes('📝 CUSTOMER NOTE:') && (
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full flex items-center gap-1">
                        <FaExclamationTriangle /> Customer Note
                      </span>
                    )}
                    <a 
                      href={selectedItem.file_url} 
                      download
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200 flex items-center gap-1"
                    >
                      <FaDownload /> Download
                    </a>
                  </div>
                </div>
              </div>

              {/* Document Viewer */}
              <div className="bg-white rounded-lg shadow p-2 h-[300px] lg:h-[400px] overflow-hidden bg-gray-100">
                {selectedItem.file_type === 'PDF' ? (
                  <iframe 
                    src={selectedItem.file_url} 
                    title="PDF Viewer"
                    className="w-full h-full border-0 rounded"
                    sandbox="allow-scripts allow-same-origin"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <img 
                      src={selectedItem.file_url} 
                      alt="Document" 
                      className="max-w-full max-h-full object-contain" 
                    />
                  </div>
                )}
              </div>

              {/* Extraction Results Section */}
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <button
                  onClick={() => setShowExtractionDetails(!showExtractionDetails)}
                  className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between border-b border-gray-200"
                >
                  <span className="font-semibold text-gray-700 flex items-center gap-2">
                    <FaInfoCircle className="text-blue-500" />
                    Extraction Results
                    {Object.keys(extractedFields).length > 0 && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
                        {Object.keys(extractedFields).length} fields
                      </span>
                    )}
                  </span>
                  <span className="text-sm text-gray-500">
                    Confidence: {formatConfidence(confidenceScore)}
                  </span>
                </button>
                
                {showExtractionDetails && (
                  <div className="p-4 space-y-4">
                    {/* Confidence Score */}
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">Confidence Score</span>
                        <span className={`text-sm font-bold ${confidenceScore > 0.7 ? 'text-green-600' : confidenceScore > 0.4 ? 'text-yellow-600' : 'text-red-600'}`}>
                          {formatConfidence(confidenceScore)}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                        <div 
                          className={`h-2 rounded-full ${confidenceScore > 0.7 ? 'bg-green-500' : confidenceScore > 0.4 ? 'bg-yellow-500' : 'bg-red-500'}`}
                          style={{ width: `${Math.min(confidenceScore * 100, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Extracted Fields */}
                    {Object.keys(extractedFields).length > 0 ? (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Extracted Data:</h4>
                        <div className="bg-gray-50 rounded-lg p-3 space-y-1">
                          {Object.entries(extractedFields).map(([key, value]) => {
                            const fieldValue = value?.value || value;
                            const confidence = value?.confidence || 1;
                            const isHighConfidence = confidence > 0.6;
                            
                            return (
                              <div key={key} className="flex items-center justify-between text-sm">
                                <span className="text-gray-600 capitalize">
                                  {key.replace(/_/g, ' ')}
                                </span>
                                <span className="flex items-center gap-2">
                                  <span className="font-medium text-gray-900">
                                    {safeDisplay(fieldValue)}
                                  </span>
                                  {confidence < 1 && (
                                    <span className={`text-xs ${isHighConfidence ? 'text-green-500' : 'text-yellow-500'}`}>
                                      {formatConfidence(confidence)}
                                    </span>
                                  )}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 italic">No auto-extracted data available</p>
                    )}

                    {/* Extraction Issues */}
                    {issues && issues.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-red-600 mb-2">⚠️ Issues:</h4>
                        <div className="bg-red-50 rounded-lg p-3 space-y-1">
                          {issues.map((issue, idx) => (
                            <div key={idx} className="text-sm text-red-700">
                              • {issue.message || issue}
                              {issue.field && <span className="text-xs text-red-500 ml-1">({issue.field})</span>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Raw Data Toggle */}
                    <details className="text-sm">
                      <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
                        View Raw Extraction Data
                      </summary>
                      <pre className="mt-2 p-3 bg-gray-900 text-gray-100 rounded-lg text-xs overflow-auto max-h-48">
                        {JSON.stringify(extractionResult, null, 2)}
                      </pre>
                    </details>
                  </div>
                )}
              </div>

              {/* Customer Note Highlight */}
              {selectedItem.customer_notes?.includes('📝 CUSTOMER NOTE:') && (
                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-r">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <FaExclamationTriangle className="h-5 w-5 text-yellow-400" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-yellow-700">
                        <strong>📝 Customer Instruction:</strong>
                        <br />
                        {selectedItem.customer_notes.split('📝 CUSTOMER NOTE:')[1]}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Batch Context */}
              {batchInfo && (
                <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <FaLayerGroup className="h-5 w-5 text-blue-400" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-blue-700">
                        <strong>📦 Batch Context:</strong> This file is part of the batch 
                        <strong> "{batchInfo.name}"</strong>. 
                        Total files in batch: {batchInfo.total} | 
                        Completed: {batchInfo.completed}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* RIGHT: Manual Entry Form */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-xl font-bold mb-4">📝 Manual Data Extraction</h3>
              
              <form className="space-y-4">
                {/* Billing Period Start */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <FaCalendarAlt className="inline mr-1" /> Billing Period Start
                  </label>
                  <input
                    type="date"
                    name="billingStart"
                    value={formData.billingStart}
                    onChange={handleFormChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    required
                  />
                </div>

                {/* Reporting Year */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    📊 Reporting Year (DEFRA Factor Year)
                  </label>
                  <select
                    name="reportingYear"
                    value={formData.reportingYear || (formData.billingStart ? formData.billingStart.split('-')[0] : '')}
                    onChange={handleFormChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">Auto-detect from billing date</option>
                    <option value="2026">2026</option>
                    <option value="2025">2025</option>
                    <option value="2024">2024</option>
                    <option value="2023">2023</option>
                    <option value="2022">2022</option>
                  </select>
                  {formData.billingStart && (
                    <p className="text-xs mt-1 text-green-600">
                      ✅ Auto-detected: Using {formData.billingStart.split('-')[0]} factors.
                    </p>
                  )}
                </div>

                {/* Consumption */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ⚡ Consumption (kWh or Litres)
                  </label>
                  <input
                    type="number"
                    name="consumption"
                    value={formData.consumption}
                    onChange={handleFormChange}
                    placeholder="Enter consumption value"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    required
                    step="0.01"
                  />
                </div>

                {/* Facility */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <FaBuilding className="inline mr-1" /> Facility
                  </label>
                  <select
                    value={selectedFacilityId}
                    onChange={(e) => {
                      setSelectedFacilityId(e.target.value);
                      setFormData({ ...formData, assetName: '' });
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">Select facility...</option>
                    {facilities.map(facility => (
                      <option key={facility.id} value={facility.id}>
                        {facility.name}
                      </option>
                    ))}
                  </select>
                  {facilities.length === 0 && (
                    <p className="text-xs mt-1 text-yellow-600">No facilities found for this organization</p>
                  )}
                </div>

                {/* Asset */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <FaCar className="inline mr-1" /> Asset (Vehicle/Meter)
                  </label>
                  <select
                    value={formData.assetName}
                    onChange={handleFormChange}
                    name="assetName"
                    disabled={!selectedFacilityId}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100"
                  >
                    <option value="">{selectedFacilityId ? "Select asset..." : "Select a facility first"}</option>
                    {assets
                      .filter(a => a.facility_id === selectedFacilityId)
                      .map(asset => (
                        <option key={asset.id} value={asset.name}>
                          {asset.name}
                        </option>
                      ))
                    }
                  </select>
                  {selectedFacilityId && (
                    <p className="text-xs mt-1 text-gray-500">
                      {assets.filter(a => a.facility_id === selectedFacilityId).length} assets in this facility
                    </p>
                  )}
                </div>

                {/* Fuel/Utility Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <FaBolt className="inline mr-1" /> Fuel/Utility Type
                  </label>
                  <select
                    name="fuelType"
                    value={formData.fuelType}
                    onChange={handleFormChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select type...</option>
                    <option value="Diesel">Diesel</option>
                    <option value="Petrol">Petrol</option>
                    <option value="Electricity">Electricity</option>
                    <option value="Natural Gas">Natural Gas</option>
                  </select>
                </div>

                {/* Staff Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    📝 Staff Notes
                  </label>
                  <textarea
                    name="staffNotes"
                    value={formData.staffNotes}
                    onChange={handleFormChange}
                    placeholder="Add any notes about this extraction..."
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>

                {/* Submit Button */}
                <button
                  type="button"
                  onClick={handleSubmit}
                  className="w-full py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2 text-lg font-semibold"
                >
                  <FaCheckCircle /> Submit & Complete Review
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // --- RENDER: Queue List ---
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">📋 Manual Review Queue</h1>
              <p className="text-gray-600">Review and process documents that require manual extraction</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleRefresh}
                disabled={isLoading}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                <FaSync className={isLoading ? 'animate-spin' : ''} />
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Priority Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-700 font-medium">Urgent</p>
                <p className="text-2xl font-bold text-red-600">{urgentCount}</p>
              </div>
              <FaExclamationTriangle className="text-2xl text-red-500" />
            </div>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-yellow-700 font-medium">High Priority</p>
                <p className="text-2xl font-bold text-yellow-600">{highCount}</p>
              </div>
              <FaClock className="text-2xl text-yellow-500" />
            </div>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-700 font-medium">Normal</p>
                <p className="text-2xl font-bold text-blue-600">{normalCount}</p>
              </div>
              <FaCheckCircle className="text-2xl text-blue-500" />
            </div>
          </div>
        </div>

        {/* GDPR Notice */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <div className="text-blue-600 text-xl">🔒</div>
            <div>
              <h4 className="font-medium text-blue-900">GDPR Compliance</h4>
              <p className="text-sm text-blue-700">
                All documents contain potentially sensitive data. Access is logged and restricted 
                to authorized personnel only. Customer data must be handled with care.
              </p>
            </div>
          </div>
        </div>

        {/* Queue Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h3 className="font-semibold text-gray-900">Pending Reviews</h3>
                <p className="text-sm text-gray-500">
                  {filteredQueue.length} items awaiting review
                </p>
              </div>
              <div className="w-full sm:w-64">
                <input
                  type="text"
                  placeholder="Search files..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none text-sm"
                />
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                  <p className="mt-4 text-gray-600">Loading queue...</p>
                </div>
              </div>
            ) : filteredQueue.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">🎉</div>
                <p className="text-gray-500 font-medium">All caught up!</p>
                <p className="text-sm text-gray-400">No pending manual reviews at this time</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Document
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Data Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Priority
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Submitted
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {paginatedQueue.map((item) => {
                    const priorityInfo = getPriorityInfo(item.priority);
                    
                    return (
                      <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4">
                          <div>
                            <p className="text-sm font-medium text-gray-900 flex items-center gap-2">
                              {item.file_type === 'PDF' ? (
                                <FaFilePdf className="text-red-500" />
                              ) : (
                                <FaImage className="text-purple-500" />
                              )}
                              {item.file_name}
                            </p>
                            {item.batch_id && (
                              <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                                <FaLayerGroup className="text-xs" />
                                Batch: {item.customer_notes?.split('Batch upload: ')[1]?.split('. File:')[0] || 'Batch'}
                              </p>
                            )}
                            {item.customer_notes?.includes('📝 CUSTOMER NOTE:') && (
                              <p className="text-xs text-yellow-600 flex items-center gap-1 mt-1">
                                <FaExclamationTriangle className="text-xs" />
                                Has customer instructions
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            item.file_type === 'PDF' ? 'bg-red-100 text-red-800' : 'bg-purple-100 text-purple-800'
                          }`}>
                            {item.file_type}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 capitalize">
                            {item.data_type || 'Unknown'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${priorityInfo.color}`}>
                            {priorityInfo.label}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div>
                            <p className="text-sm text-gray-600">
                              {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'N/A'}
                            </p>
                            <p className="text-xs text-gray-400">
                              {item.created_at ? new Date(item.created_at).toLocaleTimeString() : ''}
                            </p>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => handleClaim(item)}
                            className="px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2 ml-auto"
                          >
                            <FaEye className="text-xs" />
                            Review & Extract
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          {/* Pagination */}
          {filteredQueue.length > 0 && (
            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, filteredQueue.length)} of {filteredQueue.length} items
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <FaChevronLeft className="text-sm" />
                </button>
                <span className="px-3 py-1 text-sm text-gray-700">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <FaChevronRight className="text-sm" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ManualReviewQueue;