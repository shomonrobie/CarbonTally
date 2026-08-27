// frontend/src/v3/admin/LocationsTab.jsx
// D17 / N2 — Locations surface.
//
// Engineering decision (N2): Locations reuse the existing `facilities` model —
// the RC2 `facilities` table already carries full address fields (address_line1/
// city/county/country/region, latitude/longitude, postcode/eircode, meter
// MPAN/MPRN) and a `type` discriminator, so it already serves as the
// "facilities/locations" entity. No separate `locations` table is created.
//
// This tab presents facilities as the Locations hierarchy of the organisation
// (organisation → locations → facilities → assets/vehicles). Management of the
// underlying records lives in the "Facilities & Assets" tab to avoid duplicate
// CRUD surfaces.
import React, { useCallback, useEffect, useState } from 'react';
import { listFacilities } from '../api';
import { LoadingState, ErrorState, Alert } from '../components/ui';
import DataTable from '../components/ui/DataTable';

export default function LocationsTab({ organization }) {
  const [facilities, setFacilities] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await listFacilities(organization.id);
      setFacilities(result.facilities || []);
    } catch (e) {
      setError(e.message || 'Failed to load locations');
    } finally {
      setLoading(false);
    }
  }, [organization.id]);

  useEffect(() => { load(); }, [load, retryCount]);

  if (loading) return <LoadingState label="Loading locations…" />;
  if (error) return <ErrorState inline message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  const types = [...new Set(facilities.map((f) => f.type || 'Unclassified').filter(Boolean))].sort();
  const filtered = filter ? facilities.filter((f) => (f.type || 'Unclassified') === filter) : facilities;

  const columns = [
    { key: 'name', header: 'Location', accessor: 'name', render: (row) => <strong>{row.name}</strong>, isHeader: true },
    {
      key: 'address',
      header: 'Address',
      accessor: 'address',
      render: (row) => [row.address, row.postcode].filter(Boolean).join(', ') || '—',
    },
    { key: 'type', header: 'Type', accessor: 'type', render: (row) => row.type || 'Unclassified' },
    {
      key: 'status',
      header: 'Status',
      accessor: 'is_active',
      render: (row) => (row.is_active ? 'Active' : 'Inactive'),
    },
  ];

  return (
    <div>
      <Alert tone="info" title="Locations">
        Locations are the sites where your activities happen (organisation → locations → facilities →
        assets/vehicles). CarbonTally models locations on the facilities entity — manage the underlying records in the
        Facilities &amp; Assets tab.
      </Alert>

      {types.length > 1 && (
        <div className="v3-actions" style={{ marginTop: 12 }}>
          <label className="ct-field__label" htmlFor="location-filter">Filter by type</label>
          <select id="location-filter" className="v3-input" value={filter} onChange={(e) => setFilter(e.target.value)} style={{ width: 'auto' }}>
            <option value="">All locations</option>
            {types.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      )}

      {filtered.length === 0 ? (
        <p className="v3-muted" style={{ marginTop: 16 }}>
          No locations recorded yet. Locations never block normal processing (D17).
        </p>
      ) : (
        <div style={{ marginTop: 16 }}>
          <DataTable caption="Organisation locations" columns={columns} rows={filtered} rowKey="id" />
        </div>
      )}
    </div>
  );
}
