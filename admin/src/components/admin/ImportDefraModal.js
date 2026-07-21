import React, { useState } from 'react';
import { FaTimes, FaUpload, FaFileAlt } from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';
import * as XLSX from 'xlsx';

const ImportDefraModal = ({ isOpen, onClose, onSuccess }) => {
  const [file, setFile] = useState(null);
  const [previewData, setPreviewData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: Upload, 2: Preview & Confirm

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    
    // Parse file for preview
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = new Uint8Array(event.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(firstSheet);
        setPreviewData(jsonData);
        setStep(2);
      } catch (error) {
        toast.error('Failed to parse file: ' + error.message);
      }
    };
    reader.readAsArrayBuffer(selectedFile);
  };

  const handleImport = async () => {
    setLoading(true);
    try {
      let records = [];
      
      if (file.name.endsWith('.csv') || file.name.endsWith('.xlsx')) {
        // Use the already parsed data
        records = previewData.map(row => ({
          activity_type: row['Activity Type'] || row['activity_type'] || row['Activity_Type'] || '',
          reporting_year: parseInt(row['Reporting Year'] || row['reporting_year'] || row['Reporting_Year'] || 2024),
          co2e_multiplier: parseFloat(row['CO2e Multiplier'] || row['co2e_multiplier'] || row['CO2e_Multiplier'] || 0),
        }));
      }

      // Validate records
      const invalidRecords = records.filter(r => !r.activity_type || !r.reporting_year);
      if (invalidRecords.length > 0) {
        toast.error(`Found ${invalidRecords.length} invalid records. Please check your file format.`);
        setLoading(false);
        return;
      }

      // Insert records
      let successCount = 0;
      let errorCount = 0;

      for (const record of records) {
        try {
          // Check if exists
          const { data: existing } = await supabase
            .from('defra_conversion_factors')
            .select('id')
            .eq('activity_type', record.activity_type.trim())
            .eq('reporting_year', record.reporting_year)
            .maybeSingle();

          if (existing) {
            // Update
            await supabase
              .from('defra_conversion_factors')
              .update({
                co2e_multiplier: record.co2e_multiplier,
              })
              .eq('id', existing.id);
          } else {
            // Insert
            await supabase
              .from('defra_conversion_factors')
              .insert({
                activity_type: record.activity_type.trim(),
                reporting_year: record.reporting_year,
                co2e_multiplier: record.co2e_multiplier,
              });
          }
          successCount++;
        } catch (error) {
          errorCount++;
          console.error('Error importing record:', record, error);
        }
      }

      toast.success(`✅ Imported ${successCount} records${errorCount > 0 ? ` (${errorCount} errors)` : ''}`);
      onSuccess();
      onClose();
    } catch (error) {
      toast.error('Import failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black/50" onClick={onClose}></div>

        <div className="relative bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">📤 Import DEFRA Factors</h2>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <FaTimes />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
            {step === 1 ? (
              <div className="text-center py-12">
                <div className="mb-6">
                  <div className="text-6xl mb-4">📄</div>
                  <h3 className="text-lg font-medium text-gray-900">Upload DEFRA Factors File</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Upload CSV or Excel file with DEFRA conversion factors
                  </p>
                </div>

                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 hover:border-primary-400 transition-colors">
                  <input
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileChange}
                    className="hidden"
                    id="fileUpload"
                  />
                  <label
                    htmlFor="fileUpload"
                    className="cursor-pointer flex flex-col items-center"
                  >
                    <FaFileAlt className="text-4xl text-gray-400 mb-3" />
                    <span className="text-primary-600 font-medium">Click to upload</span>
                    <span className="text-xs text-gray-500 mt-1">or drag and drop</span>
                  </label>
                </div>

                <div className="mt-4 text-left">
                  <h4 className="font-medium text-gray-700 text-sm mb-2">Expected Format:</h4>
                  <div className="bg-gray-50 rounded-lg p-3 text-xs font-mono text-gray-600">
                    <div>Activity Type, Reporting Year, CO2e Multiplier</div>
                    <div>Diesel (DERV), 2024, 2.54</div>
                    <div>Petrol (Unleaded), 2024, 2.16</div>
                    <div>Electricity, 2024, 0.20712</div>
                  </div>
                </div>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-medium text-gray-900">Preview Data</h3>
                    <p className="text-sm text-gray-500">{previewData.length} records found</p>
                  </div>
                  <button
                    onClick={() => {
                      setStep(1);
                      setFile(null);
                      setPreviewData([]);
                    }}
                    className="text-sm text-primary-600 hover:text-primary-700"
                  >
                    ← Choose different file
                  </button>
                </div>

                <div className="border rounded-lg overflow-hidden max-h-96 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Activity Type</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Year</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Multiplier</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {previewData.slice(0, 50).map((row, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-4 py-2">{row['Activity Type'] || row['activity_type'] || row['Activity_Type'] || 'N/A'}</td>
                          <td className="px-4 py-2">{row['Reporting Year'] || row['reporting_year'] || row['Reporting_Year'] || 'N/A'}</td>
                          <td className="px-4 py-2 text-right font-mono">
                            {row['CO2e Multiplier'] || row['co2e_multiplier'] || row['CO2e_Multiplier'] || 'N/A'}
                          </td>
                        </tr>
                      ))}
                      {previewData.length > 50 && (
                        <tr>
                          <td colSpan="3" className="px-4 py-2 text-center text-gray-500 text-sm">
                            ... and {previewData.length - 50} more records
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-xs text-yellow-800">
                    ⚠️ Existing factors will be updated. New factors will be added.
                    This action cannot be undone.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            {step === 2 && (
              <button
                onClick={handleImport}
                disabled={loading || previewData.length === 0}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FaUpload />
                {loading ? 'Importing...' : `Import ${previewData.length} Records`}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImportDefraModal;