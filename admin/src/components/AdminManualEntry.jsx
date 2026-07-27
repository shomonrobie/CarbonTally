// admin/src/components/AdminManualEntry.jsx
import React from 'react';
import { useManualEntry } from '../hooks/useManualEntry';
import ManualEntryView from './ManualEntryView';

const AdminManualEntry = ({ file, organization, staffData, onBack, onComplete }) => {
  const manualEntry = useManualEntry(file, organization, true, staffData);

  const handleSubmit = async () => {
    const success = await manualEntry.handleSubmit();
    if (success && onComplete) {
      onComplete();
    }
  };

  return (
    <ManualEntryView
      {...manualEntry}
      file={file}
      isAdminMode={true}
      staffData={staffData}
      onBack={onBack}
      onSubmit={handleSubmit}
    />
  );
};

export default AdminManualEntry;