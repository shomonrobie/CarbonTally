import React, { useState } from 'react';
import { supabase } from './supabaseClient';
import toast from 'react-hot-toast';

export default function OnboardingWizard({ userId, onComplete, onSkip }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Step 1: Company Info
  const [companyName, setCompanyName] = useState('');
  const [companyNumber, setCompanyNumber] = useState('');
  const [organizationId, setOrganizationId] = useState(null);
  
  // Step 2: First Facility
  const [facilityName, setFacilityName] = useState('');
  const [facilityPostcode, setFacilityPostcode] = useState('');
  const [facilityId, setFacilityId] = useState(null);
  
  // Step 3: First Asset (Optional)
  const [assetName, setAssetName] = useState('');
  const [assetType, setAssetType] = useState('vehicle');
  const [assetDescription, setAssetDescription] = useState('');

  const totalSteps = 4;

  // Step 1: Create Organization
  const handleCreateCompany = async () => {
    if (!companyName.trim()) {
      toast.error('Please enter your company name');
      return;
    }

    setLoading(true);
    try {
      // Create organization
      const { data: orgData, error: orgError } = await supabase
        .from('organizations')
        .insert({
          name: companyName.trim(),
          company_number: companyNumber.trim() || null
        })
        .select()
        .single();

      if (orgError) throw orgError;

      // Link user to organization as admin
      const { error: memberError } = await supabase
        .from('organization_members')
        .insert({
          organization_id: orgData.id,
          user_id: userId,
          role: 'admin'
        });

      if (memberError) throw memberError;

      setOrganizationId(orgData.id);
      toast.success('Company created successfully!');
      setCurrentStep(2);
    } catch (error) {
      console.error('Error creating company:', error);
      toast.error('Failed to create company. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Create First Facility
  const handleCreateFacility = async () => {
    if (!facilityName.trim()) {
      toast.error('Please enter a facility name');
      return;
    }

    setLoading(true);
    try {
      const { data: facilityData, error } = await supabase
        .from('facilities')
        .insert({
          organization_id: organizationId,
          name: facilityName.trim(),
          postcode: facilityPostcode.trim().toUpperCase() || null
        })
        .select()
        .single();

      if (error) throw error;

      setFacilityId(facilityData.id);
      toast.success('Facility added successfully!');
      setCurrentStep(3);
    } catch (error) {
      console.error('Error creating facility:', error);
      toast.error('Failed to add facility. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Create First Asset (Optional)
  const handleCreateAsset = async () => {
    if (assetName.trim()) {
      setLoading(true);
      try {
        const { error } = await supabase
          .from('assets')
          .insert({
            facility_id: facilityId,
            name: assetName.trim(),
            description: assetDescription.trim() || null
          });

        if (error) throw error;

        toast.success('Asset added successfully!');
      } catch (error) {
        console.error('Error creating asset:', error);
        toast.error('Failed to add asset, but continuing...');
      } finally {
        setLoading(false);
      }
    }

    setCurrentStep(4);
  };

  // Step 4: Complete Onboarding
  const handleComplete = () => {
    toast.success('Welcome to CarbonTally! 🎉');
    onComplete();
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '1rem'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '16px',
        maxWidth: '600px',
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)'
      }}>
        {/* Header with Progress */}
        <div style={{
          padding: '2rem 2rem 1rem',
          borderBottom: '1px solid #e2e8f0'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1.5rem'
          }}>
            <div style={{
              fontSize: '1.5rem',
              fontWeight: '700',
              color: '#0f172a'
            }}>
              🌱 CarbonTally Setup
            </div>
            {currentStep < 4 && (
              <button
                onClick={onSkip}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#64748b',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  textDecoration: 'underline'
                }}
              >
                Skip for now
              </button>
            )}
          </div>

          {/* Progress Bar */}
          <div style={{
            display: 'flex',
            gap: '0.5rem',
            marginBottom: '0.5rem'
          }}>
            {[1, 2, 3, 4].map((step) => (
              <div
                key={step}
                style={{
                  flex: 1,
                  height: '6px',
                  borderRadius: '3px',
                  backgroundColor: step <= currentStep ? '#16a34a' : '#e2e8f0',
                  transition: 'background-color 0.3s'
                }}
              />
            ))}
          </div>
          <div style={{
            fontSize: '0.85rem',
            color: '#64748b',
            textAlign: 'center'
          }}>
            Step {currentStep} of {totalSteps}
          </div>
        </div>

        {/* Content */}
        <div style={{ padding: '2rem' }}>
          {/* Step 1: Company Info */}
          {currentStep === 1 && (
            <>
              <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏢</div>
                <h2 style={{ margin: '0 0 0.5rem 0', color: '#0f172a' }}>
                  Welcome to CarbonTally!
                </h2>
                <p style={{ color: '#64748b', margin: 0, fontSize: '1rem' }}>
                  Let's set up your company profile to get started.
                </p>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#0f172a' }}>
                  Company Name *
                </label>
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g., Birmingham Logistics Ltd"
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    outline: 'none'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#16a34a'}
                  onBlur={(e) => e.target.style.borderColor = '#cbd5e1'}
                />
              </div>

              <div style={{ marginBottom: '2rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#0f172a' }}>
                  Company Number (Optional)
                </label>
                <input
                  type="text"
                  value={companyNumber}
                  onChange={(e) => setCompanyNumber(e.target.value)}
                  placeholder="e.g., 12345678"
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    outline: 'none'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#16a34a'}
                  onBlur={(e) => e.target.style.borderColor = '#cbd5e1'}
                />
                <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.5rem' }}>
                  Your UK Companies House registration number (if applicable)
                </p>
              </div>

              <button
                onClick={handleCreateCompany}
                disabled={loading || !companyName.trim()}
                style={{
                  width: '100%',
                  padding: '1rem',
                  backgroundColor: companyName.trim() ? '#16a34a' : '#94a3b8',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '600',
                  fontSize: '1rem',
                  cursor: companyName.trim() ? 'pointer' : 'not-allowed'
                }}
              >
                {loading ? 'Creating...' : 'Continue →'}
              </button>
            </>
          )}

          {/* Step 2: First Facility */}
          {currentStep === 2 && (
            <>
              <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏭</div>
                <h2 style={{ margin: '0 0 0.5rem 0', color: '#0f172a' }}>
                  Add Your First Facility
                </h2>
                <p style={{ color: '#64748b', margin: 0, fontSize: '1rem' }}>
                  A facility is a physical location where you operate (office, warehouse, factory, etc.)
                </p>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#0f172a' }}>
                  Facility Name *
                </label>
                <input
                  type="text"
                  value={facilityName}
                  onChange={(e) => setFacilityName(e.target.value)}
                  placeholder="e.g., Birmingham Hub"
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    outline: 'none'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#16a34a'}
                  onBlur={(e) => e.target.style.borderColor = '#cbd5e1'}
                />
              </div>

              <div style={{ marginBottom: '2rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#0f172a' }}>
                  Postcode (Optional)
                </label>
                <input
                  type="text"
                  value={facilityPostcode}
                  onChange={(e) => setFacilityPostcode(e.target.value)}
                  placeholder="e.g., B1 1AA"
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    outline: 'none'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#16a34a'}
                  onBlur={(e) => e.target.style.borderColor = '#cbd5e1'}
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <button
                  onClick={() => setCurrentStep(1)}
                  style={{
                    flex: 1,
                    padding: '1rem',
                    backgroundColor: '#f1f5f9',
                    color: '#475569',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  ← Back
                </button>
                <button
                  onClick={handleCreateFacility}
                  disabled={loading || !facilityName.trim()}
                  style={{
                    flex: 2,
                    padding: '1rem',
                    backgroundColor: facilityName.trim() ? '#16a34a' : '#94a3b8',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: facilityName.trim() ? 'pointer' : 'not-allowed'
                  }}
                >
                  {loading ? 'Adding...' : 'Continue →'}
                </button>
              </div>
            </>
          )}

          {/* Step 3: First Asset (Optional) */}
          {currentStep === 3 && (
            <>
              <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🚗</div>
                <h2 style={{ margin: '0 0 0.5rem 0', color: '#0f172a' }}>
                  Add Your First Asset (Optional)
                </h2>
                <p style={{ color: '#64748b', margin: 0, fontSize: '1rem' }}>
                  Assets are vehicles, meters, or equipment at your facility that consume energy
                </p>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#0f172a' }}>
                  Asset Name
                </label>
                <input
                  type="text"
                  value={assetName}
                  onChange={(e) => setAssetName(e.target.value)}
                  placeholder="e.g., Van BV 67AAA or Main Electricity Meter"
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    outline: 'none'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#16a34a'}
                  onBlur={(e) => e.target.style.borderColor = '#cbd5e1'}
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#0f172a' }}>
                  Asset Type
                </label>
                <select
                  value={assetType}
                  onChange={(e) => setAssetType(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    outline: 'none',
                    backgroundColor: 'white'
                  }}
                >
                  <option value="vehicle">Vehicle</option>
                  <option value="meter">Utility Meter</option>
                  <option value="equipment">Equipment</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div style={{ marginBottom: '2rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#0f172a' }}>
                  Description (Optional)
                </label>
                <textarea
                  value={assetDescription}
                  onChange={(e) => setAssetDescription(e.target.value)}
                  placeholder="e.g., Small delivery van"
                  rows={3}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    outline: 'none',
                    resize: 'vertical',
                    fontFamily: 'inherit'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#16a34a'}
                  onBlur={(e) => e.target.style.borderColor = '#cbd5e1'}
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <button
                  onClick={() => setCurrentStep(2)}
                  style={{
                    flex: 1,
                    padding: '1rem',
                    backgroundColor: '#f1f5f9',
                    color: '#475569',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  ← Back
                </button>
                <button
                  onClick={handleCreateAsset}
                  style={{
                    flex: 2,
                    padding: '1rem',
                    backgroundColor: '#16a34a',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  {assetName.trim() ? 'Add Asset & Continue →' : 'Skip & Continue →'}
                </button>
              </div>
            </>
          )}

          {/* Step 4: Success */}
          {currentStep === 4 && (
            <>
              <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🎉</div>
                <h2 style={{ margin: '0 0 0.5rem 0', color: '#0f172a' }}>
                  You're All Set!
                </h2>
                <p style={{ color: '#64748b', margin: '0 0 2rem 0', fontSize: '1rem' }}>
                  Your CarbonTally account is ready to track emissions.
                </p>
              </div>

              <div style={{
                backgroundColor: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: '12px',
                padding: '1.5rem',
                marginBottom: '2rem'
              }}>
                <h3 style={{ margin: '0 0 1rem 0', color: '#166534', fontSize: '1.1rem' }}>
                  ✅ What's Next?
                </h3>
                <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#15803d', lineHeight: '1.8' }}>
                  <li>Upload your first utility bill or fuel invoice</li>
                  <li>Track emissions across your facilities</li>
                  <li>Generate your SECR compliance report</li>
                  <li>Invite team members to collaborate</li>
                </ul>
              </div>

              <button
                onClick={handleComplete}
                style={{
                  width: '100%',
                  padding: '1rem',
                  backgroundColor: '#16a34a',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '600',
                  fontSize: '1rem',
                  cursor: 'pointer'
                }}
              >
                🚀 Go to Dashboard
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}