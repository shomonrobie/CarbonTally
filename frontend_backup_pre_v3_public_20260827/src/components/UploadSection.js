// src/components/UploadSection.js

import React, { useState } from 'react';
import { FaUpload, FaFilePdf, FaImage, FaFileExcel, FaSync } from 'react-icons/fa';
import PDFRepairTool from './PDFRepairTool';
import '../css/UploadSection.css';
import toast from 'react-hot-toast';


const UploadSection = ({
  onFileSelect,
  onUpload,
  uploadType,
  setUploadType,
  loading,
  error,
  file,
  setFile,
  result,
  children
}) => {
  const [showRepairTool, setShowRepairTool] = useState(false);
  const [fileToRepair, setFileToRepair] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    const isPDF = selectedFile.type === 'application/pdf' || 
                  selectedFile.name.toLowerCase().endsWith('.pdf');
    const isImage = selectedFile.type.startsWith('image/');

    if (isPDF || isImage) {
      // Check if PDF is likely corrupted/scanned
      if (isPDF && selectedFile.size > 100 * 1024) {
        // Suggest repair for larger PDFs (likely scanned)
        setFileToRepair(selectedFile);
        setShowRepairTool(true);
        return;
      }
    }

    onFileSelect(selectedFile);
  };

  const handleRepairComplete = (repairedFile) => {
    setShowRepairTool(false);
    onFileSelect(repairedFile);
    toast.success('✅ Repaired file ready for upload!');
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      const isPDF = droppedFile.type === 'application/pdf' || 
                    droppedFile.name.toLowerCase().endsWith('.pdf');
      
      if (isPDF && droppedFile.size > 100 * 1024) {
        setFileToRepair(droppedFile);
        setShowRepairTool(true);
        return;
      }
      onFileSelect(droppedFile);
    }
  };

  const clearFile = () => {
    setFile(null);
    const fileInput = document.getElementById('singleFileInput');
    if (fileInput) fileInput.value = '';
  };

  return (
    <div className="upload-section">
      {/* PDF Repair Tool Modal */}
      {showRepairTool && fileToRepair && (
        <div className="repair-tool-overlay">
          <PDFRepairTool
            file={fileToRepair}
            onRepairComplete={handleRepairComplete}
            onClose={() => {
              setShowRepairTool(false);
              setFileToRepair(null);
            }}
          />
        </div>
      )}

      <div className="upload-header">
        <h2>Upload Data Statement</h2>
        <button
          onClick={() => setShowRepairTool(true)}
          className="repair-tool-trigger"
        >
          <FaSync /> Fix PDF Issues
        </button>
      </div>

      {/* Data Type Selector */}
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

      {/* Unified Drag & Drop Zone */}
      <div
        className={`upload-dropzone ${file ? 'has-file' : ''}`}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => document.getElementById('singleFileInput').click()}
      >
        <div className="dropzone-icon">
          {file ? '✅' : '📄'}
        </div>
        <p className="dropzone-text">
          {file ? file.name : 'Drag & drop your file here'}
        </p>
        <p className="dropzone-subtext">
          {file ? `${(file.size / 1024).toFixed(1)} KB` : 'or click to browse'}
        </p>
        <p className="dropzone-hint">
          Supports CSV, XLSX, PDF, JPG, PNG
        </p>

        <input
          id="singleFileInput"
          type="file"
          accept=".csv,.xlsx,.pdf,.jpg,.jpeg,.png"
          onChange={handleFileChange}
          className="file-input-hidden"
        />
      </div>

      {/* File Actions */}
      {file && (
        <div className="file-actions">
          <button onClick={clearFile} className="remove-file-btn">
            ✕ Remove File
          </button>
          <button onClick={onUpload} disabled={loading} className="upload-btn primary">
            {loading ? 'Processing...' : (
              uploadType === 'fuel' ? 'Calculate Scope 1 Emissions' :
              uploadType === 'utility' ? 'Calculate Scope 2 Emissions' :
              'Calculate Scope 3 Emissions'
            )}
          </button>
        </div>
      )}

      {error && <div className="upload-error">{error}</div>}

      {/* Review Queue Section */}
      {result && children}
    </div>
  );
};

export default UploadSection;