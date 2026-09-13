// CarbonTally — analytics bootstrap mount.
//
// Runs for every route (public marketing surface and authenticated
// application) because the whole product is one React application. It renders
// nothing: its only job is to decide, once, whether Google Analytics 4 may be
// loaded, and to re-evaluate when the visitor changes their cookie choice.
import { useEffect } from 'react';
import { CONSENT_ACCEPTED, subscribeToConsentChanges } from '../lib/consent';
import { initGa4Analytics } from '../lib/analytics/ga4';

export default function AnalyticsBootstrap() {
  useEffect(() => {
    let active = true;

    initGa4Analytics();

    const unsubscribe = subscribeToConsentChanges((consent) => {
      if (active && consent === CONSENT_ACCEPTED) {
        initGa4Analytics();
      }
    });

    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  return null;
}
