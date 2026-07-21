import React, { useState, useEffect } from 'react';
import { FaTimes, FaSave } from 'react-icons/fa';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';

const DefraFactorModal = ({ isOpen, onClose, factor, onSuccess }) => {
  const [formData, setFormData] = useState({
    activity_type: '',
    reporting_year: new Date().getFullYear(),
    co2e_multiplier: 0,
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (factor) {
      setFormData({
        activity_type: factor.activity_type || '',
        reporting_year: factor.reporting_year || new Date().getFullYear(),
        co2e_multiplier: factor.co2e_multiplier || 0,
      });
    } else {
      setFormData({
        activity_type: '',
        reporting_year: new Date().getFullYear(),
        co2e_multiplier: 0,
      });
    }
  }, [factor]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Validate
      if (!formData.activity_type.trim()) {
        toast.error('Activity type is required');
        setLoading(false);
        return;
      }

      if (formData.co2e_multiplier < 0) {
        toast.error('Multiplier cannot be negative');
        setLoading(false);
        return;
      }

      // Check for duplicates
      const { data: existing } = await supabase
        .from('defra_conversion_factors')
        .select('id')
        .eq('activity_type', formData.activity_type.trim())
        .eq('reporting_year', formData.reporting_year)
        .maybeSingle();

      if (existing && (!factor || existing.id !== factor.id)) {
        toast.error(`A factor for "${formData.activity_type}" in ${formData.reporting_year} already exists`);
        setLoading(false);
        return;
      }

      let error;
      if (factor) {
        // Update
        const { error: updateError } = await supabase
          .from('defra_conversion_factors')
          .update({
            activity_type: formData.activity_type.trim(),
            reporting_year: formData.reporting_year,
            co2e_multiplier: formData.co2e_multiplier,
          })
          .eq('id', factor.id);
        error = updateError;
      } else {
        // Insert
        const { error: insertError } = await supabase
          .from('defra_conversion_factors')
          .insert({
            activity_type: formData.activity_type.trim(),
            reporting_year: formData.reporting_year,
            co2e_multiplier: formData.co2e_multiplier,
          });
        error = insertError;
      }

      if (error) throw error;

      toast.success(factor ? 'Factor updated successfully!' : 'Factor added successfully!');
      onSuccess();
      onClose();
    } catch (error) {
      toast.error('Failed to save: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 10 }, (_, i) => currentYear - 5 + i);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        {/* Backdrop */}
        <div className="fixed inset-0 bg-black/50" onClick={onClose}></div>

        {/* Modal */}
        <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">
              {factor ? '✏️ Edit DEFRA Factor' : '➕ Add DEFRA Factor'}
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <FaTimes />
            </button>
          </div>

          {/* Body */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Activity Type *
              </label>
              <input
                type="text"
                value={formData.activity_type}
                onChange={(e) => setFormData({ ...formData, activity_type: e.target.value })}
                placeholder="e.g., Diesel (DERV)"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Use exact name as per DEFRA guidelines (e.g., "Diesel (DERV)", "Petrol (Unleaded)")
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reporting Year *
              </label>
              <select
                value={formData.reporting_year}
                onChange={(e) => setFormData({ ...formData, reporting_year: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                required
              >
                {years.map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                CO2e Multiplier *
              </label>
              <input
                type="number"
                step="0.000001"
                min="0"
                value={formData.co2e_multiplier}
                onChange={(e) => setFormData({ ...formData, co2e_multiplier: parseFloat(e.target.value) || 0 })}
                placeholder="e.g., 2.54"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                kg CO2e per unit of activity
              </p>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-xs text-yellow-800">
                ⚠️ Changing this value will affect all emissions calculations using this factor.
                Ensure you have the correct value from official DEFRA sources.
              </p>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FaSave />
                {loading ? 'Saving...' : factor ? 'Update' : 'Add'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default DefraFactorModal;