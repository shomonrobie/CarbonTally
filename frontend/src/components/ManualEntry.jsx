// frontend/src/components/ManualEntry.jsx
import React from 'react';
import { useManualEntry } from '../hooks/useManualEntry';
import ManualEntryView from './ManualEntryView';
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

const ManualEntry = ({ file, organization, onBack, onComplete }) => {
  const manualEntry = useManualEntry(file, organization, false, null);

  const handleSubmit = async () => {
    const success = await manualEntry.handleSubmit();
    if (success && onComplete) {
      onComplete();
    }
  };

  // ✅ Show loading if file is not available
  if (!file) {
    return (
      <div className="manual-entry-container">
        <div className="loading-state">
          <p>No file selected</p>
          <button className="back-btn" onClick={onBack}>
            <FaArrowLeft /> Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <ManualEntryView
      {...manualEntry}
      file={file}
      isAdminMode={false}
      onBack={onBack}
      onSubmit={handleSubmit}
    />
  );
};

export default ManualEntry;