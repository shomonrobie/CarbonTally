// src/components/admin/ReviewExtractionModal.js
import React, { useState, useEffect } from 'react';
import {
  FaTimes,
  FaFilePdf,
  FaImage,
  FaLayerGroup,
  FaSave,
  FaArrowLeft,
  FaBuilding,
  FaCar,
  FaCalendarAlt,
  FaBolt
} from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';

const ReviewExtractionModal = ({ isOpen, onClose, item }) => {
  const [loading, setLoading] = useState(false);
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

  if (!isOpen || !item) return null;

  useEffect(() => {
    if (item?.organization_id) {
      fetchOrganizationAssets(item.organization_id);
    }
    if (item?.batch_id) {
      fetchBatchInfo(item.batch_id);
    }
  }, [item]);

  const fetchOrganizationAssets = async (orgId) => {
    try {
      // Fetch facilities
      const { data: facilitiesData, error: facError } = await supabase
        .from('facilities')
        .select('id, name')
        .eq('organization_id', orgId)
        .order('name');

      if (facError) throw facError;
      setFacilities(facilitiesData || []);

      // Fetch assets for these facilities
      const facilityIds = facilitiesData?.map(f => f.id) || [];
      if (facilityIds.length > 0) {
        const { data: assetsData, error: assetError } = await supabase
          .from('assets')
          .select('id, name, facility_id')
          .in('facility_id', facilityIds)
          .order('name');

        if (assetError) throw assetError;
        setAssets(assetsData || []);
      }
    } catch (error) {
      console.error('Error fetching assets:', error);
      toast.error('Failed to load facilities and assets');
    }
  };

  const fetchBatchInfo = async (batchId) => {
    try {
      const { data, error } = await supabase
        .from('upload_batches')
        .select('batch_name, total_files, processed_files')
        .eq('id', batchId)
        .single();

      if (error) throw error;
      if (data) {
        setBatchInfo({
          name: data.batch_name,
          total: data.total_files,
          completed: data.processed_files
        });
      }
    } catch (error) {
      console.error('Error fetching batch info:', error);
    }
  };

  const handleFacilityChange = (facilityId) => {
    setSelectedFacilityId(facilityId);
    setFormData({ ...formData, assetName: '' });
  };

  const handleSubmit = async () => {
    setLoading(true);

    try {
      // Validate required fields
      if (!formData.billingStart || !formData.consumption || !formData.fuelType) {
        toast.error('Please fill in all required fields');
        setLoading(false);
        return;
      }

      // Update the queue item
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
          completed_at: new Date().toISOString()
        })
        .eq('id', item.id);

      if (updateError) throw updateError;

      // Approve and save to emissions_logs
      const approvalResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/approve-extraction`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          review_id: item.id,
          organization_id: item.organization_id,
          extraction_result: {
            billing_start: formData.billingStart,
            consumption: parseFloat(formData.consumption) || 0,
            fuel_utility_type: formData.fuelType,
            asset_name: formData.assetName
          },
          reporting_year: formData.reportingYear || null
        })
      });

      const approvalResult = await approvalResponse.json();
      if (approvalResult.status !== 'success') {
        throw new Error('Failed to save emissions data');
      }

      toast.success(`✅ Review completed! ${approvalResult.calculated_kg_co2e} kgCO2e saved`);

      // Handle notifications based on batch
      if (item.batch_id) {
        const { count, error: countError } = await supabase
          .from('manual_review_queue')
          .select('*', { count: 'exact', head: true })
          .eq('batch_id', item.batch_id)
          .eq('status', 'pending');

        if (!countError && count === 0) {
          // All files in batch are complete
          await supabase
            .from('upload_batches')
            .update({ 
              status: 'completed', 
              completed_at: new Date().toISOString() 
            })
            .eq('id', item.batch_id);

          toast.success('🎉 Batch fully processed! Customer will be notified.');
        } else {
          toast.success(`✅ File processed! ${count} file(s) remaining in this batch`);
        }
      } else {
        // Single file notification
        toast.success('✅ Review completed! Customer will be notified.');
      }

      onClose();
    } catch (error) {
      console.error('Error processing review:', error);
      toast.error('Failed to complete review: ' + error.message);
    } finally {
      setLoading(false);
    }
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
              <h2 className="text-xl font-bold text-gray-900">📄 Review Document</h2>
              <p className="text-sm text-gray-500">{item.file_name}</p>
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
              {/* Left: Document Preview */}
              <div className="space-y-4">
                <div className="bg-gray-100 rounded-lg p-4 h-96 flex items-center justify-center overflow-hidden">
                  {item.file_type === 'PDF' ? (
                    <iframe
                      src={item.file_url}
                      title="PDF Viewer"
                      className="w-full h-full border-0 rounded-lg"
                    />
                  ) : (
                    <img
                      src={item.file_url}
                      alt="Document"
                      className="max-w-full max-h-full object-contain"
                    />
                  )}
                </div>

                {/* Batch Info */}
                {batchInfo && (
                  <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                    <div className="flex items-center gap-2 text-blue-800">
                      <FaLayerGroup />
                      <span className="font-medium">Batch: {batchInfo.name}</span>
                    </div>
                    <p className="text-sm text-blue-700 mt-1">
                      {batchInfo.completed} of {batchInfo.total} files processed
                    </p>
                  </div>
                )}

                {/* Customer Notes */}
                {item.customer_notes?.includes('📝 CUSTOMER NOTE:') && (
                  <div className="bg-yellow-50 rounded-lg p-3 border border-yellow-200">
                    <p className="text-sm font-medium text-yellow-800 flex items-center gap-2">
                      <span>📝</span> Customer Instructions
                    </p>
                    <p className="text-sm text-yellow-700 mt-1">
                      {item.customer_notes.split('📝 CUSTOMER NOTE:')[1]}
                    </p>
                  </div>
                )}
              </div>

              {/* Right: Manual Entry Form */}
              <div>
                <h3 className="font-medium text-gray-900 mb-4">Manual Data Extraction</h3>
                
                <div className="space-y-4">
                  {/* Billing Date */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Billing Period Start *
                    </label>
                    <input
                      type="date"
                      value={formData.billingStart}
                      onChange={(e) => setFormData({ ...formData, billingStart: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                    />
                  </div>

                  {/* Reporting Year */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Reporting Year
                    </label>
                    <select
                      value={formData.reportingYear}
                      onChange={(e) => setFormData({ ...formData, reportingYear: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                    >
                      <option value="">Auto-detect from date</option>
                      <option value="2026">2026</option>
                      <option value="2025">2025</option>
                      <option value="2024">2024</option>
                      <option value="2023">2023</option>
                      <option value="2022">2022</option>
                    </select>
                    {formData.billingStart && (
                      <p className="text-xs text-gray-500 mt-1">
                        Detected: {formData.billingStart.split('-')[0]}
                      </p>
                    )}
                  </div>

                  {/* Consumption */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Consumption (kWh or Litres) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.consumption}
                      onChange={(e) => setFormData({ ...formData, consumption: e.target.value })}
                      placeholder="Enter consumption value"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                    />
                  </div>

                  {/* Facility */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Facility
                    </label>
                    <select
                      value={selectedFacilityId}
                      onChange={(e) => handleFacilityChange(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                    >
                      <option value="">Select facility...</option>
                      {facilities.map(facility => (
                        <option key={facility.id} value={facility.id}>
                          {facility.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Asset */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Asset (Vehicle/Meter)
                    </label>
                    <select
                      value={formData.assetName}
                      onChange={(e) => setFormData({ ...formData, assetName: e.target.value })}
                      disabled={!selectedFacilityId}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none disabled:bg-gray-100"
                    >
                      <option value="">{selectedFacilityId ? 'Select asset...' : 'Select a facility first'}</option>
                      {assets
                        .filter(a => a.facility_id === selectedFacilityId)
                        .map(asset => (
                          <option key={asset.id} value={asset.name}>
                            {asset.name}
                          </option>
                        ))}
                    </select>
                  </div>

                  {/* Fuel Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Fuel/Utility Type *
                    </label>
                    <select
                      value={formData.fuelType}
                      onChange={(e) => setFormData({ ...formData, fuelType: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                    >
                      <option value="">Select type...</option>
                      <option value="Diesel">Diesel</option>
                      <option value="Petrol">Petrol</option>
                      <option value="Electricity">Electricity</option>
                      <option value="Natural Gas">Natural Gas</option>
                      <option value="AdBlue">AdBlue</option>
                    </select>
                  </div>

                  {/* Staff Notes */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Staff Notes
                    </label>
                    <textarea
                      value={formData.staffNotes}
                      onChange={(e) => setFormData({ ...formData, staffNotes: e.target.value })}
                      placeholder="Add notes about this extraction..."
                      rows="3"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none resize-none"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <FaSave />
              {loading ? 'Processing...' : 'Submit & Complete'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewExtractionModal;