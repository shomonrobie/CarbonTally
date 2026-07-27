// BulkUpload.jsx - Updated with premium feature handling

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

export default function BulkUpload({ organizationId, onBack }) {
  const [files, setFiles] = useState([]);
  const [batchName, setBatchName] = useState('');
  const [dataType, setDataType] = useState('mixed');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [specialInstructions, setSpecialInstructions] = useState('');
  const [isPremiumFeature, setIsPremiumFeature] = useState(true); // Default to true until checked
  const [maxBatchFiles, setMaxBatchFiles] = useState(50);
  const [loadingSettings, setLoadingSettings] = useState(true);

  // Check if bulk upload is enabled (premium feature)
  useEffect(() => {
    const checkBulkUploadStatus = async () => {
      try {
        const response = await axios.get(`${process.env.REACT_APP_API_URL}/api/settings`);
        
        if (response.data.status === 'success') {
          const settings = response.data.settings;
          const maxFiles = settings.max_batch_files || 0;
          
          setMaxBatchFiles(maxFiles);
          
          // If max_batch_files is 0, bulk upload is disabled (premium feature)
          if (maxFiles === 0) {
            setIsPremiumFeature(false);
            toast.info('ℹ️ Bulk upload is a premium feature. Please upgrade to access it.', {
              duration: 5000
            });
          } else {
            setIsPremiumFeature(true);
          }
        }
      } catch (error) {
        console.error('Error checking bulk upload status:', error);
        // Default to showing the feature (will show upgrade message if backend returns premium_feature)
      } finally {
        setLoadingSettings(false);
      }
    };
    
    checkBulkUploadStatus();
  }, []);

  const handleFileDrop = (e) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    
    // Check if premium feature is available
    if (!isPremiumFeature) {
      toast.error('Bulk upload is a premium feature. Please upgrade to access it.');
      return;
    }
    
    // Check max files limit
    if (droppedFiles.length + files.length > maxBatchFiles) {
      toast.error(`Maximum ${maxBatchFiles} files allowed per batch`);
      return;
    }
    
    setFiles((prev) => [...prev, ...droppedFiles]);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    
    // Check if premium feature is available
    if (!isPremiumFeature) {
      toast.error('Bulk upload is a premium feature. Please upgrade to access it.');
      return;
    }
    
    // Check max files limit
    if (selectedFiles.length + files.length > maxBatchFiles) {
      toast.error(`Maximum ${maxBatchFiles} files allowed per batch`);
      return;
    }
    
    setFiles((prev) => [...prev, ...selectedFiles]);
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (!isPremiumFeature) {
      toast.error('Bulk upload is a premium feature. Please upgrade to access it.');
      return;
    }
    
    if (files.length === 0) {
      toast.error('Please select at least one file');
      return;
    }
    if (!batchName.trim()) {
      toast.error('Please enter a batch name');
      return;
    }

    setUploading(true);
    setProgress(0);

    const formData = new FormData();
    formData.append('batch_name', batchName);
    formData.append('data_type', dataType);
    formData.append('organization_id', organizationId);
    formData.append('special_instructions', specialInstructions);

    files.forEach((file) => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/upload-batch`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setProgress(percentCompleted);
          },
        }
      );

      // Check if premium feature response
      if (response.data.status === 'premium_feature') {
        toast.error(response.data.message);
        setIsPremiumFeature(false);
        setUploading(false);
        return;
      }

      if (response.data.failed_files && response.data.failed_files.length > 0) {
        toast.success(`✅ Uploaded ${files.length - response.data.failed_files.length} files. ${response.data.failed_files.length} failed.`);
      } else {
        toast.success(`✅ ${response.data.message}`);
      }
      
      setFiles([]);
      setBatchName('');
      
      if (onBack) onBack();
      
    } catch (error) {
      console.error('Batch upload error:', error);
      
      // Check if it's a premium feature error from backend
      if (error.response?.data?.status === 'premium_feature') {
        toast.error(error.response.data.message);
        setIsPremiumFeature(false);
      } else {
        toast.error('Failed to upload batch. Please try again.');
      }
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  // Premium Feature Unavailable State
  if (!isPremiumFeature && !loadingSettings) {
    return (
      <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem' }}>
        <button 
          onClick={onBack}
          style={{
            marginBottom: '0.75rem',
            background: '#f1f5f9',
            border: '1px solid #cbd5e1',
            color: '#475569',
            cursor: 'pointer',
            fontSize: '0.875rem',
            padding: '0.4rem 0.8rem',
            borderRadius: '6px',
            fontWeight: '500',
          }}
        >
          ← Back to Single Upload
        </button>
        
        <div style={{
          padding: '3rem 2rem',
          textAlign: 'center',
          backgroundColor: '#fef3c7',
          borderRadius: '12px',
          border: '2px solid #f59e0b'
        }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>⭐</div>
          <h2 style={{ margin: '0 0 0.5rem 0', color: '#92400e' }}>Premium Feature</h2>
          <p style={{ color: '#78350f', marginBottom: '1rem', fontSize: '1.1rem' }}>
            Bulk upload is a premium feature available to paid subscribers.
          </p>
          <div style={{
            padding: '1rem',
            backgroundColor: 'white',
            borderRadius: '8px',
            maxWidth: '400px',
            margin: '0 auto 1.5rem'
          }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: '#0f172a' }}>Upgrade to access:</h4>
            <ul style={{ textAlign: 'left', color: '#475569' }}>
              <li>📦 Upload up to 50 files at once</li>
              <li>⚡ Priority processing</li>
              <li>📊 Advanced analytics</li>
              <li>👥 Team collaboration</li>
            </ul>
          </div>
          <button
            onClick={() => window.location.href = '/pricing'}
            style={{
              padding: '0.75rem 2rem',
              backgroundColor: '#f59e0b',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            🚀 Upgrade Now
          </button>
        </div>
      </div>
    );
  }

  // Loading State
  if (loadingSettings) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        padding: '3rem'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div className="spinner" style={{
            width: '40px',
            height: '40px',
            border: '4px solid #e2e8f0',
            borderTopColor: '#16a34a',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 1rem'
          }} />
          <p style={{ color: '#64748b' }}>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem' }}>
      <button 
        onClick={onBack}
        style={{
          marginBottom: '0.75rem',
          background: '#f1f5f9',
          border: '1px solid #cbd5e1',
          color: '#475569',
          cursor: 'pointer',
          fontSize: '0.875rem',
          padding: '0.4rem 0.8rem',
          borderRadius: '6px',
          fontWeight: '500',
        }}
      >
        ← Back to Single Upload
      </button>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: '0 0 0.5rem 0' }}>📦 Bulk Document Upload</h2>
          <p style={{ color: '#64748b', margin: 0 }}>
            Upload multiple bills, invoices, and receipts at once. Our team will process them within 24 hours.
          </p>
        </div>
        <div style={{
          padding: '0.25rem 0.75rem',
          backgroundColor: '#fef3c7',
          borderRadius: '12px',
          fontSize: '0.8rem',
          color: '#92400e',
          fontWeight: '600'
        }}>
          ⭐ Premium
        </div>
      </div>
      
      {/* Batch Name Input */}
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
          Batch Name *
        </label>
        <input
          type="text"
          value={batchName}
          onChange={(e) => setBatchName(e.target.value)}
          placeholder="e.g., Q1 2024 Utility Bills"
          style={{
            width: '100%',
            padding: '0.75rem',
            border: '1px solid #ddd',
            borderRadius: '6px',
            fontSize: '1rem',
          }}
        />
      </div>
      
      {/* Special Instructions Input */}
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
          Special Instructions for Our Team (Optional)
        </label>
        <textarea
          value={specialInstructions}
          onChange={(e) => setSpecialInstructions(e.target.value)}
          placeholder="e.g., 'Please log these under our 2024 fiscal year', or 'This is for the London office only'"
          rows={3}
          style={{
            width: '100%',
            padding: '0.75rem',
            border: '1px solid #ddd',
            borderRadius: '6px',
            fontSize: '0.95rem',
            fontFamily: 'inherit',
            resize: 'vertical'
          }}
        />
      </div>    
      
      {/* Data Type Selector */}
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
          Document Type
        </label>
        <select
          value={dataType}
          onChange={(e) => setDataType(e.target.value)}
          style={{
            width: '100%',
            padding: '0.75rem',
            border: '1px solid #ddd',
            borderRadius: '6px',
            fontSize: '1rem',
          }}
        >
          <option value="mixed">Mixed (Auto-detect)</option>
          <option value="utility">Utility Bills Only</option>
          <option value="fuel">Fuel Invoices Only</option>
          <option value="scope3">Scope 3 Documents Only</option>
        </select>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleFileDrop}
        style={{
          border: '2px dashed #16a34a',
          borderRadius: '12px',
          padding: '3rem',
          textAlign: 'center',
          backgroundColor: '#f0fdf4',
          marginBottom: '1.5rem',
          cursor: 'pointer',
        }}
        onClick={() => document.getElementById('fileInput').click()}
      >
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📁</div>
        <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem', fontWeight: '600' }}>
          Drag & drop your files here
        </p>
        <p style={{ color: '#64748b', marginBottom: '1rem' }}>
          or click to browse (PDF, JPG, PNG)
        </p>
        <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
          Maximum {maxBatchFiles} files per batch
        </p>
        <input
          id="fileInput"
          type="file"
          multiple
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>
            Selected Files ({files.length})
          </h3>
          <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {files.map((file, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.75rem',
                  backgroundColor: '#f8fafc',
                  borderRadius: '6px',
                  marginBottom: '0.5rem',
                }}
              >
                <div style={{ flex: 1 }}>
                  <strong>{file.name}</strong>
                  <span style={{ color: '#64748b', marginLeft: '1rem' }}>
                    ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#ef4444',
                    cursor: 'pointer',
                    fontSize: '1.2rem',
                    padding: '0 0.5rem',
                  }}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={uploading || files.length === 0 || !batchName.trim()}
        style={{
          width: '100%',
          padding: '1rem',
          backgroundColor: uploading || !batchName.trim() ? '#94a3b8' : '#16a34a',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          fontSize: '1.1rem',
          fontWeight: '600',
          cursor: uploading || !batchName.trim() ? 'not-allowed' : 'pointer',
        }}
      >
        {uploading ? `Uploading... ${progress}%` : '🚀 Upload Batch'}
      </button>

      {/* Progress Bar */}
      {uploading && (
        <div
          style={{
            marginTop: '1rem',
            height: '8px',
            backgroundColor: '#e2e8f0',
            borderRadius: '4px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${progress}%`,
              height: '100%',
              backgroundColor: '#16a34a',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      )}

      {/* Info Box */}
      <div style={{
        marginTop: '2rem',
        padding: '1.5rem',
        backgroundColor: '#eff6ff',
        borderRadius: '8px',
        border: '1px solid #bfdbfe'
      }}>
        <h4 style={{ marginBottom: '0.5rem', color: '#1e40af' }}>ℹ️ How it works</h4>
        <ul style={{ color: '#1e40af', fontSize: '0.875rem', lineHeight: '1.6' }}>
          <li>Upload up to {maxBatchFiles} files in a single batch</li>
          <li>Our AI will attempt to auto-extract data from each file</li>
          <li>Files that cannot be auto-extracted will be queued for manual review</li>
          <li>You'll receive an email when all files are processed (within 24 hours)</li>
          <li>Once ready, you can generate your emissions report with one click</li>
        </ul>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}