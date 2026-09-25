// frontend/src/v3/capabilities/InvestorCapabilityPage.jsx
// P17-L — the INVESTOR / due-diligence capability truth surface
// (CT-PO-P17-DECISION-03 §9, §14.3).
//
// The decisive constraint (`§6.2`, §9.1): the investor surface must not
// overstate the product. It therefore:
//
//  * consumes the SAME canonical projection as the customer surface (`§6`), so
//    a governed value cannot differ between them (`CS-2`, `AG-6`);
//  * makes no tenant-scoped request and resolves no organisation — it does not
//    import the organisation resolver at all, so there is no tenant query path
//    to audit (`CS-1`, `SEC-1`, `SEC-3`, `AG-5`, `§19.4` row 8);
//  * shows no result, no figure, no coverage percentage and no applicability
//    claim — capability and result-presence only (`IN-1`, `§9.4`).
import React, { useCallback, useEffect, useState } from 'react';
import { getCapabilityCatalogue } from '../api';
import CapabilityTruthSurface from '../components/CapabilityTruthSurface';
import { ErrorState, LoadingState } from '../components/StateViews';
import './capabilities.css';

export default function InvestorCapabilityPage() {
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
      // Fail closed: where the statement cannot be produced, the surface shows
      // less and records the gap rather than filling it (CS-3).
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
      <CapabilityTruthSurface payload={payload} audience="investor" />
      <p className="ct-capability__footnote">
        This is a product-level statement. It contains no customer or organisation information,
        and it is generated from the same governed source the product itself renders.
      </p>
    </div>
  );
}
