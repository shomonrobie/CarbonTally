// frontend/src/components/ManualEntryView.jsx
import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
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
  FaUser
} from 'react-icons/fa';
import '../css/ManualEntry.css';

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const ManualEntryView = ({
  file,
  isAdminMode = false,
  staffData = null,
  onBack,
  onSubmit,
  
  // From hook
  formData,
  progress,
  sectionsCompleted,
  draftId,
  draftLoaded,
  loading,
  submitting,
  savingDraft,
  facilities,
  assets,
  selectedFacilityId,
  fuelTypes,
  units,
  loadingOptions,
  pdfNumPages,
  pdfPageNumber,
  pdfScale,
  pdfRotation,
  setPdfNumPages,
  setPdfPageNumber,
  setPdfScale,
  handleChange,
  handleFacilitySelect,
  saveDraft,
  deleteDraft,
  rotateLeft,
  rotateRight,
  resetRotation,
  getSectionStatus
}) => {
  // ✅ Create file URL only once
  const [fileUrl, setFileUrl] = useState(null);

  useEffect(() => {
    if (file) {
      const url = URL.createObjectURL(file);
      setFileUrl(url);
      return () => {
        if (url) URL.revokeObjectURL(url);
      };
    }
  }, [file]);

  // ✅ Check if file is loaded
  if (!file || !fileUrl) {
    return (
      <div className="manual-entry-container">
        <div className="loading-state">
          <FaSpinner className="spinner" />
          <p>Loading document...</p>
        </div>
      </div>
    );
  }

  const isPdf = file.type === 'application/pdf' || file.name?.toLowerCase().endsWith('.pdf');
  const isImage = file.type?.startsWith('image/') || file.name?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp)$/);

  const getFileTypeIcon = () => {
    if (isPdf) return <FaFilePdf className="file-icon" />;
    if (isImage) return <FaImage className="file-icon" />;
    return <FaFileUpload className="file-icon" />;
  };

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
            <span className="file-name">{file.name}</span>
            <span className="file-type-badge">{file.file_type || 'DOCUMENT'}</span>
          </div>
        </div>
        <div className="header-right">
          {isAdminMode && staffData && (
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

      {/* Split Screen */}
      <div className="manual-entry-split">
        {/* Left: Document Viewer */}
        <div className="viewer-panel">
          <div className="viewer-container">
            {isPdf ? (
              <div style={{ transform: `rotate(${pdfRotation}deg)`, transition: 'transform 0.3s ease' }}>
                <Document
                  file={fileUrl}
                  onLoadSuccess={({ numPages }) => setPdfNumPages(numPages)}
                  loading={<div className="pdf-loading"><FaSpinner className="spinner" /> Loading PDF...</div>}
                  error={<div className="pdf-error">Failed to load PDF. Please try again.</div>}
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
                <p>{file.name}</p>
                <p className="file-preview-size">{(file.size / 1024).toFixed(1)} KB</p>
                <p className="file-preview-hint">Preview not available for this file type</p>
              </div>
            )}
          </div>

          <div className="viewer-controls">
            <button onClick={() => setPdfScale(Math.max(0.5, pdfScale - 0.1))} disabled={!isPdf && !isImage}>−</button>
            <span>{(pdfScale * 100).toFixed(0)}%</span>
            <button onClick={() => setPdfScale(Math.min(2.0, pdfScale + 0.1))} disabled={!isPdf && !isImage}>+</button>
            
            <div className="rotation-controls">
              <button onClick={rotateLeft} className="rotate-btn" title="Rotate Left" disabled={!isPdf && !isImage}>↺</button>
              <button onClick={rotateRight} className="rotate-btn" title="Rotate Right" disabled={!isPdf && !isImage}>↻</button>
              {pdfRotation !== 0 && (
                <>
                  <button onClick={resetRotation} className="rotate-btn reset" title="Reset" disabled={!isPdf && !isImage}>⟲</button>
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

        {/* Right: Data Entry Form */}
        <div className="form-panel">
          <div className="form-scroll">
            <h3>✏️ Manual Data Entry</h3>
            
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
                  onClick={onSubmit}
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

export default ManualEntryView;