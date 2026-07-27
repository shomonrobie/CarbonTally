// ManualEntryCore.jsx - Shared component (reused by both frontend and admin)
import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import toast from 'react-hot-toast';
import {
  FaArrowLeft,
  FaArrowRight,
  FaSpinner,
  FaSave,
  FaCheckCircle,
  FaExclamationTriangle,
  FaFilePdf,
  FaImage,
  FaFileUpload,
  FaCalendarAlt,
  FaBolt,
  FaBuilding,
  FaCar,
  FaUser,
  FaEnvelope
} from 'react-icons/fa';

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ManualEntryCore = ({
  file,
  organization,
  isAdminMode = false, // ✅ Determines if this is for admin staff or customer
  onBack,
  onComplete,
  staffData = null // ✅ For admin mode - staff info
}) => {
  // File viewer state
  const [pdfNumPages, setPdfNumPages] = useState(null);
  const [pdfPageNumber, setPdfPageNumber] = useState(1);
  const [pdfScale, setPdfScale] = useState(1.0);
  const [pdfRotation, setPdfRotation] = useState(0);

  // Form state
  const [formData, setFormData] = useState({
    billing_start: '',
    reporting_year: new Date().getFullYear(),
    consumption: '',
    fuel_utility_type: '',
    facility_id: '',
    asset_name: '',
    notes: '',
    unit: 'kWh'
  });

  // UI State
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);
  const [draftId, setDraftId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [sectionsCompleted, setSectionsCompleted] = useState([]);
  const [facilities, setFacilities] = useState([]);
  const [assets, setAssets] = useState([]);
  const [selectedFacilityId, setSelectedFacilityId] = useState('');
  const [draftLoaded, setDraftLoaded] = useState(false);

  // Reference data for dropdowns
  const [fuelTypes, setFuelTypes] = useState([]);
  const [units, setUnits] = useState([]);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [customers, setCustomers] = useState([]); // ✅ For admin mode - customer selection

  const isPdf = file?.type === 'application/pdf' || file?.name?.toLowerCase().endsWith('.pdf');
  const isImage = file?.type?.startsWith('image/') || file?.name?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp)$/);

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  // ============================================
  // FETCH REFERENCE DATA
  // ============================================
  useEffect(() => {
    if (organization?.id) {
      fetchReferenceData();
      fetchFacilitiesAndAssets();
      
      // ✅ If admin mode, fetch customers
      if (isAdminMode) {
        fetchCustomers();
      }
    }
  }, [organization?.id]);

  const fetchReferenceData = async () => {
    setLoadingOptions(true);
    const token = await getToken();

    try {
      // Fetch fuel types
      const fuelResponse = await fetch(`${API_URL}/api/reference/fuel-types`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (fuelResponse.ok) {
        const data = await fuelResponse.json();
        setFuelTypes(data.fuel_types || []);
      }

      // Fetch units
      const unitResponse = await fetch(`${API_URL}/api/reference/units`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (unitResponse.ok) {
        const data = await unitResponse.json();
        setUnits(data.units || []);
      }
    } catch (error) {
      console.error('Error fetching reference data:', error);
    } finally {
      setLoadingOptions(false);
    }
  };

  const fetchFacilitiesAndAssets = async () => {
    try {
      const token = await getToken();
      
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
    }
  };

  // ✅ Admin mode - fetch customers
  const fetchCustomers = async () => {
    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/admin/customers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setCustomers(data.customers || []);
      }
    } catch (error) {
      console.error('Error fetching customers:', error);
    }
  };

  // ============================================
  // DRAFT MANAGEMENT
  // ============================================
  useEffect(() => {
    if (file?.id) {
      checkExistingDraft();
    }
  }, [file?.id]);

  const checkExistingDraft = async () => {
    try {
      const token = await getToken();
      const response = await fetch(
        `${API_URL}/api/drafts?file_id=${file.id}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      if (response.ok) {
        const data = await response.json();
        if (data.drafts && data.drafts.length > 0) {
          const draft = data.drafts[0];
          setDraftId(draft.id);
          setFormData({
            ...formData,
            ...draft.data,
            notes: draft.data.notes || ''
          });
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

  // ============================================
  // FORM HANDLING
  // ============================================
  const calculateProgress = (data) => {
    const sections = [
      'billing_start',
      'consumption',
      'fuel_utility_type',
      'asset_name'
    ];
    
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
    
    return { progress: progressValue, sections: completedSections };
  };

  const handleChange = (field, value) => {
    const newData = { ...formData, [field]: value };
    setFormData(newData);
    calculateProgress(newData);
  };

  const handleFacilitySelect = (facilityId) => {
    setSelectedFacilityId(facilityId);
    handleChange('facility_id', facilityId);
    handleChange('asset_name', '');
  };

  // ============================================
  // DRAFT ACTIONS
  // ============================================
  const saveDraft = async () => {
    if (!file?.id) {
      toast.error('No file associated with this entry');
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
          file_id: file.id,
          data: formData,
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

  const deleteDraft = async () => {
    if (!draftId) return;
    if (!window.confirm('Are you sure you want to discard this draft?')) return;

    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/drafts/${draftId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setDraftId(null);
        setProgress(0);
        setSectionsCompleted([]);
        toast.success('Draft discarded');
      }
    } catch (error) {
      console.error('Error deleting draft:', error);
      toast.error('Failed to delete draft');
    }
  };

  // ============================================
  // SUBMIT ACTIONS
  // ============================================
  const handleSubmit = async () => {
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
      
      if (draftId) {
        const response = await fetch(`${API_URL}/api/drafts/${draftId}/submit`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            ...formData,
            submitted_by: isAdminMode ? staffData?.id : null,
            submitted_by_email: isAdminMode ? staffData?.email : null,
            is_admin_submission: isAdminMode
          })
        });

        if (response.ok) {
          toast.success('✅ Data submitted successfully!');
          if (onComplete) onComplete();
        } else {
          const error = await response.json();
          toast.error(error.detail || 'Failed to submit');
        }
      } else {
        const saveResponse = await fetch(`${API_URL}/api/drafts/save`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            file_id: file.id,
            data: formData,
            progress: 100,
            sections_completed: ['billing_start', 'consumption', 'fuel_utility_type', 'asset_name']
          })
        });

        if (saveResponse.ok) {
          const result = await saveResponse.json();
          
          const submitResponse = await fetch(`${API_URL}/api/drafts/${result.draft_id}/submit`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              ...formData,
              submitted_by: isAdminMode ? staffData?.id : null,
              submitted_by_email: isAdminMode ? staffData?.email : null,
              is_admin_submission: isAdminMode
            })
          });

          if (submitResponse.ok) {
            toast.success('✅ Data submitted successfully!');
            if (onComplete) onComplete();
          }
        }
      }
    } catch (error) {
      console.error('Error submitting:', error);
      toast.error('Failed to submit data');
    } finally {
      setSubmitting(false);
    }
  };

  // ============================================
  // VIEWER CONTROLS
  // ============================================
  const rotateLeft = () => setPdfRotation(prev => (prev - 90 + 360) % 360);
  const rotateRight = () => setPdfRotation(prev => (prev + 90) % 360);
  const resetRotation = () => setPdfRotation(0);

  const getFileTypeIcon = () => {
    if (isPdf) return <FaFilePdf className="file-icon" />;
    if (isImage) return <FaImage className="file-icon" />;
    return <FaFileUpload className="file-icon" />;
  };

  const getSectionStatus = (section) => {
    return sectionsCompleted.includes(section) ? 'completed' : 'pending';
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="manual-entry-container">
      {/* Header */}
      <div className="manual-entry-header">
        <div className="header-left">
          <button className="back-btn" onClick={onBack}>
            <FaArrowLeft /> Back
          </button>
          <div className="file-info">
            {getFileTypeIcon()}
            <span className="file-name">{file?.name}</span>
            <span className="file-type-badge">{file?.file_type || 'DOCUMENT'}</span>
          </div>
        </div>
        <div className="header-right">
          {/* ✅ Show customer info in admin mode */}
          {isAdminMode && (
            <div className="customer-info">
              <span className="customer-badge">
                <FaUser /> {staffData?.email || 'Staff'}
              </span>
            </div>
          )}
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

      {/* Split Screen - Same as before */}
      {/* ... (keep the same split screen and form code) ... */}
      
      <div className="manual-entry-split">
        {/* Left: Document Viewer */}
        <div className="viewer-panel">
          {/* ... viewer code ... */}
        </div>

        {/* Right: Data Entry Form */}
        <div className="form-panel">
          <div className="form-scroll">
            <h3>✏️ Manual Data Entry</h3>
            
            {/* ✅ Admin mode indicator */}
            {isAdminMode && (
              <div className="admin-notice">
                <FaUser className="admin-icon" />
                <span>Entering data on behalf of customer</span>
              </div>
            )}

            {draftLoaded && (
              <div className="draft-notice">
                <FaSave className="draft-icon" />
                <span>Draft loaded from previous session</span>
                <button onClick={deleteDraft} className="discard-draft-btn">
                  Discard
                </button>
              </div>
            )}

            {/* Form Sections - Same as before, using database-driven options */}
            <div className="form-sections">
              {/* Section 1: General Info */}
              <div className="form-section">
                <div className="section-header">
                  <h4>📋 General Info</h4>
                  <span className={`section-status ${getSectionStatus('billing_start')}`}>
                    {getSectionStatus('billing_start') === 'completed' ? '✅' : '⏳'}
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
                  <span className={`section-status ${getSectionStatus('consumption')}`}>
                    {getSectionStatus('consumption') === 'completed' ? '✅' : '⏳'}
                  </span>
                </div>

                <div className="form-group">
                  <label>Units *</label>
                  <select
                    value={formData.unit}
                    onChange={(e) => handleChange('unit', e.target.value)}
                    disabled={loadingOptions}
                  >
                    <option value="">Select unit...</option>
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
                  <span className={`section-status ${getSectionStatus('fuel_utility_type') && getSectionStatus('asset_name') ? 'completed' : 'pending'}`}>
                    {getSectionStatus('fuel_utility_type') && getSectionStatus('asset_name') ? '✅' : '⏳'}
                  </span>
                </div>

                <div className="form-group">
                  <label><FaBolt /> Fuel/Utility Type *</label>
                  <select
                    value={formData.fuel_utility_type}
                    onChange={(e) => handleChange('fuel_utility_type', e.target.value)}
                    className={!formData.fuel_utility_type ? 'error' : ''}
                    disabled={loadingOptions}
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
                    </div>
                  )}
                </div>
              </div>

              {/* Section 4: Notes */}
              <div className="form-section">
                <div className="section-header">
                  <h4>📝 Notes</h4>
                </div>

                <div className="form-group">
                  <label>Additional Notes</label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => handleChange('notes', e.target.value)}
                    placeholder="Add any notes or comments about this entry..."
                    rows="3"
                  />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="form-actions">
              <div className="action-left">
                <button className="btn-back" onClick={onBack}>
                  <FaArrowLeft /> Back
                </button>
                {draftId && (
                  <button className="btn-discard" onClick={deleteDraft}>
                    🗑️ Discard
                  </button>
                )}
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
                  onClick={handleSubmit}
                  disabled={submitting || progress < 100}
                >
                  {submitting ? (
                    <><FaSpinner className="spinner" /> Submitting...</>
                  ) : (
                    <><FaCheckCircle /> Submit</>
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

export default ManualEntryCore;