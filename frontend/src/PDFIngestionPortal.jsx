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
  const [error, setError] = useState(null);
  const [extractionProgress, setExtractionProgress] = useState(0);
  const [extractionStatus, setExtractionStatus] = useState('initializing');
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [specialInstructions, setSpecialInstructions] = useState('');  
  const [sendingNote, setSendingNote] = useState(false);
  const [noteSent, setNoteSent] = useState(false);

  useEffect(() => {
    const extractFile = async () => {
      try {
        setExtractionStatus('uploading');
        setExtractionProgress(10);
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('data_type', dataType);
        formData.append('organization_id', organizationId || ''); 
        
        const isImage = file.type.startsWith('image/');
        const endpoint = isImage ? '/upload-image' : '/upload-pdf';
        
        setExtractionStatus('processing');
        setExtractionProgress(30);
        
        const response = await axios.post(`${process.env.REACT_APP_API_URL}${endpoint}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setExtractionProgress(30 + (percentCompleted * 0.4));
          }
        });
        
        setExtractionProgress(90);
        setExtractionStatus('finalizing');
        
        await new Promise(resolve => setTimeout(resolve, 500));
        
        setExtractionData(response.data);
        setExtractionProgress(100);
        setExtractionStatus('complete');
        setLoading(false);
        
      } catch (err) {
            console.error("File extraction failed:", err);
    
            let errorMsg = "Failed to extract data from file.";
            let technicalDetails = "";
            let userFriendlyMessage = "";
            let extractionIssues = [];
            let extractionSummary = {};
            
            if (err.response?.data) {
                const data = err.response.data;
                
                // Check if we have extraction issues in the response
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
            
            toast.error(userFriendlyMessage);
            setLoading(false);
            setExtractionStatus('error');
        }

    };
    
    extractFile();
  }, [file, dataType, organizationId]);

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
        setSpecialInstructions(''); // Clear the box after sending
        }
    } catch (error) {
        console.error('Failed to send note:', error);
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

  // 1. Loading State with Spinner
  if (loading) {
    const progressPercentage = Math.min(extractionProgress, 100);
    const statusMessages = {
      initializing: 'Initializing extraction engine...',
      uploading: 'Uploading file to secure storage...',
      processing: 'Extracting data from document...',
      finalizing: 'Finalizing extraction results...',
      complete: 'Extraction complete!'
    };

    return (
      <div className="ingestion-portal" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#f8fafc' }}>
        <div style={{ textAlign: 'center', padding: '3rem', background: 'white', borderRadius: '16px', boxShadow: '0 10px 40px rgba(0,0,0,0.08)', maxWidth: '500px', width: '100%' }}>
          {/* Spinner */}
          <div style={{ 
            width: '80px', 
            height: '80px', 
            margin: '0 auto 1.5rem',
            border: '6px solid #e2e8f0',
            borderTopColor: '#16a34a',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
          
          {/* Progress Bar */}
          <div style={{ 
            width: '100%', 
            height: '8px', 
            background: '#e2e8f0', 
            borderRadius: '4px', 
            overflow: 'hidden',
            marginBottom: '1rem'
          }}>
            <div style={{ 
              width: `${progressPercentage}%`, 
              height: '100%', 
              background: 'linear-gradient(90deg, #22c55e, #16a34a)',
              transition: 'width 0.5s ease',
              borderRadius: '4px'
            }} />
          </div>
          
          <p style={{ fontSize: '1.1rem', fontWeight: '600', color: '#0f172a', marginBottom: '0.5rem' }}>
            Extracting data from {file.type.startsWith('image/') ? 'image' : 'PDF'}...
          </p>
          <p style={{ color: '#64748b', fontSize: '0.95rem', marginBottom: '0.5rem' }}>
            {statusMessages[extractionStatus] || 'Processing...'}
          </p>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            {Math.round(progressPercentage)}% complete
          </p>
          <p style={{ color: '#94a3b8', fontSize: '0.75rem', marginTop: '0.5rem' }}>
            File: {file.name}
          </p>
        </div>
      </div>
    );
  }

  // 2. Error State with Detailed Technical Info
  if (error || !extractionData) {
    const errorInfo = error || { message: "Unknown error occurred" };
    const issues = errorInfo.extractionIssues || [];
    
    return (
      <div className="ingestion-portal" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#f8fafc' }}>
        <div style={{ maxWidth: '700px', width: '100%', padding: '2rem', background: 'white', borderRadius: '16px', boxShadow: '0 10px 40px rgba(0,0,0,0.08)' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>❌</div>
            <h3 style={{ color: '#dc2626', marginBottom: '0.5rem' }}>Extraction Failed</h3>
            <p style={{ color: '#475569', fontSize: '1.05rem' }}>{errorInfo.message}</p>
          </div>

          {/* Show issues if available */}
          {issues.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ color: '#0f172a', marginBottom: '0.75rem', fontSize: '0.95rem' }}>📋 Issues Found:</h4>
              {issues.map((issue, index) => (
                <div 
                  key={index} 
                  style={{ 
                    padding: '0.75rem', 
                    marginBottom: '0.5rem',
                    background: issue.severity === 'critical' ? '#fef2f2' : '#fffbeb',
                    borderLeft: `4px solid ${issue.severity === 'critical' ? '#ef4444' : '#f59e0b'}`,
                    borderRadius: '4px'
                  }}
                >
                  <div style={{ fontWeight: '600', fontSize: '0.9rem', color: '#0f172a' }}>
                    {issue.field}: {issue.message}
                  </div>
                  {issue.value && (
                    <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.25rem' }}>
                      Value: <code style={{ background: '#f1f5f9', padding: '1px 4px', borderRadius: '3px' }}>{issue.value}</code>
                    </div>
                  )}
                  {issue.technical_details && (
                    <div style={{ 
                      fontSize: '0.8rem', 
                      color: '#64748b', 
                      marginTop: '0.5rem',
                      padding: '0.5rem',
                      background: '#f1f5f9',
                      borderRadius: '4px',
                      fontFamily: 'monospace'
                    }}>
                      💻 {issue.technical_details}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Technical Details Section */}
          <div style={{ background: '#f1f5f9', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
            <h4 style={{ color: '#0f172a', marginBottom: '1rem', fontSize: '0.95rem' }}>🔍 Technical Details</h4>
            <div style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: '#475569' }}>
              <p><strong>Error:</strong> {errorInfo.originalError || errorInfo.technical || 'Unknown error'}</p>
              <p><strong>Timestamp:</strong> {errorInfo.timestamp || new Date().toISOString()}</p>
              {errorInfo.fileInfo && (
                <>
                  <p><strong>File:</strong> {errorInfo.fileInfo.name}</p>
                  <p><strong>Size:</strong> {(errorInfo.fileInfo.size / 1024).toFixed(1)} KB</p>
                  <p><strong>Type:</strong> {errorInfo.fileInfo.type}</p>
                </>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button 
              onClick={() => window.location.reload()} 
              style={{ 
                padding: '0.75rem 1.5rem', 
                background: '#3b82f6', 
                color: 'white', 
                border: 'none', 
                borderRadius: '8px', 
                fontWeight: '600', 
                cursor: 'pointer',
                fontSize: '0.95rem'
              }}
            >
              🔄 Retry
            </button>
            <button 
              onClick={onBack} 
              style={{ 
                padding: '0.75rem 1.5rem', 
                background: '#f1f5f9', 
                color: '#475569', 
                border: '1px solid #cbd5e1', 
                borderRadius: '8px', 
                fontWeight: '600', 
                cursor: 'pointer',
                fontSize: '0.95rem'
              }}
            >
              ← Back to Upload
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 3. Manual Review Queued State with Detailed Issues
  if (extractionData?.status === 'manual_review_required') {
    const issues = extractionData.extraction_issues || [];
    const summary = extractionData.extraction_summary || {};
    const confidenceScore = extractionData.confidence_score || 0;
    
    return (
      <div className="ingestion-portal" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#f8fafc' }}>
        <div style={{ maxWidth: '650px', width: '100%', padding: '2rem', background: 'white', borderRadius: '16px', boxShadow: '0 10px 40px rgba(0,0,0,0.08)' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{ fontSize: '4rem', marginBottom: '0.5rem' }}>⏳</div>
            <h2 style={{ marginBottom: '0.5rem', color: '#0f172a' }}>Queued for Manual Review</h2>
            <p style={{ fontSize: '1rem', color: '#475569' }}>
              {extractionData.message || 'Our team will manually extract your data within 24 hours.'}
            </p>
          </div>

          {/* Confidence Score */}
          {confidenceScore > 0 && (
            <div style={{ 
              textAlign: 'center', 
              marginBottom: '1.5rem',
              padding: '0.75rem',
              background: confidenceScore > 0.7 ? '#f0fdf4' : '#fffbeb',
              borderRadius: '8px',
              border: `1px solid ${confidenceScore > 0.7 ? '#bbf7d0' : '#fde68a'}`
            }}>
              <span style={{ fontSize: '0.9rem', color: '#64748b' }}>Confidence Score: </span>
              <span style={{ 
                fontWeight: 'bold',
                color: confidenceScore > 0.7 ? '#16a34a' : '#d97706'
              }}>
                {(confidenceScore * 100).toFixed(0)}%
              </span>
            </div>
          )}

          {/* EXTRACTION SUMMARY */}
          {Object.keys(summary).length > 0 && Object.values(summary).some(v => v > 0) && (
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', 
              gap: '0.75rem',
              marginBottom: '1.5rem',
              padding: '1rem',
              background: '#f8fafc',
              borderRadius: '8px'
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#0f172a' }}>{summary.total_fields || 0}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Total Fields</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#22c55e' }}>{summary.extracted_successfully || 0}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>✅ Extracted</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f59e0b' }}>{summary.needs_manual_review || 0}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>⚠️ Needs Review</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#ef4444' }}>{summary.failed || 0}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>❌ Failed</div>
              </div>
            </div>
          )}

          {/* ISSUES LIST */}
          {issues.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h4 style={{ color: '#0f172a', margin: 0, fontSize: '0.95rem' }}>📋 Extraction Issues</h4>
                <button 
                  onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#3b82f6',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    textDecoration: 'underline'
                  }}
                >
                  {showTechnicalDetails ? 'Hide Technical Details' : 'Show Technical Details'}
                </button>
              </div>
              
              {issues.map((issue, index) => (
                <div 
                  key={index} 
                  style={{ 
                    padding: '0.75rem', 
                    marginBottom: '0.5rem',
                    background: issue.severity === 'critical' ? '#fef2f2' : '#fffbeb',
                    borderLeft: `4px solid ${issue.severity === 'critical' ? '#ef4444' : '#f59e0b'}`,
                    borderRadius: '4px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '600', fontSize: '0.9rem', color: '#0f172a' }}>
                        {issue.field ? `${issue.field}: ` : ''}{issue.message}
                      </div>
                      {issue.value && (
                        <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.25rem' }}>
                          Value: <code style={{ background: '#f1f5f9', padding: '1px 4px', borderRadius: '3px' }}>{issue.value}</code>
                        </div>
                      )}
                      {showTechnicalDetails && issue.technical_details && (
                        <div style={{ 
                          fontSize: '0.8rem', 
                          color: '#64748b', 
                          marginTop: '0.5rem',
                          padding: '0.5rem',
                          background: '#f1f5f9',
                          borderRadius: '4px',
                          fontFamily: 'monospace'
                        }}>
                          💻 {issue.technical_details}
                        </div>
                      )}
                    </div>
                    <span style={{ 
                      fontSize: '0.65rem', 
                      padding: '2px 8px', 
                      borderRadius: '12px',
                      background: issue.severity === 'critical' ? '#fee2e2' : '#fef3c7',
                      color: issue.severity === 'critical' ? '#dc2626' : '#d97706',
                      whiteSpace: 'nowrap',
                      marginLeft: '0.5rem'
                    }}>
                      {issue.severity}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* REVIEW INFO */}
          <div style={{ background: '#f1f5f9', padding: '1.5rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
            <p style={{ margin: '0.5rem 0' }}><strong>Review ID:</strong> <code style={{ background: '#e2e8f0', padding: '2px 6px', borderRadius: '4px' }}>{extractionData.review_id}</code></p>
            <p style={{ margin: '0.5rem 0' }}><strong>Estimated Completion:</strong> {extractionData.estimated_completion || '24-48 hours'}</p>
            <p style={{ margin: '0.5rem 0' }}><strong>File:</strong> {file.name}</p>
          </div>
          {/* 📝 ADD SPECIAL INSTRUCTIONS SECTION */}
            <div style={{ 
            background: '#f0fdf4', 
            padding: '1.5rem', 
            borderRadius: '8px', 
            marginBottom: '1.5rem', 
            border: '1px solid #bbf7d0' 
            }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: '#166534', fontSize: '0.95rem' }}>
                📝 Add Special Instructions for Our Team (Optional)
            </h4>
            <p style={{ margin: '0 0 1rem 0', fontSize: '0.85rem', color: '#15803d' }}>
                Need this logged under a specific fiscal year or have other details? Add a note below and our team will see it.
            </p>
            
            <textarea
                value={specialInstructions}
                onChange={(e) => {
                setSpecialInstructions(e.target.value);
                setNoteSent(false); // Reset success message if they type again
                }}
                placeholder="e.g., 'Please log this under our 2024 fiscal year'"
                rows={3}
                style={{ 
                width: '100%', 
                padding: '0.75rem', 
                border: '1px solid #86efac', 
                borderRadius: '6px', 
                fontSize: '0.9rem', 
                resize: 'vertical',
                fontFamily: 'inherit',
                outline: 'none'
                }}
                onFocus={(e) => e.target.style.borderColor = '#16a34a'}
                onBlur={(e) => e.target.style.borderColor = '#86efac'}
            />
            
            <button 
                onClick={handleSendNote}
                disabled={!specialInstructions.trim() || sendingNote}
                style={{ 
                marginTop: '0.75rem',
                padding: '0.6rem 1.2rem', 
                background: specialInstructions.trim() ? '#16a34a' : '#94a3b8', 
                color: 'white', 
                border: 'none', 
                borderRadius: '6px', 
                fontWeight: '600', 
                cursor: specialInstructions.trim() ? 'pointer' : 'not-allowed',
                fontSize: '0.9rem',
                transition: 'background 0.2s'
                }}
            >
                {sendingNote ? 'Sending...' : '💾 Send Note to Team'}
            </button>
            
            {noteSent && (
                <p style={{ color: '#16a34a', fontSize: '0.85rem', marginTop: '0.75rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>✅</span> Note sent successfully! Our team will see this when processing your file.
                </p>
            )}
            </div>
          <p style={{ color: '#64748b', marginBottom: '2rem', fontSize: '0.95rem', textAlign: 'center' }}>
            📧 You will receive an email notification as soon as your data is extracted and ready to review.
          </p>
          
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button 
              onClick={() => window.location.reload()} 
              style={{ 
                padding: '0.75rem 1.5rem', 
                background: '#3b82f6', 
                color: 'white', 
                border: 'none', 
                borderRadius: '8px', 
                fontWeight: '600', 
                cursor: 'pointer',
                fontSize: '0.95rem'
              }}
            >
              🔄 Retry
            </button>
            <button 
              onClick={onBack} 
              style={{ 
                padding: '0.75rem 1.5rem', 
                background: '#f1f5f9', 
                color: '#475569', 
                border: '1px solid #cbd5e1', 
                borderRadius: '8px', 
                fontWeight: '600', 
                cursor: 'pointer',
                fontSize: '0.95rem'
              }}
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 4. Success State
  const hasErrors = extractionData?.data_streams?.some(s => s.status === "error") || false;

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
            <h3>📄 {extractionData.file_metadata?.filename || file.name}</h3>
            <p>Method: 🔍 {extractionData.file_metadata?.extraction_method || 'OCR'} | Pages: {extractionData.file_metadata?.page_count || 1}</p>
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
              ⚠️ {extractionData.data_streams?.filter(s => s.status === "error").length || 0} Critical Parsing Exceptions Discovered. Resolve errors below to unlock database transaction.
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
          {extractionData.data_streams?.map((stream) => (
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
                        {stream.asset_mapping?.suggested_assets?.map((asset, i) => (
                          <option key={i} value={asset}>{asset}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
              ))}

              {/* EXTRACTED FIELDS */}
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

      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}