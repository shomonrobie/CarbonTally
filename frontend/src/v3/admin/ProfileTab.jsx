// frontend/src/v3/admin/ProfileTab.jsx
// Organization profile + settings (read + admin edit) from the V3 backend.
// Every field is a real V3M2 column surfaced by the V3 API.
import React, { useCallback, useEffect, useState } from 'react';
import {
  getOrganizationMetadata,
  getOrganizationProfile,
  updateOrganizationMetadata,
  updateOrganizationProfile,
} from '../api';

function Field({ label, value }) {
  return (
    <div className="v3-meta-item">
      <div className="k">{label}</div>
      <div className="v">{value || '—'}</div>
    </div>
  );
}

export default function ProfileTab({ organization }) {
  const [profile, setProfile] = useState(null);
  const [metadata, setMetadata] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState('');
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [profileResult, metadataResult] = await Promise.all([
        getOrganizationProfile(organization.id),
        getOrganizationMetadata(organization.id),
      ]);
      setProfile(profileResult.organization);
      setMetadata(metadataResult.metadata || {});
    } catch (e) {
      setError(e.message || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  }, [organization.id]);

  useEffect(() => { load(); }, [load]);

  const startEdit = () => {
    setForm({ ...profile });
    setEditing(true);
  };

  const onChange = (key) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm({ ...form, [key]: value });
  };

  const PROFILE_KEYS = [
    'name', 'company_number', 'industry', 'sector', 'company_size', 'vat_number',
    'registration_number', 'registered_address', 'country', 'timezone', 'currency',
    'financial_year_end', 'reporting_standard', 'secr_enabled', 'esrs_enabled',
    'issb_enabled', 'default_factor_year', 'preferred_units', 'website',
    'primary_contact_email', 'primary_contact_name', 'billing_contact_email',
    'billing_contact_name', 'billing_address', 'address_line1',
    'address_line2', 'city', 'county', 'postcode', 'eircode', 'language', 'locale',
    'business_structure', 'reporting_frequency', 'accounting_standard',
    'sustainability_standard', 'data_protection_officer', 'privacy_policy_url',
    'terms_url',
  ];

  const METADATA_KEYS = [
    'total_employees', 'full_time_employees', 'part_time_employees',
    'contract_employees', 'average_employees', 'annual_revenue',
    'total_floor_area_sqm', 'occupied_floor_area_sqm',
    'renewable_energy_percentage', 'carbon_offset_percentage',
    'industry_sector', 'naics_code', 'sic_code',
  ];

  const saveProfile = async () => {
    setError('');
    setSaved('');
    try {
      const payload = {};
      PROFILE_KEYS.forEach((key) => {
        if (form[key] !== undefined && form[key] !== '') payload[key] = form[key];
      });
      const result = await updateOrganizationProfile(organization.id, payload);
      setProfile(result.organization);
      setEditing(false);
      setSaved('Profile saved.');
      setTimeout(() => setSaved(''), 5000);
    } catch (e) {
      setError(e.message || 'Failed to save profile');
    }
  };

  const saveMetadata = async () => {
    setError('');
    setSaved('');
    try {
      const payload = {};
      METADATA_KEYS.forEach((key) => {
        if (metadata[key] !== undefined && metadata[key] !== '') {
          payload[key] = Number(metadata[key]);
        }
      });
      const result = await updateOrganizationMetadata(organization.id, payload);
      setMetadata(result.metadata);
      setSaved('Metadata saved.');
      setTimeout(() => setSaved(''), 5000);
    } catch (e) {
      setError(e.message || 'Failed to save metadata');
    }
  };

  if (loading) {
    return <div className="v3-loading"><div className="spinner" />Loading profile…</div>;
  }

  return (
    <div>
      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {saved && <div className="v3-note">{saved}</div>}

      <div className="v3-admin-card">
        <h2>Organization profile</h2>
        {!editing ? (
          <div className="v3-meta-list">
            <Field label="Name" value={profile?.name} />
            <Field label="Company number" value={profile?.company_number} />
            <Field label="Country" value={profile?.country} />
            <Field label="Industry" value={profile?.industry} />
            <Field label="Sector" value={profile?.sector} />
            <Field label="Company size" value={profile?.company_size} />
            <Field label="VAT number" value={profile?.vat_number} />
            <Field label="Registration number" value={profile?.registration_number} />
            <Field label="Registered address" value={profile?.registered_address} />
            <Field label="City" value={profile?.city} />
            <Field label="Postcode" value={profile?.postcode} />
            <Field label="Website" value={profile?.website} />
            <Field label="Currency" value={profile?.currency} />
            <Field label="Billing mode" value={profile?.billing_mode || '—'} />
            <Field label="Timezone" value={profile?.timezone} />
            <Field label="Reporting standard" value={profile?.reporting_standard} />
            <Field label="Primary contact" value={profile?.primary_contact_name} />
            <Field label="Primary email" value={profile?.primary_contact_email} />
            <Field label="Created" value={profile?.created_at} />
          </div>
        ) : (
          <div className="v3-form-grid">
            {PROFILE_KEYS.map((key) => (
              <div className="v3-form-group" key={key}>
                <label>{key.replace(/_/g, ' ')}</label>
                <input
                  value={form[key] ?? ''}
                  onChange={onChange(key)}
                  placeholder={key.replace(/_/g, ' ')}
                />
              </div>
            ))}
            <div className="v3-form-group">
              <label>Reporting standards</label>
              <div style={{ display: 'flex', gap: 16 }}>
                {['secr_enabled', 'esrs_enabled', 'issb_enabled'].map((flag) => (
                  <label className="v3-form-check" key={flag}>
                    <input type="checkbox" checked={!!form[flag]} onChange={onChange(flag)} />
                    {flag.replace(/_enabled/g, '').toUpperCase()}
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}
        <div className="v3-admin-actions">
          {!editing ? (
            <button className="v3-btn" onClick={startEdit}>Edit profile</button>
          ) : (
            <>
              <button className="v3-btn v3-btn-primary" onClick={saveProfile}>Save profile</button>
              <button className="v3-btn" onClick={() => setEditing(false)}>Cancel</button>
            </>
          )}
        </div>
      </div>

      <div className="v3-admin-card">
        <h2>Organization metadata</h2>
        <div className="v3-form-grid">
          {METADATA_KEYS.map((key) => (
            <div className="v3-form-group" key={key}>
              <label>{key.replace(/_/g, ' ')}</label>
              <input
                value={metadata[key] ?? ''}
                onChange={(e) => setMetadata({ ...metadata, [key]: e.target.value })}
              />
            </div>
          ))}
        </div>
        <div className="v3-admin-actions">
          <button className="v3-btn v3-btn-primary" onClick={saveMetadata}>Save metadata</button>
        </div>
      </div>
    </div>
  );
}
