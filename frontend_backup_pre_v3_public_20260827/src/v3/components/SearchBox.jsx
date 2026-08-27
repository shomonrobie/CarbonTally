// frontend/src/v3/components/SearchBox.jsx
// G-P1-1 — org-scoped search box for the app shell. Queries the backend search
// endpoint (scope enforced server-side); results navigate to the relevant
// surface. Debounced; never caches data client-side.
import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchOrg } from '../api';
import Icon from './ui/Icon';

const TYPE_LABEL = {
  document: 'Document',
  item: 'Processing item',
  issue: 'Issue',
  supplier: 'Supplier',
  facility: 'Location',
  vehicle: 'Vehicle',
  report: 'Report',
};

function resultRoute(result) {
  switch (result.type) {
    case 'report': return `/reports/${result.id}`;
    case 'item': return `/processing`;
    case 'issue': return `/issues`;
    case 'document': return `/documents`;
    default: return `/organization`;
  }
}

export default function SearchBox({ organizationId }) {
  const navigate = useNavigate();
  const [q, setQ] = useState('');
  const [results, setResults] = useState(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const boxRef = useRef(null);

  // Debounce the backend query.
  useEffect(() => {
    if (!organizationId || !q.trim() || q.trim().length < 2) {
      setResults(null);
      setLoading(false);
      return undefined;
    }
    setLoading(true);
    const timer = setTimeout(() => {
      searchOrg(organizationId, q.trim(), 12)
        .then((body) => { setResults(body.results || []); setError(''); })
        .catch((e) => { setError(e.message || 'Search failed'); setResults([]); })
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(timer);
  }, [q, organizationId]);

  useEffect(() => {
    const onClick = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const go = (result) => {
    setOpen(false);
    setQ('');
    setResults(null);
    navigate(resultRoute(result));
  };

  return (
    <div className="ct-search" ref={boxRef}>
      <div className="ct-search__input-wrap">
        <Icon name="search" size={15} aria-hidden="true" />
        <input
          type="search"
          className="ct-search__input"
          placeholder="Search this organisation…"
          aria-label="Search this organisation"
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
        />
        {loading && <span className="ct-spinner ct-spinner--sm" aria-hidden="true" />}
      </div>

      {open && q.trim().length >= 2 && (
        <div className="ct-search__results" role="listbox" aria-label="Search results">
          {error && <div className="ct-search__empty">Search unavailable — {error}</div>}
          {!error && results === null && <div className="ct-search__empty">Type to search…</div>}
          {!error && results !== null && results.length === 0 && (
            <div className="ct-search__empty">No results for "{q}".</div>
          )}
          {!error && results !== null && results.length > 0 && (
            results.map((r) => (
              <button key={`${r.type}-${r.id}`} type="button" className="ct-search__result" role="option" onClick={() => go(r)}>
                <span className="ct-search__type">{TYPE_LABEL[r.type] || r.type}</span>
                <span className="ct-search__label">{r.label}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
