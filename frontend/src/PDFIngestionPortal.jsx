// src/PDFIngestionPortal.jsx

import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import axios from 'axios';
import toast from 'react-hot-toast';
import { FaSpinner, FaCheck, FaExclamationTriangle, FaSync, FaFilePdf, FaEye, FaEyeSlash } from 'react-icons/fa';

import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';
import './css/PDFIngestionPortal.css';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

export default function PDFIngestionPortal({ file, dataType, organizationId, onBack, onApprove, onPurge }) {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [extractionData, setExtractionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [extractionProgress, setExtractionProgress] = useState(0);
  const [extractionStatus, setExtractionStatus] = useState('initializing');
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [specialInstructions, setSpecialInstructions] = useState('');
  const [sendingNote, setSendingNote] = useState(false);
  const [noteSent, setNoteSent] = useState(false);
  const [repairStatus, setRepairStatus] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [manualEntryMode, setManualEntryMode] = useState(false);

  // Auto-process the PDF when component mounts
  useEffect(() => {
    processPDF();
  }, []);

  const processPDF = async () => {
    try {
      setLoading(true);
      setExtractionStatus('uploading');
      setExtractionProgress(10);
      toast.info('📤 Uploading PDF...');

      const formData = new FormData();
      formData.append('file', file);
      formData.append('data_type', dataType);
      formData.append('organization_id', organizationId || '');

      const isImage = file.type.startsWith('image/');
      const endpoint = isImage ? '/upload-image' : '/upload-pdf';

      setExtractionStatus('processing');
      setExtractionProgress(30);

      // Step 1: Try extraction first
      const response = await axios.post(`${process.env.REACT_APP_API_URL}${endpoint}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setExtractionProgress(30 + (percentCompleted * 0.4));
        }
      });

      setExtractionProgress(90);
      setExtractionStatus('finalizing');

      const result = response.data;

      // Step 2: Check if extraction succeeded
      if (result.status === 'success' || result.status === 'auto_extracted') {
        setExtractionProgress(100);
        setExtractionStatus('complete');
        setExtractionData(result);
        setLoading(false);
        toast.success('✅ PDF processed successfully!');
        return;
      }

      // Step 3: If extraction failed or needs review, check if repair is needed
      if (result.status === 'manual_review_required' || result.status === 'error') {
        // Check if this is likely a scanned/corrupted PDF
        const isScanned = result.extraction_issues?.some(i => 
          i.type === 'no_text' || 
          i.type === 'low_confidence' ||
          i.message?.toLowerCase().includes('scan') ||
          i.message?.toLowerCase().includes('ocr')
        );

        if (isScanned || result.extraction_summary?.confidence_score < 0.3) {
          // 🔧 Auto-repair needed
          setExtractionStatus('repairing');
          setExtractionProgress(50);
          toast.info('🔧 Your PDF appears to be scanned/corrupted. We\'re repairing it for carbon data extraction...');

          // Try to repair the PDF
          const repairFormData = new FormData();
          repairFormData.append('file', file);

          const repairResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/repair-pdf`, {
            method: 'POST',
            body: repairFormData,
          });

          setExtractionProgress(75);

          if (repairResponse.ok) {
            const repairResult = await repairResponse.json();

            if (repairResult.status === 'success') {
              setRepairStatus({
                status: 'success',
                message: '✅ PDF repaired successfully!',
                repairedUrl: repairResult.repaired_url,
                pages: repairResult.pages
              });

              // Step 4: Try extraction again with repaired PDF
              setExtractionStatus('re-extracting');
              setExtractionProgress(80);
              toast.info('📊 Re-extracting data from repaired PDF...');

              // Download the repaired file
              const downloadResponse = await fetch(repairResult.repaired_url);
              const blob = await downloadResponse.blob();
              const repairedFile = new File([blob], `repaired_${file.name}`, {
                type: 'application/pdf'
              });

              // Re-upload the repaired file
              const retryFormData = new FormData();
              retryFormData.append('file', repairedFile);
              retryFormData.append('data_type', dataType);
              retryFormData.append('organization_id', organizationId || '');

              const retryResponse = await axios.post(
                `${process.env.REACT_APP_API_URL}${endpoint}`,
                retryFormData,
                { headers: { 'Content-Type': 'multipart/form-data' } }
              );

              setExtractionProgress(95);
              const retryResult = retryResponse.data;

              if (retryResult.status === 'success' || retryResult.status === 'auto_extracted') {
                setExtractionProgress(100);
                setExtractionStatus('complete');
                setExtractionData(retryResult);
                setLoading(false);
                toast.success('✅ PDF repaired and extracted successfully!');
                return;
              } else {
                // Even after repair, extraction failed
                setExtractionStatus('manual_required');
                setError({
                  message: 'Auto-extraction still failed after repair. Please enter data manually.',
                  technical: 'Even after OCR repair, the system could not extract structured data.',
                  extractionIssues: retryResult.extraction_issues || [],
                  extractionSummary: retryResult.extraction_summary || {}
                });
                toast.warning('⚠️ Please enter data manually');
                setLoading(false);
                return;
              }
            } else {
              // Repair failed
              setExtractionStatus('repair_failed');
              setError({
                message: 'PDF repair failed. The file may be corrupted or encrypted.',
                technical: repairResult.message || 'Unknown repair error',
                extractionIssues: [],
                extractionSummary: {}
              });
              toast.error('❌ PDF repair failed');
              setLoading(false);
              return;
            }
          } else {
            // Repair endpoint error
            setExtractionStatus('repair_failed');
            setError({
              message: 'Unable to repair PDF. Please try a different file or enter data manually.',
              technical: 'Repair service returned an error',
              extractionIssues: [],
              extractionSummary: {}
            });
            toast.error('❌ PDF repair service unavailable');
            setLoading(false);
            return;
          }
        } else {
          // Not a scanned PDF, but still needs manual review
          setExtractionData(result);
          setExtractionProgress(100);
          setExtractionStatus('complete');
          setLoading(false);
        }
      }
    } catch (err) {
      console.error("File extraction failed:", err);

      let errorMsg = "Failed to extract data from file.";
      let technicalDetails = "";
      let userFriendlyMessage = "";
      let extractionIssues = [];
      let extractionSummary = {};

      if (err.response?.data) {
        const data = err.response.data;

        if (data.extraction_issues) {
          extractionIssues = data.extraction_issues;
        }
        if (data.extraction_summary) {
          extractionSummary = data.extraction_summary;
        }

        if (typeof data === 'string') {
          errorMsg = data;
          technicalDetails = data;
          userFriendlyMessage = "Our system encountered an issue while processing your file. Please try again or contact support.";
        } else if (data.detail) {
          errorMsg = data.detail;
          technicalDetails = data.detail;
          userFriendlyMessage = data.user_message || "We're having trouble processing this file. Please ensure it's a valid document and try again.";
        } else if (data.error) {
          errorMsg = data.error;
          technicalDetails = data.error;
          userFriendlyMessage = data.user_message || "Something went wrong. Please try uploading a different file.";
        } else {
          errorMsg = "Unknown error occurred";
          technicalDetails = JSON.stringify(data);
          userFriendlyMessage = "An unexpected error occurred. Please try again or contact support.";
        }
      } else if (err.message) {
        errorMsg = err.message;
        technicalDetails = err.message;
        userFriendlyMessage = "Network error. Please check your connection and try again.";
      }

      // Check if this is a scanned PDF that needs repair
      if (err.message?.toLowerCase().includes('scan') || err.message?.toLowerCase().includes('ocr')) {
        setExtractionStatus('repair_needed');
        setError({
          message: '📄 This appears to be a scanned document. We recommend repairing it first.',
          technical: technicalDetails,
          originalError: errorMsg,
          extractionIssues: extractionIssues,
          extractionSummary: extractionSummary
        });
      } else {
        setExtractionStatus('error');
        setError({
          message: userFriendlyMessage,
          technical: technicalDetails,
          originalError: errorMsg,
          timestamp: new Date().toISOString(),
          fileInfo: {
            name: file.name,
            size: file.size,
            type: file.type
          },
          extractionIssues: extractionIssues,
          extractionSummary: extractionSummary
        });
      }

      toast.error(userFriendlyMessage);
      setLoading(false);
    }
  };

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const handleSendNote = async () => {
    if (!specialInstructions.trim() || !extractionData?.review_id) return;

    setSendingNote(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/add-manual-review-note`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          review_id: extractionData.review_id,
          special_instructions: specialInstructions.trim()
        })
      });

      if (response.ok) {
        setNoteSent(true);
        setSpecialInstructions('');
        toast.success('✅ Note sent to our team!');
      }
    } catch (error) {
      console.error('Failed to send note:', error);
      toast.error('Failed to send note');
    } finally {
      setSendingNote(false);
    }
  };

  const handleFieldUpdate = (streamId, fieldName, newValue) => {
    setExtractionData(prev => {
      if (!prev) return prev;
      const updated = { ...prev };
      const stream = updated.data_streams.find(s => s.stream_id === streamId);
      if (stream && stream.extracted_fields[fieldName]) {
        stream.extracted_fields[fieldName].value = newValue;
        stream.extracted_fields[fieldName].status = "manually_corrected";
      }
      return updated;
    });
  };

  const handleAssetMapping = (streamId, assetName) => {
    setExtractionData(prev => {
      if (!prev) return prev;
      const updated = { ...prev };
      const stream = updated.data_streams.find(s => s.stream_id === streamId);
      if (stream) {
        stream.asset_mapping.matched_asset_id = assetName;
        if (stream.errors) {
          stream.errors = stream.errors.filter(e => e.field !== "asset_mapping");
          if (stream.errors.length === 0) stream.status = "verified";
        }
      }
      return updated;
    });
  };

  const handleApprove = async () => {
    const hasErrors = extractionData?.data_streams?.some(s => s.status === "error");
    if (hasErrors) {
      toast.error("Please resolve all errors before approving");
      return;
    }

    try {
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/approve-pdf-batch`, {
        batch_id: extractionData.batch_id,
        data_streams: extractionData.data_streams,
        organization_id: organizationId || 'mock-org-id'
      });

      toast.success("Batch approved and committed to database!");
      onApprove(extractionData);
    } catch (err) {
      console.error("Batch approval failed:", err);
      toast.error("Failed to approve batch");
    }
  };

  const handlePurge = () => {
    if (window.confirm("Are you sure you want to purge this batch? All extracted data will be lost.")) {
      onPurge();
    }
  };

  // 1. Loading State with Auto-Repair Progress
  if (loading) {
    const progressPercentage = Math.min(extractionProgress, 100);
    const statusMessages = {
      initializing: 'Initializing extraction engine...',
      uploading: 'Uploading file to secure storage...',
      processing: 'Extracting data from document...',
      repairing: '🔧 Your PDF appears to be scanned/corrupted. We\'re repairing it for carbon data extraction...',
      're-extracting': '📊 Re-extracting data from repaired PDF...',
      finalizing: 'Finalizing extraction results...',
      complete: 'Extraction complete!'
    };

    const isRepairing = ['repairing', 're-extracting'].includes(extractionStatus);
    const isRepairSuccess = repairStatus?.status === 'success';

    return (
      <div className="ingestion-portal">
        <div className="loading-container">
          <div className="loading-card">
            {/* Status Icon */}
            <div className="loading-icon">
              {isRepairing ? (
                <FaSync className="spinner" />
              ) : isRepairSuccess ? (
                <FaCheck className="success-icon" />
              ) : (
                <div className="spinner-ring" />
              )}
            </div>

            {/* Status Message */}
            <h3 className="loading-title">
              {isRepairing ? '🔧 Repairing Document...' : '📄 Processing Document...'}
            </h3>
            <p className="loading-message">
              {statusMessages[extractionStatus] || 'Processing...'}
            </p>

            {/* Progress Bar */}
            <div className="progress-container">
              <div className="progress-bar-track">
                <div
                  className={`progress-bar-fill ${isRepairing ? 'repairing' : ''} ${isRepairSuccess ? 'success' : ''}`}
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
              <span className="progress-text">{Math.round(progressPercentage)}%</span>
            </div>

            {/* Repair Status Details */}
            {isRepairing && (
              <div className="repair-status-details">
                <p className="repair-detail-text">
                  {extractionStatus === 'repairing' 
                    ? '🔄 Adding OCR text layer to make document searchable...' 
                    : '📊 Extracting carbon data from repaired document...'}
                </p>
                <div className="repair-steps">
                  <div className={`step ${extractionProgress >= 50 ? 'active' : ''}`}>
                    <span className="step-number">1</span>
                    <span className="step-label">Detect Issue</span>
                  </div>
                  <div className={`step ${extractionProgress >= 70 ? 'active' : ''}`}>
                    <span className="step-number">2</span>
                    <span className="step-label">Repair PDF</span>
                  </div>
                  <div className={`step ${extractionProgress >= 85 ? 'active' : ''}`}>
                    <span className="step-number">3</span>
                    <span className="step-label">Extract Data</span>
                  </div>
                  <div className={`step ${extractionProgress >= 100 ? 'active' : ''}`}>
                    <span className="step-number">4</span>
                    <span className="step-label">Complete</span>
                  </div>
                </div>
              </div>
            )}

            {/* File Info */}
            <p className="file-info">
              File: {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </p>

            {/* Cancel Button */}
            {!isRepairing && (
              <button onClick={onBack} className="cancel-btn">
                Cancel
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // 2. Manual Entry Mode (when repair fails)
  if (manualEntryMode) {
    return (
      <div className="ingestion-portal">
        <div className="manual-entry-container">
          <div className="manual-entry-card">
            <div className="manual-entry-header">
              <FaExclamationTriangle className="warning-icon-large" />
              <h2>✏️ Manual Data Entry</h2>
              <p>Auto-extraction failed. Please enter the data from your document manually.</p>
            </div>

            <div className="manual-entry-form">
              <div className="form-group">
                <label>📅 Billing Period Start</label>
                <input
                  type="date"
                  className="form-input"
                  placeholder="Select date"
                />
              </div>

              <div className="form-group">
                <label>⚡ Consumption (kWh or Litres)</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input"
                  placeholder="Enter consumption value"
                />
              </div>

              <div className="form-group">
                <label>🏢 Asset / Vehicle Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g., Vehicle ABC-123 or Meter #456"
                />
              </div>

              <div className="form-group">
                <label>⛽ Fuel / Utility Type</label>
                <select className="form-input">
                  <option value="">Select type...</option>
                  <option value="Diesel">Diesel</option>
                  <option value="Petrol">Petrol</option>
                  <option value="Electricity">Electricity</option>
                  <option value="Natural Gas">Natural Gas</option>
                </select>
              </div>

              <div className="form-group">
                <label>📝 Notes (optional)</label>
                <textarea
                  className="form-textarea"
                  rows="3"
                  placeholder="Any additional information..."
                />
              </div>

              <div className="manual-actions">
                <button className="submit-btn">📤 Submit for Review</button>
                <button onClick={() => setManualEntryMode(false)} className="back-btn">
                  ← Back
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 3. Error State
  if (error || !extractionData) {
    const errorInfo = error || { message: "Unknown error occurred" };
    const issues = errorInfo.extractionIssues || [];
    const isRepairNeeded = extractionStatus === 'repair_needed';

    return (
      <div className="ingestion-portal">
        <div className="error-container">
          <div className="error-card">
            <div className="error-header">
              {isRepairNeeded ? (
                <FaExclamationTriangle className="warning-icon-large" />
              ) : (
                <FaExclamationTriangle className="error-icon-large" />
              )}
              <h2>{isRepairNeeded ? '📄 Scanned Document Detected' : '❌ Extraction Failed'}</h2>
              <p>{errorInfo.message}</p>
            </div>

            {/* Repair Suggestion */}
            {isRepairNeeded && (
              <div className="repair-suggestion">
                <div className="suggestion-content">
                  <h4>🔧 Recommended Action</h4>
                  <p>This appears to be a scanned document without text. We can repair it using OCR technology to extract carbon data.</p>
                  <button
                    onClick={processPDF}
                    className="repair-suggest-btn"
                  >
                    <FaSync /> Auto-Repair Document
                  </button>
                </div>
              </div>
            )}

            {/* Issues List */}
            {issues.length > 0 && (
              <div className="issues-list">
                <h4>📋 Issues Found:</h4>
                {issues.map((issue, index) => (
                  <div key={index} className={`issue-item ${issue.severity}`}>
                    <div className="issue-header">
                      <span className="issue-field">{issue.field}</span>
                      <span className="issue-severity">{issue.severity}</span>
                    </div>
                    <p className="issue-message">{issue.message}</p>
                    {issue.technical_details && (
                      <details className="technical-details">
                        <summary>Technical Details</summary>
                        <code>{issue.technical_details}</code>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Action Buttons */}
            <div className="error-actions">
              <button onClick={() => setManualEntryMode(true)} className="manual-entry-btn">
                ✏️ Enter Data Manually
              </button>
              <button onClick={() => window.location.reload()} className="retry-btn">
                🔄 Retry
              </button>
              <button onClick={onBack} className="back-btn">
                ← Back to Upload
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 4. Manual Review Queued State
  if (extractionData?.status === 'manual_review_required') {
    const issues = extractionData.extraction_issues || [];
    const summary = extractionData.extraction_summary || {};
    const confidenceScore = extractionData.confidence_score || 0;

    return (
      <div className="ingestion-portal">
        <div className="manual-review-container">
          <div className="manual-review-card">
            <div className="review-header">
              <div className="review-icon">⏳</div>
              <h2>Queued for Manual Review</h2>
              <p>{extractionData.message || 'Our team will manually extract your data within 24 hours.'}</p>
            </div>

            {/* Confidence Score */}
            {confidenceScore > 0 && (
              <div className="confidence-section">
                <span className="confidence-label">Confidence Score:</span>
                <span className={`confidence-value ${confidenceScore > 0.7 ? 'high' : confidenceScore > 0.4 ? 'medium' : 'low'}`}>
                  {(confidenceScore * 100).toFixed(0)}%
                </span>
              </div>
            )}

            {/* Extraction Summary */}
            {Object.keys(summary).length > 0 && Object.values(summary).some(v => v > 0) && (
              <div className="summary-grid">
                <div className="summary-item">
                  <div className="summary-value">{summary.total_fields || 0}</div>
                  <div className="summary-label">Total Fields</div>
                </div>
                <div className="summary-item success">
                  <div className="summary-value">{summary.extracted_successfully || 0}</div>
                  <div className="summary-label">✅ Extracted</div>
                </div>
                <div className="summary-item warning">
                  <div className="summary-value">{summary.needs_manual_review || 0}</div>
                  <div className="summary-label">⚠️ Needs Review</div>
                </div>
                <div className="summary-item error">
                  <div className="summary-value">{summary.failed || 0}</div>
                  <div className="summary-label">❌ Failed</div>
                </div>
              </div>
            )}

            {/* Issues List */}
            {issues.length > 0 && (
              <div className="issues-container">
                <div className="issues-header">
                  <h4>📋 Extraction Issues</h4>
                  <button
                    onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                    className="toggle-tech-btn"
                  >
                    {showTechnicalDetails ? 'Hide Technical Details' : 'Show Technical Details'}
                  </button>
                </div>

                {issues.map((issue, index) => (
                  <div key={index} className={`issue-item ${issue.severity}`}>
                    <div className="issue-content">
                      <div className="issue-message">
                        {issue.field ? `${issue.field}: ` : ''}{issue.message}
                      </div>
                      {issue.value && (
                        <div className="issue-value">
                          Value: <code>{issue.value}</code>
                        </div>
                      )}
                      {showTechnicalDetails && issue.technical_details && (
                        <div className="technical-details">
                          💻 {issue.technical_details}
                        </div>
                      )}
                    </div>
                    <span className={`severity-badge ${issue.severity}`}>
                      {issue.severity}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Review Info */}
            <div className="review-info">
              <p><strong>Review ID:</strong> <code>{extractionData.review_id}</code></p>
              <p><strong>Estimated Completion:</strong> {extractionData.estimated_completion || '24-48 hours'}</p>
              <p><strong>File:</strong> {file.name}</p>
            </div>

            {/* Special Instructions */}
            <div className="special-instructions">
              <h4>📝 Add Special Instructions for Our Team (Optional)</h4>
              <p className="instructions-hint">
                Need this logged under a specific fiscal year or have other details? Add a note below.
              </p>

              <textarea
                value={specialInstructions}
                onChange={(e) => {
                  setSpecialInstructions(e.target.value);
                  setNoteSent(false);
                }}
                placeholder="e.g., 'Please log this under our 2024 fiscal year'"
                rows="3"
                className="instructions-textarea"
              />

              <button
                onClick={handleSendNote}
                disabled={!specialInstructions.trim() || sendingNote}
                className={`send-note-btn ${specialInstructions.trim() ? 'active' : 'disabled'}`}
              >
                {sendingNote ? 'Sending...' : '💾 Send Note to Team'}
              </button>

              {noteSent && (
                <p className="note-sent">
                  ✅ Note sent successfully! Our team will see this when processing your file.
                </p>
              )}
            </div>

            <p className="email-notification">
              📧 You will receive an email notification as soon as your data is extracted.
            </p>

            <div className="review-actions">
              <button onClick={() => window.location.reload()} className="retry-btn">
                🔄 Retry
              </button>
              <button onClick={onBack} className="back-btn">
                ← Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 5. Success State
  const hasErrors = extractionData?.data_streams?.some(s => s.status === "error") || false;

  return (
    <div className="ingestion-portal">
      <div className="portal-header">
        <button className="back-btn" onClick={onBack}>← Back to Upload</button>
        <div className="batch-info">
          <h2>📊 Active Batch: #{extractionData?.batch_id}</h2>
          <span className={`batch-status ${hasErrors ? 'pending' : 'ready'}`}>
            {hasErrors ? '⚠️ Pending Corrections' : '✅ Ready to Commit'}
          </span>
        </div>
      </div>

      <div className="portal-content">
        {/* LEFT PANEL - PDF Viewer */}
        <div className="pdf-viewer-panel">
          <div className="file-metadata">
            <h3>📄 {extractionData?.file_metadata?.filename || file.name}</h3>
            <p>Method: 🔍 {extractionData?.file_metadata?.extraction_method || 'OCR'} | Pages: {extractionData?.file_metadata?.page_count || 1}</p>
          </div>

          <div className="pdf-container">
            {file.type.startsWith('image/') ? (
              <div className="image-container">
                <img src={URL.createObjectURL(file)} alt="Uploaded document" className="image-preview" />
              </div>
            ) : (
              <Document
                file={URL.createObjectURL(file)}
                onLoadSuccess={onDocumentLoadSuccess}
                loading={<div className="pdf-loading">Loading PDF...</div>}
              >
                <Page pageNumber={pageNumber} scale={scale} />
              </Document>
            )}
          </div>

          <div className="pdf-controls">
            {file.type.startsWith('image/') ? (
              <>
                <button onClick={() => setScale(scale - 0.1)} disabled={scale <= 0.5}>-</button>
                <span>{Math.round(scale * 100)}%</span>
                <button onClick={() => setScale(scale + 0.1)} disabled={scale >= 2.0}>+</button>
                <span className="page-info">Image View</span>
              </>
            ) : (
              <>
                <button onClick={() => setScale(scale - 0.1)} disabled={scale <= 0.5}>-</button>
                <span>{Math.round(scale * 100)}%</span>
                <button onClick={() => setScale(scale + 0.1)} disabled={scale >= 2.0}>+</button>
                <span className="page-info">Page {pageNumber} of {numPages}</span>
                <button onClick={() => setPageNumber(pageNumber - 1)} disabled={pageNumber <= 1}>← Prev</button>
                <button onClick={() => setPageNumber(pageNumber + 1)} disabled={pageNumber >= numPages}>Next →</button>
              </>
            )}
          </div>
        </div>

        {/* RIGHT PANEL - Data Correction */}
        <div className="correction-panel">
          {hasErrors && (
            <div className="error-banner">
              ⚠️ {extractionData?.data_streams?.filter(s => s.status === "error").length || 0} Critical Parsing Exceptions Discovered.
            </div>
          )}

          <div className="correction-section">
            <h3>SECTION A: METADATA</h3>
            <div className="metadata-grid">
              <div className="field-group">
                <label>Reporting Year:</label>
                <input type="text" defaultValue="2026" />
              </div>
              <div className="field-group">
                <label>Ingestion Mode:</label>
                <select defaultValue="premium_pdf">
                  <option value="premium_pdf">Premium PDF/Image (OCR)</option>
                  <option value="digital_pdf">Digital PDF (Text)</option>
                </select>
              </div>
            </div>
          </div>

          {extractionData?.data_streams?.map((stream) => (
            <div key={stream.stream_id} className={`correction-section data-stream ${stream.status}`}>
              <h3>
                DATA STREAM {stream.stream_id} — {stream.stream_name}
                {stream.status === "verified" && <span className="status-badge verified">✅ Verified</span>}
                {stream.status === "error" && <span className="status-badge error">❌ Errors Found</span>}
              </h3>

              {stream.errors && stream.errors.map((err, idx) => (
                <div key={idx} className="error-block">
                  <div className="error-header">
                    ❌ {err.error_type === "low_confidence" ? "Low Confidence" : "Unmapped Asset"}
                  </div>
                  <p>{err.message}</p>

                  {err.requires_manual_input && (
                    <div className="field-group">
                      <label>Manual Quantity Input:</label>
                      <input
                        type="number"
                        placeholder="Enter raw numerical value"
                        onChange={(e) => handleFieldUpdate(stream.stream_id, "consumption_kwh", parseFloat(e.target.value))}
                      />
                    </div>
                  )}

                  {err.requires_asset_selection && (
                    <div className="field-group">
                      <label>Map to System Asset:</label>
                      <select onChange={(e) => handleAssetMapping(stream.stream_id, e.target.value)}>
                        <option value="">Select Asset...</option>
                        {stream.asset_mapping?.suggested_assets?.map((asset, i) => (
                          <option key={i} value={asset}>{asset}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
              ))}

              <div className="extracted-fields">
                {Object.entries(stream.extracted_fields || {}).map(([key, field]) => (
                  <div key={key} className={`field-row ${field.status}`}>
                    <label>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</label>
                    <input
                      type={field.value && typeof field.value === 'number' ? 'number' : 'text'}
                      value={field.value || ''}
                      onChange={(e) => handleFieldUpdate(stream.stream_id, key, e.target.value)}
                      className={field.status === 'failed' ? 'error-input' : ''}
                    />
                    <span className={`confidence-badge ${field.status}`}>
                      {field.status === 'verified' ? '✅ Verified' :
                       field.status === 'manually_corrected' ? '✏️ Corrected' :
                       '❌ Failed'}
                    </span>
                  </div>
                ))}
              </div>

              {stream.defra_factor && (
                <div className="defra-info">
                  <p><strong>DEFRA Factor:</strong> {stream.defra_factor.factor_name} → {stream.defra_factor.multiplier} {stream.defra_factor.unit}</p>
                  {stream.calculated_emissions_kg_co2e && (
                    <p><strong>Emissions:</strong> {stream.calculated_emissions_kg_co2e.toFixed(2)} kg CO2e</p>
                  )}
                </div>
              )}
            </div>
          ))}

          <div className="action-buttons">
            <button className="purge-btn" onClick={handlePurge}>🗑️ Purge Batch</button>
            <button
              className="approve-btn"
              onClick={handleApprove}
              disabled={hasErrors}
            >
              🔒 APPROVE & COMMIT
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}