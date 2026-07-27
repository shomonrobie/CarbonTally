// src/components/PDFRepairTool.js

import React, { useState, useRef } from 'react';
import { FaUpload, FaSpinner, FaCheck, FaExclamationTriangle, FaDownload, FaSync, FaFilePdf, FaTimes, FaEye, FaEyeSlash } from 'react-icons/fa';
import { supabase } from '../supabaseClient';
import toast from 'react-hot-toast';
import '../css/PDFRepairTool.css';

const PDFRepairTool = ({ onRepairComplete, onClose }) => {
  const [file, setFile] = useState(null);
  const [repairing, setRepairing] = useState(false);
  const [repairedFile, setRepairedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [processingStep, setProcessingStep] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [repairStats, setRepairStats] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) return;

    // Validate file type
    if (!selectedFile.type.includes('pdf')) {
      toast.error('Please upload a PDF file');
      return;
    }

    // Validate size (max 50MB)
    if (selectedFile.size > 50 * 1024 * 1024) {
      toast.error('File is too large. Max size is 50MB');
      return;
    }

    setFile(selectedFile);
    setRepairedFile(null);
    setProcessingStep('idle');
    setProgress(0);
    setErrorMessage('');
    setRepairStats(null);

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
    };
    reader.readAsDataURL(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleRepairPDF = async () => {
    if (!file) {
      toast.error('Please select a file first');
      return;
    }

    try {
      setRepairing(true);
      setProcessingStep('uploading');
      setProgress(10);
      toast.info('Uploading file...');

      const formData = new FormData();
      formData.append('file', file);

      setProgress(30);

      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/repair-pdf`, {
        method: 'POST',
        body: formData,
      });

      setProgress(70);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to repair PDF');
      }

      setProcessingStep('processing');
      toast.info('Processing PDF...');

      const result = await response.json();

      if (result.status === 'success') {
        setProcessingStep('repairing');
        setProgress(85);
        toast.info('Repairing PDF structure...');

        // Fetch the repaired file
        const downloadResponse = await fetch(result.repaired_url);
        const blob = await downloadResponse.blob();

        const repairedFileObj = new File([blob], `fixed_${file.name}`, {
          type: 'application/pdf'
        });

        setRepairedFile(repairedFileObj);
        setRepairStats({
          pages: result.pages || 0,
          originalSize: file.size,
          repairedSize: blob.size,
          ocrTextSamples: result.ocr_text_samples || []
        });
        setProcessingStep('done');
        setProgress(100);
        toast.success('✅ PDF repaired successfully!');

        // Auto-download
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `fixed_${file.name}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } else {
        throw new Error(result.message || 'Repair failed');
      }
    } catch (error) {
      console.error('❌ PDF repair error:', error);
      setProcessingStep('error');
      setErrorMessage(error.message || 'Failed to repair PDF. Please try again.');
      toast.error(`Failed to repair PDF: ${error.message}`);
    } finally {
      setRepairing(false);
    }
  };

  const handleExtractData = () => {
    if (!repairedFile) {
      toast.error('No repaired file available');
      return;
    }
    
    if (onRepairComplete) {
      onRepairComplete(repairedFile);
    }
    
    toast.success('✅ Repaired file ready for extraction!');
  };

  const resetTool = () => {
    setFile(null);
    setRepairedFile(null);
    setPreview(null);
    setProcessingStep('idle');
    setProgress(0);
    setErrorMessage('');
    setRepairStats(null);
    setRepairing(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getProgressColor = () => {
    if (progress < 30) return 'progress-uploading';
    if (progress < 70) return 'progress-processing';
    if (progress < 100) return 'progress-repairing';
    return 'progress-done';
  };

  return (
    <div className="pdf-repair-container">
      <div className="pdf-repair-header">
        <div className="pdf-repair-title">
          <FaSync className="repair-icon" />
          <div>
            <h2>🔧 PDF Repair Tool</h2>
            <p>Fix corrupted, scanned, or non-searchable PDFs</p>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="close-btn">
            <FaTimes />
          </button>
        )}
      </div>

      {/* File Upload Area */}
      <div 
        className={`pdf-repair-dropzone ${file ? 'has-file' : ''}`}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {!file ? (
          <>
            <FaUpload className="dropzone-icon" />
            <p className="dropzone-text">
              Drag & drop your PDF here, or <span className="browse-link">browse</span>
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={(e) => handleFileSelect(e.target.files[0])}
              className="file-input-hidden"
            />
            <p className="dropzone-hint">Supports all PDF files up to 50MB</p>
          </>
        ) : (
          <div className="file-info">
            <FaFilePdf className="file-icon" />
            <div className="file-details">
              <p className="file-name">{file.name}</p>
              <p className="file-size">{formatFileSize(file.size)}</p>
            </div>
            <button onClick={resetTool} className="remove-file-btn">
              <FaTimes />
            </button>
          </div>
        )}
      </div>

      {/* Preview Section */}
      {preview && (
        <div className="pdf-preview-section">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="preview-toggle-btn"
          >
            {showPreview ? <FaEyeSlash /> : <FaEye />}
            {showPreview ? 'Hide Preview' : 'Show Preview'}
          </button>
          {showPreview && (
            <div className="pdf-preview-container">
              <iframe
                src={preview}
                title="PDF Preview"
                className="pdf-preview-iframe"
              />
            </div>
          )}
        </div>
      )}

      {/* Processing Status */}
      {processingStep !== 'idle' && (
        <div className="processing-status">
          <div className="status-header">
            <div className="status-icon">
              {processingStep === 'uploading' && <FaSpinner className="spinner" />}
              {processingStep === 'processing' && <FaSpinner className="spinner" />}
              {processingStep === 'repairing' && <FaSpinner className="spinner" />}
              {processingStep === 'done' && <FaCheck className="status-success" />}
              {processingStep === 'error' && <FaExclamationTriangle className="status-error" />}
            </div>
            <div className="status-text">
              {processingStep === 'uploading' && 'Uploading your PDF...'}
              {processingStep === 'processing' && 'Processing document structure...'}
              {processingStep === 'repairing' && 'Repairing PDF and adding OCR text layer...'}
              {processingStep === 'done' && '✅ PDF repaired successfully!'}
              {processingStep === 'error' && '❌ Repair failed'}
            </div>
          </div>

          {/* Progress Bar */}
          {['uploading', 'processing', 'repairing'].includes(processingStep) && (
            <div className="progress-bar-container">
              <div 
                className={`progress-bar ${getProgressColor()}`}
                style={{ width: `${progress}%` }}
              />
              <span className="progress-text">{Math.round(progress)}%</span>
            </div>
          )}

          {/* Error Message */}
          {processingStep === 'error' && errorMessage && (
            <div className="error-message">
              <p>{errorMessage}</p>
              <button onClick={resetTool} className="retry-btn">
                <FaSync /> Try Again
              </button>
            </div>
          )}

          {/* Repair Stats */}
          {processingStep === 'done' && repairStats && (
            <div className="repair-stats">
              <div className="stat-item">
                <span className="stat-label">Pages Processed</span>
                <span className="stat-value">{repairStats.pages}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Original Size</span>
                <span className="stat-value">{formatFileSize(repairStats.originalSize)}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Repaired Size</span>
                <span className="stat-value">{formatFileSize(repairStats.repairedSize)}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">OCR Applied</span>
                <span className="stat-value">{repairStats.ocrTextSamples.length > 0 ? '✅ Yes' : '❌ No'}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {file && (
        <div className="pdf-repair-actions">
          <button
            onClick={handleRepairPDF}
            disabled={repairing}
            className="repair-btn primary"
          >
            {repairing ? <FaSpinner className="spinner" /> : <FaSync />}
            {repairing ? 'Repairing...' : '🔧 Repair PDF'}
          </button>

          {repairedFile && (
            <button
              onClick={handleExtractData}
              className="repair-btn success"
            >
              <FaUpload />
              Extract Data Now
            </button>
          )}

          {!repairing && file && (
            <button
              onClick={resetTool}
              className="repair-btn secondary"
            >
              <FaTimes />
              Cancel
            </button>
          )}
        </div>
      )}

      {/* Features */}
      <div className="pdf-repair-features">
        <div className="feature-card">
          <div className="feature-icon">🔍</div>
          <h4>OCR Text Layer</h4>
          <p>Adds searchable text to scanned documents</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">📐</div>
          <h4>Repair Structure</h4>
          <p>Fixes corrupted PDF structure</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">⚡</div>
          <h4>Auto-Format</h4>
          <p>Optimizes for carbon data extraction</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🔒</div>
          <h4>Secure Processing</h4>
          <p>Your data is encrypted and private</p>
        </div>
      </div>
    </div>
  );
};

export default PDFRepairTool;