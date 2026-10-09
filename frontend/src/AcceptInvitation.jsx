// frontend/src/AcceptInvitation.jsx
// CT-CONSULTANT-CLIENT-IDENTITY-04 (PD-1A) — the invitee's acceptance journey.
//
// The email link issued by the inviter resolves to
//   /accept-invitation?token=<single-use token>
// and this page turns that link into an organisation membership:
//
//   1. the token is read from the URL (a URL fragment is never used);
//   2. the invitee signs IN or signs UP with the INVITED email (existing
//      Supabase Auth — this page adds no second authentication system and never
//      stores a password);
//   3. the single-use token is exchanged for a membership by the backend
//      (POST /api/v3/organizations/invitations/accept), which enforces the
//      email binding, expiry and single-use rules SERVER-SIDE;
//   4. success redirects into the actor's server-authoritative workspace.
//
// The UI is not a security boundary: nothing here can create a membership the
// backend would refuse. No tenant/org existence information is shown before a
// successful, authenticated acceptance.
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { supabase } from './supabaseClient';
import { acceptInvitation, goToWorkspace } from './v3/api';
import './css/AcceptInvitation.css';

//: The invitee may confirm their email and come back; the token survives a
//: reload via sessionStorage (never localStorage — it is a single-use bearer
//: and must not outlive the browser session).
const TOKEN_KEY = 'ct_pending_invitation_token';

const safeMessageFor = (error) => {
  const status = error?.status;
  if (status === 404) return 'This invitation link is not valid.';
  if (status === 409) {
    return 'This invitation has already been used, or it has been withdrawn.';
  }
  if (status === 410) {
    return 'This invitation has expired. Ask the person who invited you for a new one.';
  }
  if (status === 403) {
    return 'This invitation was sent to a different email address. Please sign in '
      + 'with the email address the invitation was sent to.';
  }
  if (status === 401) return 'Please sign in again to accept your invitation.';
  return "We couldn't accept this invitation just now. Please try again.";
};

const tokenFromLocation = (search) => {
  try {
    return new URLSearchParams(search || '').get('token') || '';
  } catch {
    return '';
  }
};

export default function AcceptInvitation() {
  const navigate = useNavigate();
  const location = useLocation();

  const [token] = useState(() => {
    const fromUrl = tokenFromLocation(location.search);
    if (fromUrl) {
      try { sessionStorage.setItem(TOKEN_KEY, fromUrl); } catch { /* ignore */ }
      return fromUrl;
    }
    try { return sessionStorage.getItem(TOKEN_KEY) || ''; } catch { return ''; }
  });

  // phase: 'invalid' | 'needs-auth' | 'accepting' | 'accepted' | 'failed'
  const [phase, setPhase] = useState(token ? 'needs-auth' : 'invalid');
  const [error, setError] = useState('');
  const acceptedRef = useRef(false);

  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirmEmail, setConfirmEmail] = useState(false);

  const doAccept = useCallback(async () => {
    if (acceptedRef.current) return;
    setPhase('accepting');
    setError('');
    try {
      await acceptInvitation(token);
      acceptedRef.current = true;
      try { sessionStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
      setPhase('accepted');
      // Land on the actor's server-authoritative workspace (client portal).
      await goToWorkspace(navigate);
    } catch (e) {
      setError(safeMessageFor(e));
      setPhase('failed');
    }
  }, [token, navigate]);

  // Resume automatically when a session already exists (invitee signed in
  // earlier) or appears later (e.g. after the Google OAuth round-trip).
  useEffect(() => {
    if (!token) return undefined;
    let active = true;
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (active && session) doAccept();
    }).catch(() => { /* stay on the sign-in form */ });
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        if (session) doAccept();
      }
    );
    return () => { active = false; subscription.unsubscribe(); };
  }, [token, doAccept]);

  const onPasswordAuth = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      if (isSignup) {
        const { data, error: signUpError } = await supabase.auth.signUp({
          email: email.trim(),
          password,
          options: { data: { onboarding: true } },
        });
        if (signUpError) {
          setError(
            signUpError.message && signUpError.message.includes('already registered')
              ? 'This email is already registered — please sign in instead.'
              : 'We could not create your account. Please try again.'
          );
          return;
        }
        // Email confirmation enabled → the invitee confirms, then returns here.
        if (!data?.session) setConfirmEmail(true);
      } else {
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });
        if (signInError) {
          setError('Those sign-in details were not recognised. Please try again.');
        }
      }
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  const onGoogle = async () => {
    setError('');
    try {
      // Return to this page (token preserved in sessionStorage) after OAuth.
      await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: `${window.location.origin}/accept-invitation` },
      });
    } catch {
      setError('Google sign-in is unavailable right now. Please use your email.');
    }
  };

  return (
    <div className="ct-accept-container">
      <div className="ct-accept-card">
        <h1 className="ct-accept-brand">🌱 CarbonTally</h1>

        {phase === 'invalid' && (
          <div className="ct-accept-panel" role="alert">
            <h2>This link is incomplete</h2>
            <p className="ct-accept-muted">
              The invitation link is missing its token. Please open the link from
              your invitation email again.
            </p>
            <Link className="ct-accept-link" to="/login">Go to sign in</Link>
          </div>
        )}

        {(phase === 'needs-auth' || phase === 'failed' || phase === 'accepting') && (
          <div className="ct-accept-panel">
            <h2>You&apos;ve been invited to CarbonTally</h2>
            <p className="ct-accept-muted">
              Sign in — or create your account — using the email address the
              invitation was sent to, then accept your invitation.
            </p>

            {phase === 'accepting' && (
              <div className="ct-accept-status" role="status">
                <span className="ct-accept-spinner" aria-hidden="true" />
                Accepting your invitation…
              </div>
            )}

            {phase === 'failed' && (
              <div className="ct-accept-error" role="alert">{error}</div>
            )}

            {confirmEmail ? (
              <div role="status">
                <p>
                  We sent a confirmation link to <strong>{email.trim()}</strong>.
                  Click it, then you will be returned here to accept your
                  invitation.
                </p>
              </div>
            ) : (
              <>
                <button
                  type="button"
                  className="ct-accept-google"
                  onClick={onGoogle}
                  disabled={busy}
                >
                  Continue with Google
                </button>
                <div className="ct-accept-divider"><span>or</span></div>
                <form onSubmit={onPasswordAuth} className="ct-accept-form">
                  <label htmlFor="ct-accept-email">Email</label>
                  <input
                    id="ct-accept-email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    required
                  />
                  <label htmlFor="ct-accept-password">Password</label>
                  <input
                    id="ct-accept-password"
                    type="password"
                    autoComplete={isSignup ? 'new-password' : 'current-password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    minLength={6}
                    required
                  />
                  {phase !== 'failed' && error && (
                    <div className="ct-accept-error" role="alert">{error}</div>
                  )}
                  <button type="submit" className="ct-accept-submit" disabled={busy}>
                    {busy ? 'Please wait…' : (isSignup ? 'Create account & accept' : 'Sign in & accept')}
                  </button>
                </form>
                <div className="ct-accept-toggle">
                  {isSignup ? (
                    <p>
                      Already have an account?{' '}
                      <button type="button" onClick={() => { setIsSignup(false); setError(''); }}>
                        Sign in
                      </button>
                    </p>
                  ) : (
                    <p>
                      New to CarbonTally?{' '}
                      <button type="button" onClick={() => { setIsSignup(true); setError(''); }}>
                        Create account
                      </button>
                    </p>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {phase === 'accepted' && (
          <div className="ct-accept-panel" role="status">
            <h2>Invitation accepted</h2>
            <p className="ct-accept-muted">
              You now have access to your organisation. Taking you to your
              workspace…
            </p>
          </div>
        )}
      </div>
    </div>
  );
}


