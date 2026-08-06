// UploadManager.jsx - Fixed API Endpoints

import React, { useState, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { supabase } from './supabaseClient';
import toast from 'react-hot-toast';
import {
  FaFilePdf, FaImage, FaCheckCircle, FaExclamationTriangle, FaSpinner,
  FaEye, FaEyeSlash, FaArrowLeft, FaArrowRight, FaDownload, FaTimes,
  FaPlus, FaSave, FaBuilding, FaCar, FaBolt, FaCalendarAlt, FaFileUpload,
  FaTrash, FaUndo, FaInfoCircle, FaUpload, FaBoxes, FaFile, FaUser,
  FaEnvelope, FaPhone, FaBriefcase, FaMapMarkerAlt
} from 'react-icons/fa';
import './css/UploadManager.css';
import useDocumentLogging from './hooks/useDocumentLogging';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const UploadManager = ({ organization, onUploadComplete }) => {
  // Mode: 'single' or 'bulk'
  const [uploadMode, setUploadMode] = useState('single');
  
  // Single Upload State
  const [activeStep, setActiveStep] = useState('upload');
  const [file, setFile] = useState(null);
  const [uploadType, setUploadType] = useState('utility');
  const [specialInstructions, setSpecialInstructions] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState(null);
  const [batchId, setBatchId] = useState(null);
  const [fileId, setFileId] = useState(null);
  
  // Review State
  const [documentStatus, setDocumentStatus] = useState('processing');
  const [extractedData, setExtractedData] = useState(null);
  const [reviewData, setReviewData] = useState({
    billing_start: '',
    consumption: '',
    fuel_utility_type: '',
    asset_name: '',
    facility_id: '',
    reporting_year: ''
  });
  const [pdfRotation, setPdfRotation] = useState(0);
  const [facilities, setFacilities] = useState([]);
  const [assets, setAssets] = useState([]);
  const [selectedFacilityId, setSelectedFacilityId] = useState('');
  const [staffNotes, setStaffNotes] = useState('');
  const [confidenceScore, setConfidenceScore] = useState(0);
  const [extractionIssues, setExtractionIssues] = useState([]);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [pdfNumPages, setPdfNumPages] = useState(null);
  const [pdfPageNumber, setPdfPageNumber] = useState(1);
  const [pdfScale, setPdfScale] = useState(1.0);
  const [manualEntryMode, setManualEntryMode] = useState(false);
  const [sendingToCarbonTally, setSendingToCarbonTally] = useState(false);

  // Complete State
  const [completedData, setCompletedData] = useState(null);

  // Bulk Upload State
  const [bulkFiles, setBulkFiles] = useState([]);
  const [bulkBatchName, setBulkBatchName] = useState('');
  const [bulkDataType, setBulkDataType] = useState('mixed');
  const [bulkSpecialInstructions, setBulkSpecialInstructions] = useState('');
  const [bulkUploading, setBulkUploading] = useState(false);
  const [bulkProgress, setBulkProgress] = useState(0);
  const [bulkFileProgress, setBulkFileProgress] = useState({});
  const [bulkBatchId, setBulkBatchId] = useState(null);
  const [bulkStatus, setBulkStatus] = useState(null);
  const [bulkError, setBulkError] = useState(null);

  const fileInputRef = useRef(null);
  const bulkFileInputRef = useRef(null);
  const pollInterval = useRef(null);
  
  const { 
    logDocumentUpload, 
    logExtraction, 
    logManualEntry, 
    logDocumentDecision, 
    logError,
    logUserAction,
    getRecentLogs
  } = useDocumentLogging();

  // Get auth token
  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  const rotateLeft = () => {
    setPdfRotation(prev => (prev - 90 + 360) % 360);
  };

  const rotateRight = () => {
    setPdfRotation(prev => (prev + 90) % 360);
  };

  const resetRotation = () => {
    setPdfRotation(0);
  };

  const getRotationStyle = (rotation) => {
    return {
      transform: `rotate(${rotation}deg)`,
      transition: 'transform 0.3s ease'
    };
  };

  // ============================================
  // FIXED: FETCH FACILITIES AND ASSETS
  // ============================================

  const fetchFacilitiesAndAssets = async () => {
    if (!organization?.id) {
      console.log('⏳ Waiting for organization ID...');
      return;
    }

    try {
      const token = await getToken();
      
      // ✅ FIX: Include organization ID in the path
      const facResponse = await fetch(`${API_URL}/api/organizations/${organization.id}/facilities?limit=1000`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (facResponse.ok) {
        const data = await facResponse.json();
        setFacilities(data.facilities || []);
        console.log('✅ Facilities loaded:', data.facilities?.length || 0);
      } else {
        console.error('❌ Failed to fetch facilities:', facResponse.status);
      }

      // ✅ FIX: Include organization ID in the path
      const assetResponse = await fetch(`${API_URL}/api/organizations/${organization.id}/assets?limit=1000`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (assetResponse.ok) {
        const data = await assetResponse.json();
        setAssets(data.assets || []);
        console.log('✅ Assets loaded:', data.assets?.length || 0);
      } else {
        console.error('❌ Failed to fetch assets:', assetResponse.status);
      }
    } catch (error) {
      console.error('Error fetching facilities/assets:', error);
      toast.error('Failed to load facilities and assets');
    }
  };

  useEffect(() => {
    if (organization?.id) {
      fetchFacilitiesAndAssets();
    }
  }, [organization?.id]);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollInterval.current) {
        clearInterval(pollInterval.current);
      }
    };
  }, []);

  // ============================================
  // FIXED: SINGLE UPLOAD FUNCTIONS
  // ============================================

  const handleFileUpload = async () => {
    if (!file) {
      toast.error('Please select a file first');
      return;
    }

    if (!organization?.id) {
      toast.error('Organization not found. Please reload.');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('data_type', uploadType);
    formData.append('organization_id', organization.id);
    if (specialInstructions) {
      formData.append('special_instructions', specialInstructions);
    }

    const startTime = Date.now();

    try {
      const token = await getToken();
      
      // ✅ Log upload start
      await logDocumentUpload(file, {
        data_type: uploadType,
        special_instructions: specialInstructions,
        organization_id: organization.id
      });
      
      // ✅ FIX: Use correct upload endpoint
      const response = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const result = await response.json();

      if (response.ok) {
        setBatchId(result.batch_id);
        setFileId(result.file_id);
        setUploadProgress(100);
        toast.success('✅ File uploaded successfully!');
        
        // ✅ Log extraction start
        await logExtraction(result.file_id, {
          success: result.extraction_result ? true : false,
          confidence: result.confidence_score || 0,
          fields_extracted: result.extraction_result?.data_streams?.length || 0,
          duration_ms: Date.now() - startTime
        });
        
        if (result.extraction_result) {
          setExtractedData(result.extraction_result);
          setDocumentStatus(result.status || 'processing');
          setConfidenceScore(result.confidence_score || 0);
          setExtractionIssues(result.issues || []);
          populateReviewForm(result.extraction_result);
          setActiveStep('review');
        } else {
          setActiveStep('review');
          setDocumentStatus('processing');
          pollDocumentStatus(result.file_id);
        }
      } else {
        setUploadError(result.detail || 'Upload failed');
        toast.error(result.detail || 'Upload failed');
        
        // ✅ Log upload error
        await logError(new Error(result.detail || 'Upload failed'), {
          fileId: result.file_id,
          fileName: file.name,
          data_type: uploadType
        });
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadError(error.message);
      toast.error('Upload failed: ' + error.message);
      
      // ✅ Log error
      await logError(error, {
        fileName: file.name,
        fileSize: file.size,
        data_type: uploadType
      });
    } finally {
      setUploading(false);
    }
  };

  const pollDocumentStatus = async (fileId) => {
    if (!fileId) return;
    
    let attempts = 0;
    const maxAttempts = 30;

    pollInterval.current = setInterval(async () => {
      attempts++;
      try {
        const token = await getToken();
        // ✅ FIX: Use correct status endpoint
        const response = await fetch(`${API_URL}/api/documents/${fileId}/status`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json();
          const status = data.document?.status || 'processing';
          setDocumentStatus(status);

          if (status === 'ready_for_review' || status === 'approved' || status === 'rejected') {
            clearInterval(pollInterval.current);
            if (status === 'ready_for_review' && data.document?.metadata?.extraction_result) {
              const extractionResult = data.document.metadata.extraction_result;
              setExtractedData(extractionResult);
              populateReviewForm(extractionResult);
              setConfidenceScore(data.document.metadata.confidence_score || 0);
              setExtractionIssues(data.document.metadata.issues || []);
              toast.success('📊 Extraction complete! Please review the data.');
            }
            setActiveStep('review');
          }
        }

        if (attempts >= maxAttempts) {
          clearInterval(pollInterval.current);
          toast('Processing is taking longer than expected. Please refresh.', {
            icon: '⏳',
            duration: 4000,
          });
        }
      } catch (error) {
        console.error('Poll error:', error);
      }
    }, 2000);
  };

  const populateReviewForm = (extractionResult) => {
    const streams = extractionResult.data_streams || [];
    const firstStream = streams[0] || {};
    const fields = firstStream.extracted_fields || {};

    setReviewData({
      billing_start: fields.billing_start?.value || fields.billingStart?.value || '',
      consumption: fields.consumption?.value || fields.total_consumption?.value || '',
      fuel_utility_type: fields.fuel_utility_type?.value || fields.fuelType?.value || fields.fuel_type?.value || '',
      asset_name: fields.asset_name?.value || fields.assetName?.value || '',
      facility_id: fields.facility_id?.value || '',
      reporting_year: fields.reporting_year?.value || fields.reportingYear?.value || ''
    });

    if (fields.asset_name?.value) {
      const matchedAsset = assets.find(a => a.name.toLowerCase() === fields.asset_name.value.toLowerCase());
      if (matchedAsset?.facility_id) {
        setSelectedFacilityId(matchedAsset.facility_id);
        setReviewData(prev => ({
          ...prev,
          facility_id: matchedAsset.facility_id
        }));
      }
    }
  };

  const handleReviewChange = (field, value) => {
    setReviewData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleFacilitySelect = (facilityId) => {
    setSelectedFacilityId(facilityId);
    setReviewData(prev => ({
      ...prev,
      facility_id: facilityId
    }));
  };

  // ============================================
  // FIXED: APPROVE FUNCTION
  // ============================================

  const handleApprove = async () => {
    if (!fileId) {
      toast.error('No document to approve');
      return;
    }

    if (!reviewData.billing_start) {
      toast.error('Please enter a billing period start date');
      return;
    }
    if (!reviewData.consumption || parseFloat(reviewData.consumption) <= 0) {
      toast.error('Please enter a valid consumption value');
      return;
    }
    if (!reviewData.fuel_utility_type) {
      toast.error('Please select a fuel/utility type');
      return;
    }
    if (!reviewData.asset_name) {
      toast.error('Please enter or select an asset name');
      return;
    }

    setReviewSubmitting(true);

    try {
      const token = await getToken();
      
      const extractionResult = {
        billing_start: reviewData.billing_start,
        consumption: parseFloat(reviewData.consumption),
        fuel_utility_type: reviewData.fuel_utility_type,
        asset_name: reviewData.asset_name,
        facility_id: reviewData.facility_id,
        reporting_year: reviewData.reporting_year || new Date().getFullYear()
      };

      // ✅ FIX: Use correct review endpoint
      const response = await fetch(`${API_URL}/api/documents/${fileId}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          action: 'approve',
          notes: staffNotes,
          extraction_result: extractionResult
        })
      });

      if (response.ok) {
        const result = await response.json();
        setCompletedData(result);
        setActiveStep('complete');
        toast.success('✅ Document approved and saved successfully!');
        
        // ✅ Log approval
        await logDocumentDecision(fileId, 'approve', staffNotes, {
          emission_id: result.emission_id,
          extraction_data: extractionResult,
          reviewed_by: organization?.name || 'Unknown'
        });
        
        if (onUploadComplete) onUploadComplete(result);
      } else {
        const error = await response.json();
        console.error('Approval error:', error);
        toast.error(error.detail || 'Failed to approve document');
        
        // ✅ Log error
        await logError(new Error(error.detail || 'Approval failed'), {
          fileId,
          action: 'approve',
          data: extractionResult
        });
      }
    } catch (error) {
      console.error('Approval error:', error);
      toast.error('Failed to approve document');
      
      // ✅ Log error
      await logError(error, {
        fileId,
        action: 'approve'
      });
    } finally {
      setReviewSubmitting(false);
    }
  };

  // ============================================
  // FIXED: REJECT FUNCTION
  // ============================================

  const handleReject = async () => {
    if (!fileId) {
      toast.error('No document to reject');
      return;
    }

    if (!window.confirm('Are you sure you want to reject this document?')) return;

    try {
      const token = await getToken();
      
      // ✅ Log rejection
      await logDocumentDecision(fileId, 'reject', staffNotes || 'Rejected by user', {
        reason: staffNotes || 'Rejected by user',
        reviewed_by: organization?.name || 'Unknown'
      });
      
      // ✅ FIX: Use correct review endpoint
      const response = await fetch(`${API_URL}/api/documents/${fileId}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          action: 'reject',
          notes: staffNotes || 'Rejected by user'
        })
      });

      if (response.ok) {
        toast.success('Document rejected');
        setActiveStep('upload');
        setFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to reject document');
      }
    } catch (error) {
      console.error('Rejection error:', error);
      toast.error('Failed to reject document');
    }
  };

  // ============================================
  // FIXED: SEND TO CARBON TALLY
  // ============================================

  const handleSendToCarbonTally = async () => {
    if (!fileId) {
      toast.error('No file selected');
      return;
    }

    setSendingToCarbonTally(true);
    
    try {
      const token = await getToken();
      
      // ✅ Log manual entry request
      await logManualEntry(fileId, { 
        requested: true,
        reason: 'Customer requested manual extraction'
      }, {
        file_name: file?.name,
        organization_id: organization?.id
      });
      
      // ✅ FIX: Use correct admin documents endpoint
      const response = await fetch(`${API_URL}/api/admin/documents/${fileId}/status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          status: 'staff_review',
          notes: 'Customer requested manual extraction'
        })
      });

      if (response.ok) {
        toast.success('📋 Document sent to CarbonTally team for manual extraction!');
        toast.custom('Our team will process your document within 24-48 hours.', {
          icon: '⏳',
          duration: 5000,
        });
        setManualEntryMode(true);
        setDocumentStatus('staff_review');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to send for manual extraction');
      }
    } catch (error) {
      console.error('Error sending to CarbonTally:', error);
      toast.error('Failed to send document for manual extraction');
    } finally {
      setSendingToCarbonTally(false);
    }
  };

  // ============================================
  // FIXED: BULK UPLOAD FUNCTIONS
  // ============================================

  const handleBulkFileDrop = (e) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    addBulkFiles(droppedFiles);
  };

  const handleBulkFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    addBulkFiles(selectedFiles);
  };

  const addBulkFiles = (newFiles) => {
    const validFiles = newFiles.filter(file => {
      const validTypes = ['application/pdf', 'image/jpeg', 'image/png'];
      if (!validTypes.includes(file.type)) {
        toast.error(`❌ ${file.name}: Unsupported file type. Only PDF, JPG, PNG allowed.`);
        return false;
      }
      return true;
    });

    const validSizeFiles = validFiles.filter(file => {
      if (file.size > 50 * 1024 * 1024) {
        toast.error(`❌ ${file.name}: File exceeds 50MB limit.`);
        return false;
      }
      return true;
    });

    if (validSizeFiles.length + bulkFiles.length > 50) {
      toast.error('Maximum 50 files allowed per batch');
      return;
    }

    setBulkFiles(prev => [...prev, ...validSizeFiles]);
  };

  const removeBulkFile = (index) => {
    setBulkFiles(prev => prev.filter((_, i) => i !== index));
  };

  // ============================================
  // FIXED: HANDLE BULK UPLOAD
  // ============================================

  const handleBulkUpload = async () => {
    if (bulkFiles.length === 0) {
      toast.error('Please select at least one file');
      return;
    }
    if (!bulkBatchName.trim()) {
      toast.error('Please enter a batch name');
      return;
    }
    if (!organization?.id) {
      toast.error('Organization not found. Please reload.');
      return;
    }

    setBulkUploading(true);
    setBulkProgress(0);
    setBulkError(null);
    setBulkFileProgress({});

    const formData = new FormData();
    formData.append('batch_name', bulkBatchName);
    formData.append('data_type', bulkDataType);
    formData.append('organization_id', organization.id);
    formData.append('special_instructions', bulkSpecialInstructions);

    bulkFiles.forEach((file) => {
      formData.append('files', file);
    });

    try {
      const token = await getToken();

      // ✅ Log bulk upload start
      await logDocumentUpload({
        name: bulkBatchName,
        size: bulkFiles.reduce((acc, f) => acc + f.size, 0),
        type: 'bulk',
        data_type: bulkDataType
      }, {
        file_count: bulkFiles.length,
        special_instructions: bulkSpecialInstructions,
        organization_id: organization.id,
        is_bulk: true
      });

      // ✅ FIX: Use correct batch endpoint
      const response = await fetch(`${API_URL}/api/batches`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setBulkBatchId(data.batch_id);
        toast.success(`✅ Batch "${bulkBatchName}" created with ${bulkFiles.length} files. Processing started.`);
        setBulkProgress(100);
        
        // Poll for batch status
        pollBulkStatus(data.batch_id);
        
        setBulkFiles([]);
        setBulkBatchName('');
        setBulkSpecialInstructions('');
        
        setBulkStatus({
          batch_id: data.batch_id,
          batch_name: bulkBatchName,
          status: 'processing',
          total_files: bulkFiles.length,
          processed_files: 0,
          files: bulkFiles.map(f => ({
            name: f.name,
            status: 'pending'
          }))
        });
      } else {
        setBulkError(data.detail || 'Failed to upload batch');
        toast.error(data.detail || 'Failed to upload batch');
        setBulkUploading(false);
        
        // ✅ Log bulk upload error
        await logError(new Error(data.detail || 'Batch upload failed'), {
          batch_name: bulkBatchName,
          file_count: bulkFiles.length,
          is_bulk: true
        });
      }
    } catch (error) {
      console.error('Batch upload error:', error);
      setBulkError(error.message);
      toast.error('Failed to upload batch. Please try again.');
      setBulkUploading(false);
      
      // ✅ Log bulk upload error
      await logError(error, {
        batch_name: bulkBatchName,
        file_count: bulkFiles.length,
        is_bulk: true
      });
    }
  };

  const pollBulkStatus = async (batchId) => {
    if (pollInterval.current) {
      clearInterval(pollInterval.current);
    }

    pollInterval.current = setInterval(async () => {
      try {
        const token = await getToken();
        // ✅ FIX: Use correct batch status endpoint
        const response = await fetch(`${API_URL}/api/batches/${batchId}/status`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json();
          setBulkStatus(data);
          
          const progressMap = {};
          data.files?.forEach(file => {
            progressMap[file.id] = file.status;
          });
          setBulkFileProgress(progressMap);

          if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(pollInterval.current);
            if (data.status === 'completed') {
              toast.success(`✅ Batch "${data.batch_name}" processed successfully!`);
              if (onUploadComplete) onUploadComplete(data);
              setBulkUploading(false);
            } else {
              toast.error('Batch processing failed. Please try again.');
              setBulkUploading(false);
            }
          }
        }
      } catch (error) {
        console.error('Error polling batch status:', error);
      }
    }, 3000);
  };

  const clearBulkUpload = () => {
    setBulkFiles([]);
    setBulkBatchName('');
    setBulkSpecialInstructions('');
    setBulkBatchId(null);
    setBulkStatus(null);
    setBulkError(null);
    setBulkFileProgress({});
    if (bulkFileInputRef.current) bulkFileInputRef.current.value = '';
  };

  const handleBackToUpload = () => {
    setActiveStep('upload');
    setFile(null);
    setExtractedData(null);
    setReviewData({
      billing_start: '',
      consumption: '',
      fuel_utility_type: '',
      asset_name: '',
      facility_id: '',
      reporting_year: ''
    });
    setStaffNotes('');
    setBatchId(null);
    setFileId(null);
    setUploadProgress(0);
    setUploadError(null);
    setCompletedData(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ============================================
  // RENDER FUNCTIONS
  // ============================================

  // Single Upload View
  const renderSingleUploadView = () => (
    <div className="upload-view">
      <div className="upload-header">
        <h2>⬆️ Upload Data Statement</h2>
        <p className="upload-subtitle">Upload your fuel, utility, or Scope 3 data documents</p>
        <button
          className="switch-mode-btn"
          onClick={() => setUploadMode('bulk')}
        >
          <FaBoxes /> Switch to Bulk Upload
        </button>
      </div>

      <div className="upload-type-selector">
        <label className={`type-option ${uploadType === 'fuel' ? 'active' : ''}`}>
          <input type="radio" name="uploadType" value="fuel" checked={uploadType === 'fuel'} onChange={() => setUploadType('fuel')} />
          ⛽ Scope 1: Fuel
        </label>
        <label className={`type-option ${uploadType === 'utility' ? 'active' : ''}`}>
          <input type="radio" name="uploadType" value="utility" checked={uploadType === 'utility'} onChange={() => setUploadType('utility')} />
          🔌 Scope 2: Utility
        </label>
        <label className={`type-option ${uploadType === 'scope3' ? 'active' : ''}`}>
          <input type="radio" name="uploadType" value="scope3" checked={uploadType === 'scope3'} onChange={() => setUploadType('scope3')} />
          🌱 Scope 3: Travel/Waste
        </label>
      </div>

      <div
        className={`drop-zone ${file ? 'has-file' : ''}`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
          }
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="drop-icon">{file ? '📄' : '📤'}</div>
        <p className="drop-title">{file ? file.name : 'Drag & drop your file here'}</p>
        <p className="drop-subtitle">{file ? `(${(file.size / 1024).toFixed(1)} KB)` : 'or click to browse'}</p>
        <p className="drop-hint">Supports PDF, JPG, PNG, CSV, XLSX</p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.csv,.xlsx"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              setFile(e.target.files[0]);
            }
          }}
          style={{ display: 'none' }}
        />
        {file && (
          <button
            className="remove-file-btn"
            onClick={(e) => {
              e.stopPropagation();
              setFile(null);
              if (fileInputRef.current) fileInputRef.current.value = '';
            }}
          >
            <FaTimes /> Remove
          </button>
        )}
      </div>

      <div className="upload-form">
        <div className="form-group">
          <label>Special Instructions (Optional)</label>
          <textarea
            value={specialInstructions}
            onChange={(e) => setSpecialInstructions(e.target.value)}
            placeholder="Add any special instructions for processing this document..."
            rows="2"
          />
        </div>

        {uploadError && (
          <div className="error-message">
            <FaExclamationTriangle />
            {uploadError}
          </div>
        )}

        <button
          className={`upload-btn ${uploading ? 'loading' : ''}`}
          onClick={handleFileUpload}
          disabled={!file || uploading}
        >
          {uploading ? (
            <>
              <FaSpinner className="spinner" />
              Uploading... {uploadProgress}%
            </>
          ) : (
            <>
              <FaFileUpload />
              Upload & Process
            </>
          )}
        </button>

        {uploading && (
          <div className="progress-bar">
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
            </div>
          </div>
        )}
      </div>

      <div className="upload-info">
        <div className="info-card">
          <h4>💡 How it works</h4>
          <ul>
            <li>Upload your document (PDF, image, or spreadsheet)</li>
            <li>Our AI will extract relevant data automatically</li>
            <li>Review and verify the extracted data</li>
            <li>Approve to save to your emissions records</li>
          </ul>
        </div>
      </div>
    </div>
  );

  // Bulk Upload View
  const renderBulkUploadView = () => (
    <div className="upload-view">
      <div className="upload-header">
        <h2>📦 Bulk Document Upload</h2>
        <p className="upload-subtitle">Upload multiple bills, invoices, and receipts at once</p>
        <button
          className="switch-mode-btn"
          onClick={() => {
            setUploadMode('single');
            clearBulkUpload();
          }}
        >
          <FaFileUpload /> Switch to Single Upload
        </button>
      </div>

      {/* Bulk Upload Form */}
      <div className="bulk-form">
        <div className="form-group">
          <label>Batch Name *</label>
          <input
            type="text"
            value={bulkBatchName}
            onChange={(e) => setBulkBatchName(e.target.value)}
            placeholder="e.g., Q1 2024 Utility Bills"
            disabled={bulkUploading}
          />
        </div>

        <div className="form-group">
          <label>Document Type</label>
          <select
            value={bulkDataType}
            onChange={(e) => setBulkDataType(e.target.value)}
            disabled={bulkUploading}
          >
            <option value="mixed">Mixed (Auto-detect)</option>
            <option value="utility">Utility Bills Only</option>
            <option value="fuel">Fuel Invoices Only</option>
            <option value="scope3">Scope 3 Documents Only</option>
          </select>
        </div>

        <div className="form-group">
          <label>Special Instructions (Optional)</label>
          <textarea
            value={bulkSpecialInstructions}
            onChange={(e) => setBulkSpecialInstructions(e.target.value)}
            placeholder="e.g., 'Please log these under our 2024 fiscal year'"
            rows="2"
            disabled={bulkUploading}
          />
        </div>

        <div
          className="bulk-drop-zone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleBulkFileDrop}
          onClick={() => bulkFileInputRef.current?.click()}
        >
          <div className="drop-icon">📁</div>
          <p className="drop-title">Drag & drop your files here</p>
          <p className="drop-subtitle">or click to browse (PDF, JPG, PNG)</p>
          <p className="drop-hint">Maximum 50 files per batch</p>
          <input
            ref={bulkFileInputRef}
            type="file"
            multiple
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleBulkFileSelect}
            style={{ display: 'none' }}
            disabled={bulkUploading}
          />
        </div>

        {/* Bulk File List */}
        {bulkFiles.length > 0 && (
          <div className="bulk-file-list">
            <div className="file-list-header">
              <span>Selected Files ({bulkFiles.length})</span>
              <button
                className="clear-files-btn"
                onClick={clearBulkUpload}
                disabled={bulkUploading}
              >
                <FaTrash /> Clear All
              </button>
            </div>
            <div className="file-items">
              {bulkFiles.map((file, index) => (
                <div key={index} className="bulk-file-item">
                  <div className="file-info">
                    <span className="file-icon">📄</span>
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
                  </div>
                  <button
                    className="remove-file-btn"
                    onClick={() => removeBulkFile(index)}
                    disabled={bulkUploading}
                  >
                    <FaTimes />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {bulkError && (
          <div className="error-message">
            <FaExclamationTriangle />
            {bulkError}
          </div>
        )}

        <button
          className={`upload-btn ${bulkUploading ? 'loading' : ''}`}
          onClick={handleBulkUpload}
          disabled={bulkUploading || bulkFiles.length === 0 || !bulkBatchName.trim()}
        >
          {bulkUploading ? (
            <>
              <FaSpinner className="spinner" />
              Uploading... {bulkProgress}%
            </>
          ) : (
            <>
              <FaUpload />
              Upload Batch ({bulkFiles.length} files)
            </>
          )}
        </button>

        {bulkUploading && (
          <div className="progress-bar">
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${bulkProgress}%` }} />
            </div>
          </div>
        )}
      </div>

      {/* Batch Status */}
      {bulkStatus && (
        <div className="batch-status">
          <h3>📊 Batch Status: {bulkStatus.batch_name}</h3>
          <div className="status-summary">
            <div className="status-item">
              <span className="status-value">{bulkStatus.total_files}</span>
              <span className="status-label">Total Files</span>
            </div>
            <div className="status-item success">
              <span className="status-value">
                {bulkStatus.files?.filter(f => f.status === 'completed').length || 0}
              </span>
              <span className="status-label">✅ Processed</span>
            </div>
            {bulkStatus.files?.filter(f => f.status === 'failed').length > 0 && (
              <div className="status-item error">
                <span className="status-value">
                  {bulkStatus.files?.filter(f => f.status === 'failed').length}
                </span>
                <span className="status-label">❌ Failed</span>
              </div>
            )}
          </div>

          <div className="file-status-list">
            {bulkStatus.files?.map((file, index) => (
              <div key={index} className={`file-status ${file.status}`}>
                <span className="file-name">{file.name}</span>
                <span className={`status-badge ${file.status}`}>
                  {file.status === 'completed' && '✅ Done'}
                  {file.status === 'processing' && '⏳ Processing'}
                  {file.status === 'pending' && '⏳ Pending'}
                  {file.status === 'failed' && '❌ Failed'}
                </span>
              </div>
            ))}
          </div>

          <button
            className="clear-batch-btn"
            onClick={() => {
              clearBulkUpload();
              setUploadMode('single');
            }}
          >
            Clear Batch
          </button>
        </div>
      )}

      <div className="upload-info">
        <div className="info-card">
          <h4>ℹ️ How it works</h4>
          <ul>
            <li>Upload up to 50 files in a single batch</li>
            <li>Our AI will auto-extract data from each file</li>
            <li>You'll receive an email when all files are processed</li>
          </ul>
        </div>
      </div>
    </div>
  );

  // UploadManager.jsx - Updated Review View with Manual Entry Option

// Add state for manual entry mode


// Function to send to CarbonTally for manual extraction
// const handleSendToCarbonTally = async () => {
//   if (!fileId) {
//     toast.error('No file selected');
//     return;
//   }

//   setSendingToCarbonTally(true);
  
//   try {
//     const token = await getToken();
    
//     // Update document status to 'staff_review' and add to manual review queue
//     const response = await fetch(`${API_URL}/api/admin/documents/${fileId}/status`, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//         'Authorization': `Bearer ${token}`
//       },
//       body: JSON.stringify({
//         status: 'staff_review',
//         notes: 'Customer requested manual extraction'
//       })
//     });

//     if (response.ok) {
//       toast.success('📋 Document sent to CarbonTally team for manual extraction!');
//       toast('Our team will process your document within 24-48 hours.', {
//         icon: '⏳',
//         duration: 5000,
//       });
//       setManualEntryMode(true);
//       setDocumentStatus('staff_review');
//     } else {
//       const error = await response.json();
//       toast.error(error.detail || 'Failed to send for manual extraction');
//     }
//   } catch (error) {
//     console.error('Error sending to CarbonTally:', error);
//     toast.error('Failed to send document for manual extraction');
//   } finally {
//     setSendingToCarbonTally(false);
//   }
// };

// Updated Review View render function
const renderReviewView = () => {
  const isPdf = file?.type === 'application/pdf' || file?.name?.toLowerCase().endsWith('.pdf');
  const isImage = file?.type?.startsWith('image/') || file?.name?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp)$/);
  const isReady = documentStatus === 'ready_for_review';
  const isManualMode = manualEntryMode || documentStatus === 'staff_review';

  return (
    <div className="review-view">
      {/* Header */}
      <div className="review-header">
        <div className="review-header-left">
          <button className="back-btn" onClick={handleBackToUpload}>
            <FaArrowLeft /> Back
          </button>
          <div className="review-file-info">
            <span className="file-icon">
              {isPdf ? <FaFilePdf /> : isImage ? <FaImage /> : <FaFileUpload />}
            </span>
            <span className="file-name">{file?.name}</span>
            <span className="file-type-badge">{uploadType.toUpperCase()}</span>
          </div>
        </div>
        <div className="review-header-right">
          <span className={`status-badge ${documentStatus}`}>
            {documentStatus === 'processing' && <FaSpinner className="spinner-sm" />}
            {documentStatus === 'ready_for_review' && <FaCheckCircle />}
            {documentStatus === 'staff_review' && '👨‍💻 Staff Review'}
            {documentStatus === 'approved' && '✅ Approved'}
            {documentStatus === 'rejected' && '❌ Rejected'}
            {documentStatus === 'processing' ? 'Processing...' : 
             documentStatus === 'ready_for_review' ? 'Ready for Review' : 
             documentStatus === 'staff_review' ? 'Manual Extraction' :
             documentStatus}
          </span>
          {confidenceScore > 0 && documentStatus === 'ready_for_review' && (
            <span className={`confidence-badge ${confidenceScore > 0.7 ? 'high' : confidenceScore > 0.4 ? 'medium' : 'low'}`}>
              Confidence: {(confidenceScore * 100).toFixed(0)}%
            </span>
          )}
        </div>
      </div>

      {/* Split Screen */}
      <div className="review-split">
        {/* Left: Document Viewer */}
        <div className="review-left">
          <div className="viewer-container">
            {isPdf ? (
              <div style={getRotationStyle(pdfRotation)}>
                <Document
                  file={URL.createObjectURL(file)}
                  onLoadSuccess={({ numPages }) => setPdfNumPages(numPages)}
                  loading={<div className="pdf-loading"><FaSpinner className="spinner" /> Loading PDF...</div>}
                >
                  <Page
                    pageNumber={pdfPageNumber}
                    scale={pdfScale}
                    renderTextLayer={false}
                    renderAnnotationLayer={false}
                  />
                </Document>
              </div>
            ) : isImage ? (
              <img
                src={URL.createObjectURL(file)}
                alt="Document preview"
                className="image-preview"
                style={{
                  transform: `scale(${pdfScale}) rotate(${pdfRotation}deg)`,
                  transition: 'transform 0.3s ease'
                }}
              />
            ) : (
              <div className="file-preview">
                <FaFileUpload className="file-preview-icon" />
                <p>{file?.name}</p>
                <p className="file-preview-size">{(file?.size / 1024).toFixed(1)} KB</p>
                <p className="file-preview-hint">Preview not available for this file type</p>
              </div>
            )}
          </div>

          {/* Viewer Controls */}
          <div className="viewer-controls">
            <button onClick={() => setPdfScale(Math.max(0.5, pdfScale - 0.1))}>−</button>
            <span>{(pdfScale * 100).toFixed(0)}%</span>
            <button onClick={() => setPdfScale(Math.min(2.0, pdfScale + 0.1))}>+</button>
            
            <div className="rotation-controls">
              <button onClick={rotateLeft} className="rotate-btn" title="Rotate Left">↺</button>
              <button onClick={rotateRight} className="rotate-btn" title="Rotate Right">↻</button>
              {pdfRotation !== 0 && (
                <>
                  <button onClick={resetRotation} className="rotate-btn reset" title="Reset">⟲</button>
                  <span className="rotation-badge">{pdfRotation}°</span>
                </>
              )}
            </div>
            
            {isPdf && (
              <>
                <span className="page-info">
                  Page {pdfPageNumber} of {pdfNumPages || '?'}
                </span>
                <button
                  onClick={() => setPdfPageNumber(Math.max(1, pdfPageNumber - 1))}
                  disabled={pdfPageNumber <= 1}
                >
                  <FaArrowLeft />
                </button>
                <button
                  onClick={() => setPdfPageNumber(Math.min(pdfNumPages || 1, pdfPageNumber + 1))}
                  disabled={pdfPageNumber >= (pdfNumPages || 1)}
                >
                  <FaArrowRight />
                </button>
              </>
            )}
          </div>
        </div>

        {/* Right: Data Extraction Form */}
        <div className="review-right">
          <div className="extraction-form">
            <h3>📊 Extracted Data</h3>
            
            {/* Status messages */}
            {documentStatus === 'processing' && (
              <div className="processing-indicator">
                <FaSpinner className="spinner" />
                <p>AI is extracting data from your document...</p>
                <p className="processing-hint">This may take a few moments</p>
              </div>
            )}

            {documentStatus === 'staff_review' && (
              <div className="manual-notice">
                <div className="manual-notice-icon">👨‍💻</div>
                <div>
                  <strong>Manual Extraction Requested</strong>
                  <p>Our team will manually extract data from your document within 24-48 hours.</p>
                </div>
              </div>
            )}

            {/* Issues Warning */}
            {extractionIssues.length > 0 && documentStatus === 'ready_for_review' && (
              <div className="issues-warning">
                <FaExclamationTriangle />
                <div>
                  <strong>Extraction Issues Found:</strong>
                  <ul>
                    {extractionIssues.slice(0, 3).map((issue, i) => (
                      <li key={i}>{issue.message || issue}</li>
                    ))}
                    {extractionIssues.length > 3 && (
                      <li>+{extractionIssues.length - 3} more issues</li>
                    )}
                  </ul>
                </div>
              </div>
            )}

            {/* Manual Entry Form - Always editable */}
            <div className="form-grid">
              <div className="form-group">
                <label><FaCalendarAlt /> Billing Period Start *</label>
                <input
                  type="date"
                  value={reviewData.billing_start}
                  onChange={(e) => handleReviewChange('billing_start', e.target.value)}
                  placeholder="mm/dd/yyyy"
                  className={!reviewData.billing_start ? 'error' : ''}
                />
              </div>

              <div className="form-group">
                <label><FaCalendarAlt /> Reporting Year</label>
                <select
                  value={reviewData.reporting_year || new Date().getFullYear()}
                  onChange={(e) => handleReviewChange('reporting_year', e.target.value)}
                >
                  {[new Date().getFullYear(), new Date().getFullYear() - 1, new Date().getFullYear() - 2].map(y => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label><FaBolt /> Consumption (kWh or Litres) *</label>
                <input
                  type="number"
                  step="0.01"
                  value={reviewData.consumption}
                  onChange={(e) => handleReviewChange('consumption', e.target.value)}
                  placeholder="Enter consumption value"
                  className={(!reviewData.consumption || parseFloat(reviewData.consumption) <= 0) ? 'error' : ''}
                />
              </div>

              <div className="form-group">
                <label><FaBolt /> Fuel/Utility Type *</label>
                <select
                  value={reviewData.fuel_utility_type}
                  onChange={(e) => handleReviewChange('fuel_utility_type', e.target.value)}
                  className={!reviewData.fuel_utility_type ? 'error' : ''}
                >
                  <option value="">Select type...</option>
                  <option value="Diesel">Diesel</option>
                  <option value="Petrol">Petrol</option>
                  <option value="Electricity">Electricity</option>
                  <option value="Natural Gas">Natural Gas</option>
                </select>
              </div>

              <div className="form-group">
                <label><FaBuilding /> Facility</label>
                <select
                  value={selectedFacilityId}
                  onChange={(e) => handleFacilitySelect(e.target.value)}
                >
                  <option value="">Select facility...</option>
                  {facilities.map(f => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label><FaCar /> Asset (Vehicle/Meter) *</label>
                <input
                  type="text"
                  value={reviewData.asset_name}
                  onChange={(e) => handleReviewChange('asset_name', e.target.value)}
                  placeholder="e.g., Delivery Van"
                  className={!reviewData.asset_name ? 'error' : ''}
                />
                {selectedFacilityId && (
                  <div className="asset-suggestions">
                    {assets
                      .filter(a => a.facility_id === selectedFacilityId)
                      .slice(0, 5)
                      .map(a => (
                        <button
                          key={a.id}
                          className="asset-suggestion"
                          onClick={() => handleReviewChange('asset_name', a.name)}
                        >
                          {a.name}
                        </button>
                      ))}
                  </div>
                )}
              </div>

              <div className="form-group full-width">
                <label>📝 Notes</label>
                <textarea
                  value={staffNotes}
                  onChange={(e) => setStaffNotes(e.target.value)}
                  placeholder="Add any notes about this document..."
                  rows="2"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="review-actions">
              {documentStatus !== 'staff_review' && documentStatus !== 'approved' && (
                <button
                  className="btn-manual"
                  onClick={handleSendToCarbonTally}
                  disabled={sendingToCarbonTally}
                >
                  {sendingToCarbonTally ? (
                    <><FaSpinner className="spinner" /> Sending...</>
                  ) : (
                    <><FaUser /> Send to CarbonTally</>
                  )}
                </button>
              )}
              
              {documentStatus === 'staff_review' && (
                <span className="manual-badge">👨‍💻 Manual Extraction in Progress</span>
              )}

              {documentStatus !== 'approved' && documentStatus !== 'rejected' && (
                <>
                  <button className="btn-reject" onClick={handleReject} disabled={reviewSubmitting}>
                    <FaTimes /> Reject
                  </button>
                  <button className="btn-approve" onClick={handleApprove} disabled={reviewSubmitting}>
                    {reviewSubmitting ? (
                      <><FaSpinner className="spinner" /> Processing...</>
                    ) : (
                      <><FaCheckCircle /> Approve & Save</>
                    )}
                  </button>
                </>
              )}

              {(documentStatus === 'approved' || documentStatus === 'rejected') && (
                <button className="btn-back" onClick={handleBackToUpload}>
                  <FaArrowLeft /> Back to Upload
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
  // Review View (Split Screen) - Same as before
//   const renderReviewView = () => {
//     const isPdf = file?.type === 'application/pdf' || file?.name?.toLowerCase().endsWith('.pdf');
//     const isImage = file?.type?.startsWith('image/') || file?.name?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp)$/);
//     const isReady = documentStatus === 'ready_for_review';

//     return (
//       <div className="review-view">
//         <div className="review-header">
//           <div className="review-header-left">
//             <button className="back-btn" onClick={handleBackToUpload}>
//               <FaArrowLeft /> Back
//             </button>
//             <div className="review-file-info">
//               <span className="file-icon">
//                 {isPdf ? <FaFilePdf /> : isImage ? <FaImage /> : <FaFileUpload />}
//               </span>
//               <span className="file-name">{file?.name}</span>
//               <span className="file-type-badge">{uploadType.toUpperCase()}</span>
//             </div>
//           </div>
//           <div className="review-header-right">
//             <span className={`status-badge ${documentStatus}`}>
//               {documentStatus === 'processing' && <FaSpinner className="spinner-sm" />}
//               {documentStatus === 'ready_for_review' && <FaCheckCircle />}
//               {documentStatus === 'approved' && '✅ Approved'}
//               {documentStatus === 'rejected' && '❌ Rejected'}
//               {documentStatus === 'processing' ? 'Processing...' : 
//                documentStatus === 'ready_for_review' ? 'Ready for Review' : 
//                documentStatus}
//             </span>
//             {confidenceScore > 0 && (
//               <span className={`confidence-badge ${confidenceScore > 0.7 ? 'high' : confidenceScore > 0.4 ? 'medium' : 'low'}`}>
//                 Confidence: {(confidenceScore * 100).toFixed(0)}%
//               </span>
//             )}
//           </div>
//         </div>

//         <div className="review-split">
//           <div className="review-left">
//             <div className="viewer-container">
//                 {isPdf ? (
//                 <div style={getRotationStyle(pdfRotation)}>
//                     <Document
//                     file={URL.createObjectURL(file)}
//                     onLoadSuccess={({ numPages }) => setPdfNumPages(numPages)}
//                     loading={<div className="pdf-loading"><FaSpinner className="spinner" /> Loading PDF...</div>}
//                     >
//                     <Page
//                         pageNumber={pdfPageNumber}
//                         scale={pdfScale}
//                         renderTextLayer={false}
//                         renderAnnotationLayer={false}
//                     />
//                     </Document>
//                 </div>
//                 ) : isImage ? (
//                 <img
//                     src={URL.createObjectURL(file)}
//                     alt="Document preview"
//                     className="image-preview"
//                     style={{
//                     transform: `scale(${pdfScale}) rotate(${pdfRotation}deg)`,
//                     transition: 'transform 0.3s ease'
//                     }}
//                 />
//                 ) : (
//                 <div className="file-preview">
//                     <FaFileUpload className="file-preview-icon" />
//                     <p>{file?.name}</p>
//                     <p className="file-preview-size">{(file?.size / 1024).toFixed(1)} KB</p>
//                     <p className="file-preview-hint">Preview not available for this file type</p>
//                 </div>
//                 )}
//             </div>

//             {/* Viewer Controls - Updated with rotation buttons */}
//             <div className="viewer-controls">
//                 {/* Zoom controls */}
//                 <button onClick={() => setPdfScale(Math.max(0.5, pdfScale - 0.1))}>−</button>
//                 <span>{(pdfScale * 100).toFixed(0)}%</span>
//                 <button onClick={() => setPdfScale(Math.min(2.0, pdfScale + 0.1))}>+</button>
                
//                 {/* Rotation controls */}
//                 <div className="rotation-controls">
//                 <button 
//                     onClick={rotateLeft}
//                     className="rotate-btn"
//                     title="Rotate Left (90°)"
//                 >
//                     ↺
//                 </button>
//                 <button 
//                     onClick={rotateRight}
//                     className="rotate-btn"
//                     title="Rotate Right (90°)"
//                 >
//                     ↻
//                 </button>
//                 {pdfRotation !== 0 && (
//                     <button 
//                     onClick={resetRotation}
//                     className="rotate-btn reset"
//                     title="Reset Rotation"
//                     >
//                     ⟲
//                     </button>
//                 )}
//                 {pdfRotation !== 0 && (
//                     <span className="rotation-badge">{pdfRotation}°</span>
//                 )}
//                 </div>
                
//                 {/* Page navigation (PDF only) */}
//                 {isPdf && (
//                 <>
//                     <span className="page-info">
//                     Page {pdfPageNumber} of {pdfNumPages || '?'}
//                     </span>
//                     <button
//                     onClick={() => setPdfPageNumber(Math.max(1, pdfPageNumber - 1))}
//                     disabled={pdfPageNumber <= 1}
//                     >
//                     <FaArrowLeft />
//                     </button>
//                     <button
//                     onClick={() => setPdfPageNumber(Math.min(pdfNumPages || 1, pdfPageNumber + 1))}
//                     disabled={pdfPageNumber >= (pdfNumPages || 1)}
//                     >
//                     <FaArrowRight />
//                     </button>
//                 </>
//                 )}
//             </div>
//             </div>

//           <div className="review-right">
//             <div className="extraction-form">
//               <h3>📊 Extracted Data</h3>
              
//               {!isReady && documentStatus === 'processing' && (
//                 <div className="processing-indicator">
//                   <FaSpinner className="spinner" />
//                   <p>AI is extracting data from your document...</p>
//                   <p className="processing-hint">This may take a few moments</p>
//                 </div>
//               )}

//               {extractionIssues.length > 0 && (
//                 <div className="issues-warning">
//                   <FaExclamationTriangle />
//                   <div>
//                     <strong>Extraction Issues Found:</strong>
//                     <ul>
//                       {extractionIssues.slice(0, 3).map((issue, i) => (
//                         <li key={i}>{issue.message || issue}</li>
//                       ))}
//                       {extractionIssues.length > 3 && (
//                         <li>+{extractionIssues.length - 3} more issues</li>
//                       )}
//                     </ul>
//                   </div>
//                 </div>
//               )}

//               <div className="form-grid">
//                 <div className="form-group">
//                   <label><FaCalendarAlt /> Billing Period Start *</label>
//                   <input
//                     type="date"
//                     value={reviewData.billing_start}
//                     onChange={(e) => handleReviewChange('billing_start', e.target.value)}
//                     disabled={!isReady}
//                     className={!reviewData.billing_start && isReady ? 'error' : ''}
//                   />
//                 </div>

//                 <div className="form-group">
//                   <label><FaCalendarAlt /> Reporting Year</label>
//                   <select
//                     value={reviewData.reporting_year || new Date().getFullYear()}
//                     onChange={(e) => handleReviewChange('reporting_year', e.target.value)}
//                     disabled={!isReady}
//                   >
//                     {[new Date().getFullYear(), new Date().getFullYear() - 1, new Date().getFullYear() - 2].map(y => (
//                       <option key={y} value={y}>{y}</option>
//                     ))}
//                   </select>
//                 </div>

//                 <div className="form-group">
//                   <label><FaBolt /> Consumption (kWh or Litres) *</label>
//                   <input
//                     type="number"
//                     step="0.01"
//                     value={reviewData.consumption}
//                     onChange={(e) => handleReviewChange('consumption', e.target.value)}
//                     disabled={!isReady}
//                     placeholder="Enter consumption value"
//                     className={(!reviewData.consumption || parseFloat(reviewData.consumption) <= 0) && isReady ? 'error' : ''}
//                   />
//                 </div>

//                 <div className="form-group">
//                   <label><FaBolt /> Fuel/Utility Type *</label>
//                   <select
//                     value={reviewData.fuel_utility_type}
//                     onChange={(e) => handleReviewChange('fuel_utility_type', e.target.value)}
//                     disabled={!isReady}
//                     className={!reviewData.fuel_utility_type && isReady ? 'error' : ''}
//                   >
//                     <option value="">Select type...</option>
//                     <option value="Diesel">Diesel</option>
//                     <option value="Petrol">Petrol</option>
//                     <option value="Electricity">Electricity</option>
//                     <option value="Natural Gas">Natural Gas</option>
//                   </select>
//                 </div>

//                 <div className="form-group">
//                   <label><FaBuilding /> Facility</label>
//                   <select
//                     value={selectedFacilityId}
//                     onChange={(e) => handleFacilitySelect(e.target.value)}
//                     disabled={!isReady}
//                   >
//                     <option value="">Select facility...</option>
//                     {facilities.map(f => (
//                       <option key={f.id} value={f.id}>{f.name}</option>
//                     ))}
//                   </select>
//                 </div>

//                 <div className="form-group">
//                   <label><FaCar /> Asset (Vehicle/Meter) *</label>
//                   <input
//                     type="text"
//                     value={reviewData.asset_name}
//                     onChange={(e) => handleReviewChange('asset_name', e.target.value)}
//                     disabled={!isReady}
//                     placeholder="e.g., Delivery Van"
//                     className={!reviewData.asset_name && isReady ? 'error' : ''}
//                   />
//                   {selectedFacilityId && (
//                     <div className="asset-suggestions">
//                       {assets
//                         .filter(a => a.facility_id === selectedFacilityId)
//                         .slice(0, 5)
//                         .map(a => (
//                           <button
//                             key={a.id}
//                             className="asset-suggestion"
//                             onClick={() => handleReviewChange('asset_name', a.name)}
//                           >
//                             {a.name}
//                           </button>
//                         ))}
//                     </div>
//                   )}
//                 </div>

//                 <div className="form-group full-width">
//                   <label>📝 Notes</label>
//                   <textarea
//                     value={staffNotes}
//                     onChange={(e) => setStaffNotes(e.target.value)}
//                     disabled={!isReady}
//                     placeholder="Add any notes about this document..."
//                     rows="2"
//                   />
//                 </div>
//               </div>

//               {isReady && (
//                 <div className="review-actions">
//                   <button className="btn-reject" onClick={handleReject} disabled={reviewSubmitting}>
//                     <FaTimes /> Reject
//                   </button>
//                   <button className="btn-approve" onClick={handleApprove} disabled={reviewSubmitting}>
//                     {reviewSubmitting ? (
//                       <><FaSpinner className="spinner" /> Processing...</>
//                     ) : (
//                       <><FaCheckCircle /> Approve & Save</>
//                     )}
//                   </button>
//                 </div>
//               )}

//               {!isReady && documentStatus !== 'processing' && (
//                 <div className="review-actions">
//                   <button className="btn-back" onClick={handleBackToUpload}>
//                     <FaArrowLeft /> Back
//                   </button>
//                   <button className="btn-retry" onClick={() => pollDocumentStatus(fileId)}>
//                     <FaUndo /> Check Status
//                   </button>
//                 </div>
//               )}
//             </div>
//           </div>
//         </div>
//       </div>
//     );
//   };

  // Complete View
  const renderCompleteView = () => (
    <div className="complete-view">
      <div className="complete-card">
        <div className="complete-icon">✅</div>
        <h2>Document Processed Successfully!</h2>
        <p>The document has been approved and saved to your emissions records.</p>
        
        {completedData && (
          <div className="complete-details">
            <div className="detail-item">
              <span className="detail-label">Document ID:</span>
              <span className="detail-value">{completedData.document_id}</span>
            </div>
            {completedData.emission_id && (
              <div className="detail-item">
                <span className="detail-label">Emission Record ID:</span>
                <span className="detail-value">{completedData.emission_id}</span>
              </div>
            )}
            <div className="detail-item">
              <span className="detail-label">Status:</span>
              <span className="detail-value success">{completedData.status}</span>
            </div>
          </div>
        )}

        <div className="complete-actions">
          <button className="btn-primary" onClick={handleBackToUpload}>
            Upload Another Document
          </button>
          <button className="btn-secondary" onClick={() => window.location.reload()}>
            Go to Dashboard
          </button>
        </div>
      </div>
    </div>
  );

  // Main Render
  return (
    <div className="upload-manager">
      {activeStep === 'upload' && uploadMode === 'single' && renderSingleUploadView()}
      {activeStep === 'upload' && uploadMode === 'bulk' && renderBulkUploadView()}
      {activeStep === 'review' && renderReviewView()}
      {activeStep === 'complete' && renderCompleteView()}
    </div>
  );
};

export default UploadManager;