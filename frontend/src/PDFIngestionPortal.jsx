import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import axios from 'axios';
import toast from 'react-hot-toast';

import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;
export default function PDFIngestionPortal({ file, dataType, organizationId, onBack, onApprove, onPurge }) {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [extractionData, setExtractionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // <-- ADDED ERROR STATE

  useEffect(() => {
    const extractFile = async () => {
      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('data_type', dataType);
        formData.append('organization_id', organizationId || ''); 
        
        // Detect file type and call appropriate endpoint
        const isImage = file.type.startsWith('image/');
        const endpoint = isImage ? '/upload-image' : '/upload-pdf';
        
        const response = await axios.post(`${process.env.REACT_APP_API_URL}${endpoint}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        setExtractionData(response.data);
        setLoading(false);
      } catch (err) {
        console.error("File extraction failed:", err);
        const errorMsg = err.response?.data?.detail || "Failed to extract data from file. Please try again.";
        setError(errorMsg);
        toast.error(errorMsg);
        setLoading(false);
      }
    };
    
    extractFile();
  }, [file, dataType, organizationId]);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
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
        organization_id: 'mock-org-id'
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

  // 1. Loading State
  if (loading) {
    return (
      <div className="ingestion-portal">
        <div className="loading-state" style={{ textAlign: 'center', padding: '4rem' }}>
          <div className="spinner"></div>
          <p style={{ marginTop: '1rem', fontSize: '1.1rem' }}>Extracting data from {file.type.startsWith('image/') ? 'image' : 'PDF'}...</p>
        </div>
      </div>
    );
  }

    // 2. Error State (Prevents the null crash!)
  if (error || !extractionData) {
    return (
      <div className="ingestion-portal">
        <div className="error-state" style={{ textAlign: 'center', padding: '4rem' }}>
          <h3 style={{ color: '#ef4444', marginBottom: '1rem' }}>❌ Extraction Failed</h3>
          <p style={{ marginBottom: '1.5rem', color: '#64748b' }}>{error || "Unknown error occurred."}</p>
          <button className="back-btn" onClick={onBack} style={{ padding: '0.75rem 1.5rem' }}>
            ← Go Back to Upload
          </button>
        </div>
      </div>
    );
  }

  // 🌟 3. NEW: Manual Review Queued State
  if (extractionData.status === 'manual_review_required') {
    return (
      <div className="ingestion-portal" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#f8fafc' }}>
        <div style={{ textAlign: 'center', padding: '3rem', background: 'white', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', maxWidth: '500px', width: '100%' }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>⏳</div>
          <h2 style={{ marginBottom: '1rem', color: '#0f172a' }}>Queued for Manual Review</h2>
          <p style={{ fontSize: '1.1rem', color: '#475569', marginBottom: '2rem' }}>
            {extractionData.message}
          </p>
          
          <div style={{ background: '#f1f5f9', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem', textAlign: 'left' }}>
            <p style={{ margin: '0.5rem 0' }}><strong>Review ID:</strong> <code style={{ background: '#e2e8f0', padding: '2px 6px', borderRadius: '4px' }}>{extractionData.review_id}</code></p>
            <p style={{ margin: '0.5rem 0' }}><strong>Estimated Completion:</strong> {extractionData.estimated_completion}</p>
            <p style={{ margin: '0.5rem 0' }}><strong>File:</strong> {file.name}</p>
          </div>
          
          <p style={{ color: '#64748b', marginBottom: '2rem', fontSize: '0.9rem' }}>
            You will receive an email notification as soon as your data is extracted and ready to review.
          </p>
          
          <button onClick={onBack} style={{ padding: '0.75rem 1.5rem', background: '#16a34a', color: 'white', border: 'none', borderRadius: '8px', fontWeight: '600', cursor: 'pointer', fontSize: '1rem' }}>
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // 4. Success State (Safe to access extractionData now)
  // Added ?. just in case, though it shouldn't reach here without data_streams
  const hasErrors = extractionData.data_streams?.some(s => s.status === "error") || false;

  return (    
    <div className="ingestion-portal">
      {/* HEADER */}
      <div className="portal-header">
        <button className="back-btn" onClick={onBack}>← Back to Upload</button>
        <div className="batch-info">
          <h2>📊 Active Batch: #{extractionData.batch_id}</h2>
          <span className={`batch-status ${hasErrors ? 'pending' : 'ready'}`}>
            {hasErrors ? '⚠️ Pending Corrections' : '✅ Ready to Commit'}
          </span>
        </div>
      </div>

      {/* MAIN CONTENT - SPLIT SCREEN */}
      <div className="portal-content">
        {/* LEFT PANEL - FILE VIEWER (40%) */}
        <div className="pdf-viewer-panel">
          <div className="file-metadata">
            <h3>📄 {extractionData.file_metadata.filename}</h3>
            <p>Method: 🔍 {extractionData.file_metadata.extraction_method} | Pages: {extractionData.file_metadata.page_count}</p>
          </div>

          <div className="pdf-container">
            {file.type.startsWith('image/') ? (
              <div className="image-container">
                <img 
                  src={URL.createObjectURL(file)} 
                  alt="Uploaded document" 
                  style={{ maxWidth: '100%', height: 'auto' }}
                />
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

        {/* RIGHT PANEL - DATA CORRECTION INTERFACE (60%) */}
        <div className="correction-panel">
          {hasErrors && (
            <div className="error-banner">
              ⚠️ {extractionData.data_streams.filter(s => s.status === "error").length} Critical Parsing Exceptions Discovered. Resolve errors below to unlock database transaction.
            </div>
          )}

          {/* SECTION A: METADATA */}
          <div className="correction-section">
            <h3>SECTION A: MULTI-TENANT ROUTING & METADATA</h3>
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

          {/* DATA STREAMS */}
          {extractionData.data_streams.map((stream) => (
            <div key={stream.stream_id} className={`correction-section data-stream ${stream.status}`}>
              <h3>
                DATA STREAM {stream.stream_id} — {stream.stream_name} ({stream.scope} Compliance)
                {stream.status === "verified" && <span className="status-badge verified">✅ Verified</span>}
                {stream.status === "error" && <span className="status-badge error">❌ Errors Found</span>}
              </h3>

              {/* ERRORS */}
              {stream.errors && stream.errors.map((err, idx) => (
                <div key={idx} className="error-block">
                  <div className="error-header">
                    ❌ ERROR: {err.error_type === "low_confidence" ? "PARSER CHARACTER MATCH STRUCTURAL EXCEPTION" : "UNMAPPED SOURCE ASSET IDENTIFIED"}
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
                        <option value="">⚠️ Select Asset Profile to Route Log...</option>
                        {stream.asset_mapping.suggested_assets.map((asset, i) => (
                          <option key={i} value={asset}>{asset}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
              ))}

              {/* EXTRACTED FIELDS */}
              <div className="extracted-fields">
                {Object.entries(stream.extracted_fields).map(([key, field]) => (
                  <div key={key} className={`field-row ${field.status}`}>
                    <label>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</label>
                    <input 
                      type={field.value && typeof field.value === 'number' ? 'number' : 'text'}
                      value={field.value || ''}
                      onChange={(e) => handleFieldUpdate(stream.stream_id, key, e.target.value)}
                      className={field.status === 'failed' ? 'error-input' : ''}
                    />
                    <span className={`confidence-badge ${field.status}`}>
                      {field.status === 'verified' ? '✅ Auto-Verified' : 
                       field.status === 'manually_corrected' ? '✏️ Manually Corrected' : 
                       '❌ Failed'}
                    </span>
                  </div>
                ))}
              </div>

              {/* DEFRA FACTOR INFO */}
              {stream.defra_factor && (
                <div className="defra-info">
                  <p><strong>Legal DEFRA Factor:</strong> {stream.defra_factor.factor_name} → Multiplier: {stream.defra_factor.multiplier} {stream.defra_factor.unit}</p>
                  {stream.calculated_emissions_kg_co2e && (
                    <p><strong>Calculated Baseline:</strong> {stream.calculated_emissions_kg_co2e.toFixed(2)} kg CO2e</p>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* ACTION BUTTONS */}
          <div className="action-buttons">
            <button className="purge-btn" onClick={handlePurge}>🗑️ Purge Processing Batch</button>
            <button 
              className="approve-btn" 
              onClick={handleApprove}
              disabled={hasErrors}
            >
              🔒 APPROVE CORRECTIONS & COMMIT TO SYSTEM
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}