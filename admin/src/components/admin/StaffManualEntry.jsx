// admin/src/components/StaffManualEntry.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { supabase } from '../supabaseClient';
import toast from 'react-hot-toast';
import {
  FaSpinner,
  FaCheckCircle,
  FaSave,
  FaArrowLeft,
  FaArrowRight,
  FaTimes,
  FaCalendarAlt,
  FaBolt,
  FaBuilding,
  FaCar,
  FaFilePdf,
  FaImage,
  FaFileUpload,
  FaExclamationTriangle,
  FaUser,
  FaClock,
  FaLayerGroup
} from 'react-icons/fa';
import './css/StaffManualEntry.css';

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const StaffManualEntry = ({ review, onComplete, onCancel }) => {
  // Review data
  const [file, setFile] = useState(null);
  const [fileUrl, setFileUrl] = useState(null);
  const [facilities, setFacilities] = useState([]);
  const [assets, setAssets] = useState([]);
  const [fuelTypes, setFuelTypes] = useState([]);
  const [units, setUnits] = useState([]);
  
  // Form state
  const [formData, setFormData] = useState({
    billing_start: '',
    reporting_year: new Date().getFullYear(),
    consumption: '',
    fuel_utility_type: '',
    facility_id: '',
    asset_name: '',
    staff_notes: '',
    unit: 'kWh'
  });

  const [selectedFacilityId, setSelectedFacilityId] = useState('');
  const [loading, setLoading] = useState(true);
  const [savingDraft, setSavingDraft] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [sectionsCompleted, setSectionsCompleted] = useState([]);
  
  // PDF viewer state
  const [pdfNumPages, setPdfNumPages] = useState(null);
  const [pdfPageNumber, setPdfPageNumber] = useState(1);
  const [pdfScale, setPdfScale] = useState(1.0);
  const [pdfRotation, setPdfRotation] = useState(0);
  
  // UI state
  const [showExtractionData, setShowExtractionData] = useState(true);
  const [draftId, setDraftId] = useState(null);
  const [draftLoaded, setDraftLoaded] = useState(false);
  const [batchProgress, setBatchProgress] = useState(null);

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  // Fetch file and data
  useEffect(() => {
    if (review) {
      fetchFileData();
      fetchReferenceData();
      fetchFacilitiesAndAssets();
      checkExistingDraft();
      fetchBatchProgress();
    }
  }, [review]);

  // Fetch file from URL
  const fetchFileData = async () => {
    try {
      if (review.file_url) {
        const response = await fetch(review.file_url);
        const blob = await response.blob();
        const fileObj = new File([blob], review.file_name, { type: blob.type });
        setFile(fileObj);
        setFileUrl(URL.createObjectURL(fileObj));
      }
    } catch (error) {
      console.error('Error fetching file:', error);
      toast.error('Failed to load document');
    }
  };

  // Fetch reference data
  const fetchReferenceData = async () => {
    const token = await getToken();

    try {
      const [fuelResponse, unitResponse] = await Promise.all([
        fetch(`${API_URL}/api/reference/fuel-types`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/reference/units`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (fuelResponse.ok) {
        const data = await fuelResponse.json();
        setFuelTypes(data.fuel_types || []);
      }

      if (unitResponse.ok) {
        const data = await unitResponse.json();
        setUnits(data.units || []);
      }
    } catch (error) {
      console.error('Error fetching reference data:', error);
    }
  };

  // Fetch facilities and assets
  const fetchFacilitiesAndAssets = async () => {
    const token = await getToken();

    try {
      const facResponse = await fetch(`${API_URL}/api/organizations/assets/facilities?limit=1000`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (facResponse.ok) {
        const data = await facResponse.json();
        setFacilities(data.facilities || []);
      }

      const assetResponse = await fetch(`${API_URL}/api/organizations/assets/?limit=1000`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (assetResponse.ok) {
        const data = await assetResponse.json();
        setAssets(data.assets || []);
      }
    } catch (error) {
      console.error('Error fetching facilities/assets:', error);
    } finally {
      setLoading(false);
    }
  };

  // Check for existing draft
  const checkExistingDraft = async () => {
    if (!review.id) return;

    try {
      const token = await getToken();
      const response = await fetch(
        `${API_URL}/api/drafts?file_id=${review.file_id}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      if (response.ok) {
        const data = await response.json();
        if (data.drafts && data.drafts.length > 0) {
          const draft = data.drafts[0];
          setDraftId(draft.id);
          setFormData(prev => ({
            ...prev,
            ...draft.data,
            staff_notes: draft.data.staff_notes || ''
          }));
          setProgress(draft.progress);
          setSectionsCompleted(draft.sections_completed || []);
          setDraftLoaded(true);
          
          if (draft.data.facility_id) {
            setSelectedFacilityId(draft.data.facility_id);
          }
          
          toast.success(`📝 Draft loaded (${draft.progress}% complete)`);
        }
      }
    } catch (error) {
      console.error('Error checking draft:', error);
    }
  };

  // Fetch batch progress
  const fetchBatchProgress = async () => {
    if (!review.batch_id) return;

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/batches/${review.batch_id}/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setBatchProgress(data);
      }
    } catch (error) {
      console.error('Error fetching batch progress:', error);
    }
  };

  // Load auto-extraction data
  const loadAutoExtractionData = () => {
    if (!review.auto_extraction_result) {
      toast.info('No auto-extraction data available');
      return;
    }

    const result = review.auto_extraction_result;
    const extractionResult = result.extraction_result || result;
    const dataStreams = extractionResult.data_streams || [];
    const firstStream = dataStreams[0] || {};
    const fields = firstStream.extracted_fields || {};

    setFormData(prev => ({
      ...prev,
      billing_start: fields.billing_start?.value || fields.billingStart?.value || '',
      consumption: fields.consumption?.value || fields.total_consumption?.value || '',
      fuel_utility_type: fields.fuel_utility_type?.value || fields.fuelType?.value || fields.fuel_type?.value || '',
      asset_name: fields.asset_name?.value || fields.assetName?.value || '',
      reporting_year: fields.reporting_year?.value || fields.reportingYear?.value || new Date().getFullYear()
    }));

    if (fields.asset_name?.value) {
      const matchedAsset = assets.find(a => a.name.toLowerCase() === fields.asset_name.value.toLowerCase());
      if (matchedAsset?.facility_id) {
        setSelectedFacilityId(matchedAsset.facility_id);
      }
    }

    toast.success('📋 Auto-extraction data loaded');
    calculateProgress(formData);
  };

  // Calculate progress
  const calculateProgress = (data) => {
    const sections = ['billing_start', 'consumption', 'fuel_utility_type', 'asset_name'];
    let completed = 0;
    const completedSections = [];
    
    sections.forEach(section => {
      if (data[section] && data[section].toString().trim() !== '') {
        completed++;
        completedSections.push(section);
      }
    });
    
    const progressValue = Math.round((completed / sections.length) * 100);
    setProgress(progressValue);
    setSectionsCompleted(completedSections);
  };

  // Handle form change
  const handleChange = (field, value) => {
    const newData = { ...formData, [field]: value };
    setFormData(newData);
    calculateProgress(newData);
  };

  // Handle facility select
  const handleFacilitySelect = (facilityId) => {
    setSelectedFacilityId(facilityId);
    handleChange('facility_id', facilityId);
    handleChange('asset_name', '');
  };

  // Save draft
  const saveDraft = async () => {
    if (!review.id) {
      toast.error('No review associated');
      return;
    }

    setSavingDraft(true);
    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/drafts/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          file_id: review.file_id,
          data: {
            ...formData,
            staff_notes: formData.staff_notes
          },
          progress: progress,
          sections_completed: sectionsCompleted
        })
      });

      if (response.ok) {
        const result = await response.json();
        setDraftId(result.draft_id);
        toast.success(`💾 Draft saved (${progress}% complete)`);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to save draft');
      }
    } catch (error) {
      console.error('Error saving draft:', error);
      toast.error('Failed to save draft');
    } finally {
      setSavingDraft(false);
    }
  };

  // Auto-save every 30 seconds
  useEffect(() => {
    if (!draftLoaded) return;
    
    const interval = setInterval(() => {
      if (progress > 0 && progress < 100) {
        saveDraft();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [formData, progress]);

  // Complete review
  const handleComplete = async () => {
    // Validate required fields
    if (!formData.billing_start) {
      toast.error('Please enter billing period start date');
      return;
    }
    if (!formData.consumption || parseFloat(formData.consumption) <= 0) {
      toast.error('Please enter a valid consumption value');
      return;
    }
    if (!formData.fuel_utility_type) {
      toast.error('Please select fuel/utility type');
      return;
    }
    if (!formData.asset_name) {
      toast.error('Please enter asset name');
      return;
    }

    setSubmitting(true);

    try {
      const token = await getToken();
      
      // Complete the review
      const response = await fetch(`${API_URL}/api/admin/reviews/${review.id}/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          notes: formData.staff_notes || 'Completed manual entry',
          extraction_data: {
            billing_start: formData.billing_start,
            consumption: parseFloat(formData.consumption),
            fuel_utility_type: formData.fuel_utility_type,
            asset_name: formData.asset_name,
            facility_id: formData.facility_id,
            reporting_year: formData.reporting_year || new Date().getFullYear(),
            unit: formData.unit
          }
        })
      });

      if (response.ok) {
        toast.success('✅ Review completed and sent to customer!');
        if (onComplete) onComplete();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to complete review');
      }
    } catch (error) {
      console.error('Error completing review:', error);
      toast.error('Failed to complete review');
    } finally {
      setSubmitting(false);
    }
  };

  // Reject review
  const handleReject = async () => {
    if (!window.confirm('Are you sure you want to reject this document?')) return;

    const reason = window.prompt('Please enter a reason for rejection:');
    if (reason === null) return; // User cancelled

    setSubmitting(true);

    try {
      const token = await getToken();
      
      const response = await fetch(`${API_URL}/api/admin/reviews/${review.id}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ reason })
      });

      if (response.ok) {
        toast.success('❌ Review rejected');
        if (onComplete) onComplete();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to reject review');
      }
    } catch (error) {
      console.error('Error rejecting review:', error);
      toast.error('Failed to reject review');
    } finally {
      setSubmitting(false);
    }
  };

  // Rotation controls
  const rotateLeft = () => setPdfRotation(prev => (prev - 90 + 360) % 360);
  const rotateRight = () => setPdfRotation(prev => (prev + 90) % 360);
  const resetRotation = () => setPdfRotation(0);

  const getRotationStyle = (rotation) => ({
    transform: `rotate(${rotation}deg)`,
    transition: 'transform 0.3s ease'
  });

  const isPdf = file?.type === 'application/pdf' || file?.name?.toLowerCase().endsWith('.pdf');
  const isImage = file?.type?.startsWith('image/') || file?.name?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp)$/);

  if (loading) {
    return (
      <div className="staff-manual-entry">
        <div className="loading-state">
          <FaSpinner className="spinner" />
          <p>Loading document...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="staff-manual-entry">
      {/* Header */}
      <div className="entry-header">
        <div className="header-left">
          <button className="back-btn" onClick={onCancel}>
            <FaArrowLeft /> Back
          </button>
          <div className="file-info">
            {isPdf ? <FaFilePdf className="file-icon" /> : isImage ? <FaImage className="file-icon" /> : <FaFileUpload className="file-icon" />}
            <span className="file-name">{review?.file_name}</span>
            <span className="org-name">🏢 {review?.organization_name || 'N/A'}</span>
          </div>
        </div>
        <div className="header-right">
          <div className="progress-indicator">
            <span className="progress-label">{progress}% Complete</span>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          </div>
          <button
            className="save-draft-btn"
            onClick={saveDraft}
            disabled={savingDraft}
          >
            {savingDraft ? <FaSpinner className="spinner" /> : <FaSave />}
            {savingDraft ? 'Saving...' : 'Save Draft'}
          </button>
        </div>
      </div>

      {/* Batch Context */}
      {batchProgress && (
        <div className="batch-context">
          <div className="batch-info">
            <span className="batch-name">
              <FaLayerGroup /> {batchProgress.batch_name}
            </span>
            <span className="batch-progress">
              Progress: {batchProgress.percentage || 0}% ({batchProgress.processed_files || 0}/{batchProgress.total_files || 0} files)
            </span>
            <span className="batch-status">
              Status: {batchProgress.status || 'Processing'}
            </span>
          </div>
          <div className="batch-progress-bar">
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${batchProgress.percentage || 0}%` }} />
            </div>
          </div>
        </div>
      )}

      {/* Split Screen */}
      <div className="entry-split">
        {/* Left: Document Viewer */}
        <div className="viewer-panel">
          <div className="viewer-container">
            {isPdf && fileUrl ? (
              <div style={getRotationStyle(pdfRotation)}>
                <Document
                  file={fileUrl}
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
            ) : isImage && fileUrl ? (
              <img
                src={fileUrl}
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
                <p>{review?.file_name}</p>
                <p className="file-preview-hint">Preview not available</p>
              </div>
            )}
          </div>

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

          {/* Customer Notes */}
          {review?.customer_notes && (
            <div className="customer-notes">
              <div className="notes-header">
                <FaUser /> Customer Note
              </div>
              <p>{review.customer_notes}</p>
            </div>
          )}
        </div>

        {/* Right: Data Entry Form */}
        <div className="form-panel">
          <div className="form-scroll">
            <div className="form-header">
              <h3>📝 Manual Data Entry</h3>
              {review?.auto_extraction_result && (
                <button
                  className="load-auto-btn"
                  onClick={loadAutoExtractionData}
                >
                  🤖 Load Auto-Data
                </button>
              )}
              {draftLoaded && (
                <span className="draft-badge">
                  <FaSave /> Draft
                </span>
              )}
            </div>

            <div className="form-sections">
              {/* Section 1: General Info */}
              <div className="form-section">
                <div className="section-header">
                  <h4>📋 General Info</h4>
                  <span className={`section-status ${sectionsCompleted.includes('billing_start') ? 'completed' : 'pending'}`}>
                    {sectionsCompleted.includes('billing_start') ? '✅' : '⏳'}
                  </span>
                </div>

                <div className="form-group">
                  <label><FaCalendarAlt /> Billing Period Start *</label>
                  <input
                    type="date"
                    value={formData.billing_start}
                    onChange={(e) => handleChange('billing_start', e.target.value)}
                    className={!formData.billing_start ? 'error' : ''}
                  />
                </div>

                <div className="form-group">
                  <label>Reporting Year</label>
                  <select
                    value={formData.reporting_year}
                    onChange={(e) => handleChange('reporting_year', parseInt(e.target.value))}
                  >
                    {[new Date().getFullYear(), new Date().getFullYear() - 1, new Date().getFullYear() - 2].map(y => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Section 2: Consumption */}
              <div className="form-section">
                <div className="section-header">
                  <h4>⚡ Consumption</h4>
                  <span className={`section-status ${sectionsCompleted.includes('consumption') ? 'completed' : 'pending'}`}>
                    {sectionsCompleted.includes('consumption') ? '✅' : '⏳'}
                  </span>
                </div>

                <div className="form-group">
                  <label>Units *</label>
                  <select
                    value={formData.unit}
                    onChange={(e) => handleChange('unit', e.target.value)}
                  >
                    {units.map(unit => (
                      <option key={unit.id} value={unit.code}>
                        {unit.name} {unit.symbol ? `(${unit.symbol})` : ''}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Consumption Value *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.consumption}
                    onChange={(e) => handleChange('consumption', e.target.value)}
                    placeholder="Enter consumption value"
                    className={(!formData.consumption || parseFloat(formData.consumption) <= 0) ? 'error' : ''}
                  />
                </div>
              </div>

              {/* Section 3: Activity */}
              <div className="form-section">
                <div className="section-header">
                  <h4>🏭 Activity</h4>
                  <span className={`section-status ${sectionsCompleted.includes('fuel_utility_type') && sectionsCompleted.includes('asset_name') ? 'completed' : 'pending'}`}>
                    {sectionsCompleted.includes('fuel_utility_type') && sectionsCompleted.includes('asset_name') ? '✅' : '⏳'}
                  </span>
                </div>

                <div className="form-group">
                  <label><FaBolt /> Fuel/Utility Type *</label>
                  <select
                    value={formData.fuel_utility_type}
                    onChange={(e) => handleChange('fuel_utility_type', e.target.value)}
                    className={!formData.fuel_utility_type ? 'error' : ''}
                  >
                    <option value="">Select type...</option>
                    {fuelTypes.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label} {type.reporting_year ? `(${type.reporting_year})` : ''}
                      </option>
                    ))}
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
                      <option key={f.id} value={f.id}>
                        {f.name} {f.city ? `(${f.city})` : ''}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label><FaCar /> Asset (Vehicle/Meter) *</label>
                  <input
                    type="text"
                    value={formData.asset_name}
                    onChange={(e) => handleChange('asset_name', e.target.value)}
                    placeholder="e.g., Delivery Van"
                    className={!formData.asset_name ? 'error' : ''}
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
                            onClick={() => handleChange('asset_name', a.name)}
                          >
                            {a.name}
                          </button>
                        ))}
                      }
                    </div>
                  )}
                </div>
              </div>

              {/* Section 4: Notes */}
              <div className="form-section">
                <div className="section-header">
                  <h4>📝 Staff Notes</h4>
                </div>

                <div className="form-group">
                  <textarea
                    value={formData.staff_notes}
                    onChange={(e) => handleChange('staff_notes', e.target.value)}
                    placeholder="Add any notes about this review..."
                    rows="3"
                  />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="form-actions">
              <div className="action-left">
                <button className="btn-reject" onClick={handleReject} disabled={submitting}>
                  <FaTimes /> Reject
                </button>
                <button className="btn-back" onClick={onCancel}>
                  Back
                </button>
              </div>
              <div className="action-right">
                <button
                  className="btn-save"
                  onClick={saveDraft}
                  disabled={savingDraft}
                >
                  {savingDraft ? <FaSpinner className="spinner" /> : <FaSave />}
                  {savingDraft ? 'Saving...' : 'Save Draft'}
                </button>
                <button
                  className="btn-submit"
                  onClick={handleComplete}
                  disabled={submitting || progress < 100}
                >
                  {submitting ? (
                    <><FaSpinner className="spinner" /> Submitting...</>
                  ) : (
                    <><FaCheckCircle /> Complete & Send</>
                  )}
                </button>
              </div>
            </div>

            {progress < 100 && (
              <div className="form-hint">
                <FaExclamationTriangle />
                <span>
                  {100 - progress}% of fields remaining. Please complete all required fields.
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StaffManualEntry;