// frontend/src/hooks/useManualEntry.js
import { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';
import toast from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const useManualEntry = (file, organization, isAdminMode = false, staffData = null) => {
  // File viewer state
  const [pdfNumPages, setPdfNumPages] = useState(null); // ✅ Add this
  const [pdfPageNumber, setPdfPageNumber] = useState(1);
  const [pdfScale, setPdfScale] = useState(1.0);
  const [pdfRotation, setPdfRotation] = useState(0);

  // Form state
  const [formData, setFormData] = useState({
    billing_start: '',
    reporting_year: new Date().getFullYear(),
    consumption: '',
    fuel_utility_type: '',
    facility_id: '',
    asset_name: '',
    notes: '',
    unit: 'kWh'
  });

  // UI State
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);
  const [draftId, setDraftId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [sectionsCompleted, setSectionsCompleted] = useState([]);
  const [facilities, setFacilities] = useState([]);
  const [assets, setAssets] = useState([]);
  const [selectedFacilityId, setSelectedFacilityId] = useState('');
  const [draftLoaded, setDraftLoaded] = useState(false);

  // Reference data for dropdowns
  const [fuelTypes, setFuelTypes] = useState([]);
  const [units, setUnits] = useState([]);
  const [loadingOptions, setLoadingOptions] = useState(true);

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  // Fetch reference data
  useEffect(() => {
    if (organization?.id) {
      fetchReferenceData();
      fetchFacilitiesAndAssets();
    }
  }, [organization?.id]);

  const fetchReferenceData = async () => {
    setLoadingOptions(true);
    const token = await getToken();

    try {
      const fuelResponse = await fetch(`${API_URL}/api/reference/fuel-types`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (fuelResponse.ok) {
        const data = await fuelResponse.json();
        setFuelTypes(data.fuel_types || []);
      }

      const unitResponse = await fetch(`${API_URL}/api/reference/units`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (unitResponse.ok) {
        const data = await unitResponse.json();
        setUnits(data.units || []);
      }
    } catch (error) {
      console.error('Error fetching reference data:', error);
    } finally {
      setLoadingOptions(false);
    }
  };

  const fetchFacilitiesAndAssets = async () => {
    try {
      const token = await getToken();
      
      const facResponse = await fetch(`${API_URL}/api/organizations/assets/facilities?limit=1000`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (facResponse.ok) {
        const data = await facResponse.json();
        setFacilities(data.facilities || []);
      }

      const assetResponse = await fetch(`${API_URL}/api/organizations/assets/?limit=1000`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (assetResponse.ok) {
        const data = await assetResponse.json();
        setAssets(data.assets || []);
      }
    } catch (error) {
      console.error('Error fetching facilities/assets:', error);
    }
  };

  // Draft management
  useEffect(() => {
    if (file?.id) {
      checkExistingDraft();
    }
  }, [file?.id]);

  const checkExistingDraft = async () => {
    try {
      const token = await getToken();
      const response = await fetch(
        `${API_URL}/api/drafts?file_id=${file.id}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      if (response.ok) {
        const data = await response.json();
        if (data.drafts && data.drafts.length > 0) {
          const draft = data.drafts[0];
          setDraftId(draft.id);
          setFormData(prev => ({
            ...prev,
            ...draft.data,
            notes: draft.data.notes || ''
          }));
          setProgress(draft.progress);
          setSectionsCompleted(draft.sections_completed || []);
          setDraftLoaded(true);
          
          if (draft.data.facility_id) {
            setSelectedFacilityId(draft.data.facility_id);
          }
          
          toast.success(`📝 Draft loaded (${draft.progress}% complete)`);
        }
      }
    } catch (error) {
      console.error('Error checking draft:', error);
    }
  };

  const calculateProgress = (data) => {
    const sections = [
      'billing_start',
      'consumption',
      'fuel_utility_type',
      'asset_name'
    ];
    
    let completed = 0;
    const completedSections = [];
    
    sections.forEach(section => {
      if (data[section] && data[section].toString().trim() !== '') {
        completed++;
        completedSections.push(section);
      }
    });
    
    const progressValue = Math.round((completed / sections.length) * 100);
    setProgress(progressValue);
    setSectionsCompleted(completedSections);
    
    return { progress: progressValue, sections: completedSections };
  };

  const handleChange = (field, value) => {
    const newData = { ...formData, [field]: value };
    setFormData(newData);
    calculateProgress(newData);
  };

  const handleFacilitySelect = (facilityId) => {
    setSelectedFacilityId(facilityId);
    handleChange('facility_id', facilityId);
    handleChange('asset_name', '');
  };

  const saveDraft = async () => {
    if (!file?.id) {
      toast.error('No file associated with this entry');
      return;
    }

    setSavingDraft(true);
    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/drafts/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          file_id: file.id,
          data: formData,
          progress: progress,
          sections_completed: sectionsCompleted
        })
      });

      if (response.ok) {
        const result = await response.json();
        setDraftId(result.draft_id);
        toast.success(`💾 Draft saved (${progress}% complete)`);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to save draft');
      }
    } catch (error) {
      console.error('Error saving draft:', error);
      toast.error('Failed to save draft');
    } finally {
      setSavingDraft(false);
    }
  };

  // Auto-save every 30 seconds
  useEffect(() => {
    if (!draftLoaded) return;
    
    const interval = setInterval(() => {
      if (progress > 0 && progress < 100) {
        saveDraft();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [formData, progress, draftLoaded]);

  const deleteDraft = async () => {
    if (!draftId) return;
    if (!window.confirm('Are you sure you want to discard this draft?')) return;

    const token = await getToken();

    try {
      const response = await fetch(`${API_URL}/api/drafts/${draftId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setDraftId(null);
        setProgress(0);
        setSectionsCompleted([]);
        toast.success('Draft discarded');
      }
    } catch (error) {
      console.error('Error deleting draft:', error);
      toast.error('Failed to delete draft');
    }
  };

  const handleSubmit = async () => {
    if (!formData.billing_start) {
      toast.error('Please enter billing period start date');
      return;
    }
    if (!formData.consumption || parseFloat(formData.consumption) <= 0) {
      toast.error('Please enter a valid consumption value');
      return;
    }
    if (!formData.fuel_utility_type) {
      toast.error('Please select fuel/utility type');
      return;
    }
    if (!formData.asset_name) {
      toast.error('Please enter asset name');
      return;
    }

    setSubmitting(true);

    try {
      const token = await getToken();
      
      if (draftId) {
        const response = await fetch(`${API_URL}/api/drafts/${draftId}/submit`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            ...formData,
            submitted_by: isAdminMode ? staffData?.id : null,
            submitted_by_email: isAdminMode ? staffData?.email : null,
            is_admin_submission: isAdminMode
          })
        });

        if (response.ok) {
          toast.success('✅ Data submitted successfully!');
          return true;
        } else {
          const error = await response.json();
          toast.error(error.detail || 'Failed to submit');
          return false;
        }
      } else {
        const saveResponse = await fetch(`${API_URL}/api/drafts/save`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            file_id: file.id,
            data: formData,
            progress: 100,
            sections_completed: ['billing_start', 'consumption', 'fuel_utility_type', 'asset_name']
          })
        });

        if (saveResponse.ok) {
          const result = await saveResponse.json();
          
          const submitResponse = await fetch(`${API_URL}/api/drafts/${result.draft_id}/submit`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              ...formData,
              submitted_by: isAdminMode ? staffData?.id : null,
              submitted_by_email: isAdminMode ? staffData?.email : null,
              is_admin_submission: isAdminMode
            })
          });

          if (submitResponse.ok) {
            toast.success('✅ Data submitted successfully!');
            return true;
          }
        }
        return false;
      }
    } catch (error) {
      console.error('Error submitting:', error);
      toast.error('Failed to submit data');
      return false;
    } finally {
      setSubmitting(false);
    }
  };

  // Rotation controls
  const rotateLeft = () => setPdfRotation(prev => (prev - 90 + 360) % 360);
  const rotateRight = () => setPdfRotation(prev => (prev + 90) % 360);
  const resetRotation = () => setPdfRotation(0);

  return {
    // State
    formData,
    setFormData,
    progress,
    sectionsCompleted,
    draftId,
    draftLoaded,
    loading,
    submitting,
    savingDraft,
    facilities,
    assets,
    selectedFacilityId,
    fuelTypes,
    units,
    loadingOptions,
    pdfNumPages,      // ✅ Added
    pdfPageNumber,
    pdfScale,
    pdfRotation,
    
    // Setters
    setPdfNumPages,   // ✅ Added
    setPdfPageNumber,
    setPdfScale,
    
    // Actions
    handleChange,
    handleFacilitySelect,
    saveDraft,
    deleteDraft,
    handleSubmit,
    rotateLeft,
    rotateRight,
    resetRotation,
    fetchFacilitiesAndAssets,
    fetchReferenceData,
    
    // Helpers
    getSectionStatus: (section) => sectionsCompleted.includes(section) ? 'completed' : 'pending',
    calculateProgress
  };
};