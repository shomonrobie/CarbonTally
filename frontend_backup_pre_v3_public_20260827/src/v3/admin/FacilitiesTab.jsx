// frontend/src/v3/admin/FacilitiesTab.jsx
// Facilities + assets using the V3 org-scoped backend (real data).
import React, { useCallback, useEffect, useState } from 'react';
import {
  createAsset,
  createFacility,
  listAssets,
  listFacilities,
  removeAsset,
  removeFacility,
} from '../api';

export default function FacilitiesTab({ organization }) {
  const [facilities, setFacilities] = useState([]);
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [showFacility, setShowFacility] = useState(false);
  const [showAsset, setShowAsset] = useState(false);
  const [confirmRemove, setConfirmRemove] = useState(null);
  const [facilityForm, setFacilityForm] = useState({ name: '', postcode: '', country: 'GB' });
  const [assetForm, setAssetForm] = useState({ name: '', facility_id: '', type: '' });

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [facilitiesResult, assetsResult] = await Promise.all([
        listFacilities(organization.id),
        listAssets(organization.id),
      ]);
      setFacilities(facilitiesResult.facilities || []);
      setAssets(assetsResult.assets || []);
    } catch (e) {
      setError(e.message || 'Failed to load facilities');
    } finally {
      setLoading(false);
    }
  }, [organization.id]);

  useEffect(() => { load(); }, [load]);

  const flash = (message) => {
    setNotice(message);
    setTimeout(() => setNotice(''), 5000);
  };

  const onAddFacility = async () => {
    setError('');
    try {
      await createFacility(organization.id, facilityForm);
      setShowFacility(false);
      setFacilityForm({ name: '', postcode: '', country: 'GB' });
      flash('Facility added.');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to add facility');
    }
  };

  const onAddAsset = async () => {
    setError('');
    try {
      await createAsset(organization.id, assetForm);
      setShowAsset(false);
      setAssetForm({ name: '', facility_id: '', type: '' });
      flash('Asset added.');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to add asset');
    }
  };

  const onRemove = async (kind, id) => {
    try {
      if (kind === 'facility') await removeFacility(id);
      else await removeAsset(id);
      setConfirmRemove(null);
      flash(`${kind === 'facility' ? 'Facility' : 'Asset'} removed.`);
      await load();
    } catch (e) {
      setError(e.message || 'Failed to remove');
    }
  };

  const assetCount = (facilityId) => assets.filter((a) => a.facility_id === facilityId).length;

  return (
    <div>
      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {notice && <div className="v3-note">{notice}</div>}

      <div className="v3-admin-card">
        <div className="v3-admin-actions" style={{ marginTop: 0 }}>
          <h2 style={{ margin: 0, flex: 1 }}>Facilities</h2>
          <button className="v3-btn v3-btn-primary" onClick={() => setShowFacility(true)}>+ New facility</button>
        </div>
        {loading ? (
          <div className="v3-loading"><div className="spinner" />Loading facilities…</div>
        ) : facilities.length === 0 ? (
          <div className="v3-empty">No facilities yet.</div>
        ) : (
          <table className="v3-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Postcode</th>
                <th>Country</th>
                <th>Type</th>
                <th>Assets</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {facilities.map((facility) => (
                <tr key={facility.id}>
                  <td><div className="v3-report-name">{facility.name}</div></td>
                  <td className="v3-muted">{facility.postcode || '—'}</td>
                  <td className="v3-muted">{facility.country || '—'}</td>
                  <td className="v3-muted">{facility.type || '—'}</td>
                  <td>{assetCount(facility.id)}</td>
                  <td>
                    <button className="v3-btn v3-btn-sm" onClick={() => setConfirmRemove({ kind: 'facility', id: facility.id, name: facility.name })}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="v3-admin-card">
        <div className="v3-admin-actions" style={{ marginTop: 0 }}>
          <h2 style={{ margin: 0, flex: 1 }}>Assets</h2>
          <button className="v3-btn v3-btn-primary" onClick={() => setShowAsset(true)}>+ New asset</button>
        </div>
        {loading ? (
          <div className="v3-loading"><div className="spinner" />Loading assets…</div>
        ) : assets.length === 0 ? (
          <div className="v3-empty">No assets yet.</div>
        ) : (
          <table className="v3-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Facility</th>
                <th>Type</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <tr key={asset.id}>
                  <td><div className="v3-report-name">{asset.name}</div></td>
                  <td className="v3-muted">{asset.facility_id || '—'}</td>
                  <td className="v3-muted">{asset.type || '—'}</td>
                  <td>
                    <button className="v3-btn v3-btn-sm" onClick={() => setConfirmRemove({ kind: 'asset', id: asset.id, name: asset.name })}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showFacility && (
        <div className="v3-modal-backdrop" onClick={() => setShowFacility(false)}>
          <div className="v3-modal" onClick={(e) => e.stopPropagation()}>
            <h2>New facility</h2>
            <div className="v3-form-group"><label>Name</label><input value={facilityForm.name} onChange={(e) => setFacilityForm({ ...facilityForm, name: e.target.value })} /></div>
            <div className="v3-form-group"><label>Postcode</label><input value={facilityForm.postcode} onChange={(e) => setFacilityForm({ ...facilityForm, postcode: e.target.value })} /></div>
            <div className="v3-form-group">
              <label>Country</label>
              <select value={facilityForm.country} onChange={(e) => setFacilityForm({ ...facilityForm, country: e.target.value })}>
                <option value="GB">GB</option>
                <option value="IE">IE</option>
              </select>
            </div>
            <div className="v3-modal-actions">
              <button className="v3-btn" onClick={() => setShowFacility(false)}>Cancel</button>
              <button className="v3-btn v3-btn-primary" onClick={onAddFacility} disabled={!facilityForm.name.trim()}>Add facility</button>
            </div>
          </div>
        </div>
      )}

      {showAsset && (
        <div className="v3-modal-backdrop" onClick={() => setShowAsset(false)}>
          <div className="v3-modal" onClick={(e) => e.stopPropagation()}>
            <h2>New asset</h2>
            <div className="v3-form-group"><label>Name</label><input value={assetForm.name} onChange={(e) => setAssetForm({ ...assetForm, name: e.target.value })} /></div>
            <div className="v3-form-group">
              <label>Facility</label>
              <select value={assetForm.facility_id} onChange={(e) => setAssetForm({ ...assetForm, facility_id: e.target.value })}>
                <option value="">None</option>
                {facilities.map((facility) => <option key={facility.id} value={facility.id}>{facility.name}</option>)}
              </select>
            </div>
            <div className="v3-form-group"><label>Type</label><input value={assetForm.type} onChange={(e) => setAssetForm({ ...assetForm, type: e.target.value })} /></div>
            <div className="v3-modal-actions">
              <button className="v3-btn" onClick={() => setShowAsset(false)}>Cancel</button>
              <button className="v3-btn v3-btn-primary" onClick={onAddAsset} disabled={!assetForm.name.trim()}>Add asset</button>
            </div>
          </div>
        </div>
      )}

      {confirmRemove && (
        <div className="v3-modal-backdrop" onClick={() => setConfirmRemove(null)}>
          <div className="v3-modal v3-confirm-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Remove {confirmRemove.kind}?</h2>
            <p className="v3-muted">{confirmRemove.name} will be marked inactive.</p>
            <div className="v3-modal-actions">
              <button className="v3-btn" onClick={() => setConfirmRemove(null)}>Cancel</button>
              <button className="v3-btn v3-btn-danger" onClick={() => onRemove(confirmRemove.kind, confirmRemove.id)}>
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

