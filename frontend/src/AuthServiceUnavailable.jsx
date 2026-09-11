// frontend/src/AuthServiceUnavailable.jsx
//
// CarbonTally-branded "sign-in temporarily unavailable" notice.
//
// Shown when the authentication service (Supabase Auth) cannot be reached, when
// an OAuth initiation/callback fails for infrastructure reasons, when a session
// cannot be restored, or when the timeout is exceeded.
//
// IMPORTANT: this component is only for AUTH SERVICE UNAVAILABLE. Invalid
// credentials, unsigned-in state, and forbidden/unauthorised responses are
// handled separately and must never be presented as an outage.
//
// It deliberately does NOT display raw Supabase error strings, and it states
// that data has not been lost.
import React from 'react';

export default function AuthServiceUnavailable({ onRetry, context }) {
  const heading = 'CarbonTally sign-in is temporarily unavailable';

  const detailByContext = {
    callback: 'We could not complete your sign-in. This is a temporary problem on our side, not a problem with your account.',
    session: 'We could not restore your existing session. This is a temporary problem on our side, not a problem with your account.',
    oauth: 'We could not start Google sign-in. This is a temporary problem on our side, not a problem with your account.',
  };
  const detail =
    detailByContext[context] ||
    'We could not reach the CarbonTally sign-in service. This is a temporary problem on our side, not a problem with your account.';

  return (
    <div
      role="alert"
      aria-live="polite"
      data-testid="auth-service-unavailable"
      style={{
        maxWidth: 560,
        margin: '48px auto',
        padding: '28px 24px',
        border: '1px solid #d7dee8',
        borderRadius: 12,
        background: '#ffffff',
        boxShadow: '0 6px 24px rgba(15, 40, 70, 0.08)',
        fontFamily: 'inherit',
        color: '#12324f',
        textAlign: 'left',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
        <span aria-hidden="true" style={{ fontSize: 22 }}>🌱</span>
        <strong style={{ fontSize: 18, letterSpacing: 0.2 }}>CarbonTally</strong>
      </div>

      <h1 style={{ fontSize: 20, margin: '0 0 10px' }}>{heading}</h1>

      <p style={{ margin: '0 0 12px', lineHeight: 1.5 }}>{detail}</p>

      <ul style={{ margin: '0 0 16px 18px', padding: 0, lineHeight: 1.6 }}>
        <li>This is a <strong>temporary</strong> service interruption.</li>
        <li>Your account and your organisation&rsquo;s data have <strong>not</strong> been deleted or lost.</li>
        <li>Please wait a moment and try again.</li>
      </ul>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <button
          type="button"
          onClick={onRetry}
          style={{
            padding: '10px 18px',
            borderRadius: 8,
            border: '1px solid #12324f',
            background: '#12324f',
            color: '#ffffff',
            cursor: 'pointer',
            fontSize: 14,
          }}
        >
          Try again
        </button>
        <a href="/privacy" style={{ color: '#12324f', fontSize: 14 }}>Privacy Policy</a>
      </div>

      <p style={{ margin: '16px 0 0', fontSize: 13, color: '#4a6580', lineHeight: 1.5 }}>
        If sign-in remains unavailable, please try again shortly. CarbonTally service status and
        support contact details are published on this site.
      </p>
    </div>
  );
}
