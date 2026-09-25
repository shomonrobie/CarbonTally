// frontend/src/v3/capabilities/CapabilitiesPage.jsx
// P17-L — the CUSTOMER capability truth surface (CT-PO-P17-DECISION-03 §8).
//
// Answers exactly one question: "what does CarbonTally support?"
// It does NOT answer "which Scope 3 categories apply to my organisation?" —
// there is no customer-facing applicability model (PO-3, F-1), and this page
// contains no applicability control, label or state.
//
// The capability facts are PRODUCT-level: this page makes no tenant-scoped
// request at all. The customer's own results are reached from their Emissions
// and Reports pages, so the two facts can never be confused (§8).
import React, { useCallback, useEffect, useState } from 'react';
import { getCapabilityCatalogue } from '../api';
import CapabilityTruthSurface from '../components/CapabilityTruthSurface';
import { ErrorState, LoadingState } from '../components/StateViews';
import './capabilities.css';

export default function CapabilitiesPage() {
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async () => {
    try {
      const data = await getCapabilityCatalogue();
      setPayload(data);
      setError('');
    } catch (e) {
      // Bounded, friendly error: the governed statement is simply not shown
      // while it cannot be produced (CS-3 — show less, never something stronger).
      setError(e.message || 'Unable to load the capability statement.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      if (active) await load();
    })();
    return () => {
      active = false;
    };
  }, [load, retryCount]);

  if (loading) {
    return <LoadingState label="Loading the governed capability statement…" />;
  }

  if (error || !payload) {
    return (
      <ErrorState
        title="Capability statement unavailable"
        message={error || 'Unable to load the capability statement.'}
        onRetry={() => {
          setLoading(true);
          setRetryCount((count) => count + 1);
        }}
      />
    );
  }

  return (
    <div>
      <CapabilityTruthSurface payload={payload} audience="customer" />
      <p className="ct-capability__where">
        Reviewing the product rather than your own data? The same governed statement is presented
        for a product/due-diligence read at <a href="/capabilities/product">Product capability</a>.
      </p>
    </div>
  );
}
