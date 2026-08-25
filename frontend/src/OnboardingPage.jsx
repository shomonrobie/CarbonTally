// frontend/src/OnboardingPage.jsx
// D35 — Self-service customer onboarding.
//
// A brand-new authenticated customer with NO organization chooses whether their
// organization already exists in CarbonTally (D19 existing-data discovery:
// USE ALL / PARTIAL / DISCARD) or whether to create a fresh organization. The
// initial creator becomes OWNER via the server-authoritative
// POST /api/v3/organizations endpoint.
//
// States (each with success / error / retry / guard):
//   details      -> organization details form
//   review       -> candidate organizations found (blocked OR informational)
//   verify       -> email verification code entry
//   decision     -> USE ALL / PARTIAL / DISCARD
//   created      -> organization created (transient success state)
import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from './supabaseClient';
import {
  chooseOnboardingAdoption,
  createOnboardingDiscoveryRequest,
  createOrganization,
  getConsultantProfile,
  getOpsMe,
  onboardingDiscoveryLookup,
  resolveV3Organization,
  verifyOnboardingDiscoveryRequest,
} from './v3/api';
import './v3/v3.css';

const COUNTRIES = ['GB', 'IE', 'DE', 'FR', 'NL', 'US', 'AU', 'CA', 'Other'];

const ELIGIBLE_CATEGORIES = [
  'documents',
  'suppliers',
  'extraction_records',
  'mappings',
  'calculations',
  'reports',
  'report_versions',
  'processing_history',
];

const CATEGORY_LABELS = {
  documents: 'Documents',
  suppliers: 'Suppliers',
  extraction_records: 'Extraction records',
  mappings: 'Mappings',
  calculations: 'Calculations',
  reports: 'Reports',
  report_versions: 'Report versions',
  processing_history: 'Processing history',
};

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [checking, setChecking] = useState(true);
  const [step, setStep] = useState('details');
  const [orgForm, setOrgForm] = useState({
    name: '',
    country: 'GB',
    company_number: '',
  });
  const [candidates, setCandidates] = useState([]);
  const [blocked, setBlocked] = useState(false);
  const [activeRequest, setActiveRequest] = useState(null);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  // Authenticated route guard: a customer with an organization, or a
  // staff/consultant identity, never sees onboarding (server-authoritative).
  // D35: the guard is BOUNDED — the user must never be stuck indefinitely on
  // the checking screen, even if an upstream resolution call is slow.
  useEffect(() => {
    let active = true;
    let fallbackTimer = setTimeout(() => {
      if (active) setChecking(false);
    }, 12000);
    (async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) {
        navigate('/login', { replace: true });
        return;
      }
      try {
        if (await resolveV3Organization()) {
          navigate('/home', { replace: true });
          return;
        }
      } catch (_e) {
        /* no org -> continue */
      }
      try {
        if (await getOpsMe()) {
          navigate('/ops', { replace: true });
          return;
        }
      } catch (_e) {
        /* not staff -> continue */
      }
      try {
        if (await getConsultantProfile()) {
          navigate('/consultant', { replace: true });
          return;
        }
      } catch (_e) {
        /* not consultant -> continue */
      }
      if (active) {
        clearTimeout(fallbackTimer);
        setChecking(false);
      }
    })();
    return () => {
      active = false;
      clearTimeout(fallbackTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const goHome = () => navigate('/home', { replace: true });

  const onSubmitDetails = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setNotice('');
    try {
      const result = await createOrganization({
        name: orgForm.name.trim(),
        country: orgForm.country || 'GB',
        company_number: orgForm.company_number.trim() || undefined,
      });
      // Organization created — creator is OWNER.
      if (result.candidates && result.candidates.length > 0) {
        setCandidates(result.candidates);
        setBlocked(false);
        setNotice(
          'Your organisation is ready, and we found existing organisations that may hold your data. You can review them now or later from the workspace.'
        );
        setStep('review');
        setLoading(false);
        return;
      }
      goHome();
    } catch (err) {
      if (err && err.status === 409) {
        // Duplicate-prevention block: an existing organisation matches strongly
        // (e.g. exact company number). Surface the candidates for the customer
        // to review — adoption is mandatory before creating a duplicate.
        setBlocked(true);
        try {
          const lookup = await onboardingDiscoveryLookup({
            name: orgForm.name.trim(),
            company_number: orgForm.company_number.trim() || undefined,
          });
          setCandidates(lookup.candidates || []);
        } catch (_lookupErr) {
          setCandidates([]);
        }
        setStep('review');
      } else if (err && err.status === 401) {
        navigate('/login', { replace: true });
      } else {
        setError(
          (err && err.raw) || 'We could not create your organisation. Please check the details and try again.'
        );
      }
    } finally {
      setLoading(false);
    }
  };
  const onCreateAnyway = async () => {
    setLoading(true);
    setError('');
    try {
      await createOrganization({
        name: orgForm.name.trim(),
        country: orgForm.country || 'GB',
        company_number: orgForm.company_number.trim() || undefined,
        acknowledged_candidates: candidates.map((c) => c.organization_id),
      });
      goHome();
    } catch (err) {
      setError(
        (err && err.raw) || 'We could not create your organisation. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const onRequestAccess = async (candidate) => {
    setLoading(true);
    setError('');
    try {
      const result = await createOnboardingDiscoveryRequest(candidate.organization_id);
      setActiveRequest(result.request);
      setNotice(
        `A verification code has been sent to the registered contact for “${candidate.name}”.`
      );
      setStep('verify');
    } catch (err) {
      setError((err && err.raw) || 'We could not start the request. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const onVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await verifyOnboardingDiscoveryRequest(activeRequest.id, code.trim());
      setStep('decision');
    } catch (err) {
      setError(
        (err && err.raw) || 'The verification code was not accepted. Please check it and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const onChoose = async (choice, scope = {}) => {
    setLoading(true);
    setError('');
    try {
      await chooseOnboardingAdoption(activeRequest.id, choice, scope);
      if (choice === 'discard' && blocked) {
        // DISCARD never deletes existing data; in the blocked (pre-org) case
        // the customer then creates a fresh organisation, explicitly
        // acknowledging the candidates they reviewed and decided not to adopt.
        await createOrganization({
          name: orgForm.name.trim(),
          country: orgForm.country || 'GB',
          company_number: orgForm.company_number.trim() || undefined,
          acknowledged_candidates: candidates.map((c) => c.organization_id),
        });
      }
      goHome();
    } catch (err) {
      setError(
        (err && err.raw) || 'We could not apply your choice. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const onToggleCategory = (category) => {
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    );
  };

  const resetAll = () => {
    setStep('details');
    setError('');
    setNotice('');
    setBlocked(false);
    setCandidates([]);
    setActiveRequest(null);
    setSelectedCategories([]);
    setCode('');
  };

  if (checking) {
    return (
      <div className="v3-shell">
        <div className="v3-onboarding">
          <div className="v3-card v3-card-padded" style={{ textAlign: 'center' }}>
            <div className="v3-spinner" aria-label="Loading" />
            <p>Checking your account…</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="v3-shell">
      <header className="v3-nav">
        <div className="v3-nav-brand">
          <span className="v3-nav-logo">CarbonTally</span>
          <span className="v3-nav-tag">V3</span>
        </div>
        <nav className="v3-nav-links" aria-label="Onboarding">
          <span className="v3-nav-link" style={{ cursor: 'default', opacity: 0.7 }}>
            Set up your organisation
          </span>
        </nav>
        <div className="v3-nav-context">
          <button className="v3-nav-logout" onClick={async () => { await supabase.auth.signOut(); navigate('/login', { replace: true }); }} type="button">
            Sign out
          </button>
        </div>
      </header>

      <main className="v3-shell-main">
        <div className="v3-onboarding">
          <div className="v3-card v3-card-padded">
            <h1 className="v3-onboarding-title">Welcome to CarbonTally</h1>
            <p className="v3-onboarding-sub">
              Set up your organisation to start measuring, verifying and reporting
              your carbon emissions.
            </p>

            {step === 'details' && (
              <form onSubmit={onSubmitDetails} className="v3-form">
                {notice && <div className="v3-notice">{notice}</div>}
                {error && (
                  <div className="v3-error">
                    {error}
                    <button type="button" className="v3-link-btn" onClick={resetAll}>
                      Start over
                    </button>
                  </div>
                )}
                <div className="form-group">
                  <label>Organisation name *</label>
                  <input
                    type="text"
                    value={orgForm.name}
                    onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })}
                    placeholder="e.g. ABC Logistics Ltd"
                    required
                    maxLength={200}
                  />
                </div>
                <div className="form-group">
                  <label>Country</label>
                  <select
                    value={orgForm.country}
                    onChange={(e) => setOrgForm({ ...orgForm, country: e.target.value })}
                  >
                    {COUNTRIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Company registration number (optional)</label>
                  <input
                    type="text"
                    value={orgForm.company_number}
                    onChange={(e) =>
                      setOrgForm({ ...orgForm, company_number: e.target.value })
                    }
                    placeholder="e.g. IE123456 — helps us check for existing data"
                    maxLength={100}
                  />
                </div>

                <p className="v3-onboarding-hint">
                  We check whether your organisation may already exist in CarbonTally
                  before creating a new one. You remain in control: you can adopt
                  existing data or start fresh.
                </p>

                <button type="submit" className="btn-primary btn-gradient" disabled={loading}>
                  {loading ? 'Checking…' : 'Continue →'}
                </button>
              </form>
            )}

            {step === 'review' && (
              <div>
                {blocked ? (
                  <div className="v3-error v3-notice-block">
                    An existing organisation matching your details was found. Existing
                    data is never shown or merged without your verification and explicit
                    choice.
                  </div>
                ) : (
                  <div className="v3-notice">{notice}</div>
                )}
                {error && <div className="v3-error">{error}</div>}
                <h2 className="v3-onboarding-step">
                  {blocked ? 'Existing organisations found' : 'Existing organisations may be yours'}
                </h2>
                <p className="v3-onboarding-hint">
                  These are candidate matches only. You can request access to your
                  organisation&apos;s existing data (you&apos;ll verify via its registered
                  contact), or start with a new organisation.
                </p>

                {candidates.length === 0 && (
                  <p className="v3-onboarding-hint">
                    No candidates could be loaded. You can still continue below.
                  </p>
                )}

                <div className="v3-candidate-list">
                  {candidates.map((candidate) => (
                    <div key={candidate.organization_id} className="v3-candidate-card">
                      <div className="v3-candidate-name">{candidate.name}</div>
                      <div className="v3-candidate-meta">
                        {candidate.country && <span>{candidate.country}</span>}
                        {candidate.company_number && <span>{candidate.company_number}</span>}
                      </div>
                      <div className="v3-candidate-counts">
                        {Object.entries(candidate.data_summary || {})
                          .filter(([, count]) => count > 0)
                          .map(([key, count]) => (
                            <span key={key} className="v3-candidate-count">
                              {count} {CATEGORY_LABELS[key] || key}
                            </span>
                          ))}
                      </div>
                      {blocked ? (
                        <button
                          type="button"
                          className="btn-primary"
                          disabled={loading}
                          onClick={() => onRequestAccess(candidate)}
                        >
                          Request access to this data
                        </button>
                      ) : (
                        <p className="v3-onboarding-hint" style={{ margin: 0 }}>
                          You can review and adopt this organisation&apos;s data from the
                          workspace (Existing data).
                        </p>
                      )}
                    </div>
                  ))}
                </div>

                <div className="v3-onboarding-actions">
                  {blocked ? (
                    <button
                      type="button"
                      className="btn-secondary"
                      disabled={loading}
                      onClick={onCreateAnyway}
                    >
                      I&apos;ve reviewed these — create a new organisation anyway
                    </button>
                  ) : (
                    <button type="button" className="btn-secondary" disabled={loading} onClick={goHome}>
                      Continue to my workspace
                    </button>
                  )}
                  <button type="button" className="v3-link-btn" onClick={resetAll} disabled={loading}>
                    Back
                  </button>
                </div>
              </div>
            )}

            {step === 'verify' && (
              <form onSubmit={onVerify} className="v3-form">
                {notice && <div className="v3-notice">{notice}</div>}
                {error && <div className="v3-error">{error}</div>}
                <h2 className="v3-onboarding-step">Verify access to existing data</h2>
                <p className="v3-onboarding-hint">
                  A verification code was sent to the registered contact email of the
                  existing organisation. Enter it below to confirm you are authorised to
                  access its data. The code expires after 15 minutes.
                </p>
                <div className="form-group">
                  <label>Verification code</label>
                  <input
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    placeholder="Enter the code from the email"
                    required
                    minLength={8}
                    maxLength={16}
                    autoFocus
                  />
                </div>
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Verifying…' : 'Verify'}
                </button>
                <div className="v3-onboarding-actions">
                  <button type="button" className="v3-link-btn" onClick={resetAll} disabled={loading}>
                    Start over
                  </button>
                </div>
              </form>
            )}

            {step === 'decision' && (
              <div>
                {error && <div className="v3-error">{error}</div>}
                <h2 className="v3-onboarding-step">How would you like to proceed?</h2>
                <p className="v3-onboarding-hint">
                  You have verified access to existing organisational data. You are the
                  ultimate owner of your data — choose how to use it.
                </p>

                <div className="v3-decision-list">
                  <div className="v3-decision-card">
                    <h3>Use all existing data</h3>
                    <p>
                      Your organisation and its existing documents, extractions,
                      calculations and reports are kept in place — nothing is copied or
                      deleted. You become the Owner of the existing organisation.
                    </p>
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={loading}
                      onClick={() => onChoose('use_all')}
                    >
                      Use all existing data
                    </button>
                  </div>

                  <div className="v3-decision-card">
                    <h3>Select specific data</h3>
                    <p>Choose which categories of existing data to keep.</p>
                    <div className="v3-category-checks">
                      {ELIGIBLE_CATEGORIES.map((category) => (
                        <label key={category} className="v3-check">
                          <input
                            type="checkbox"
                            checked={selectedCategories.includes(category)}
                            onChange={() => onToggleCategory(category)}
                          />
                          {CATEGORY_LABELS[category]}
                        </label>
                      ))}
                    </div>
                    <button
                      type="button"
                      className="btn-secondary"
                      disabled={loading || selectedCategories.length === 0}
                      onClick={() =>
                        onChoose('partial', { categories: selectedCategories })
                      }
                    >
                      Use selected categories
                    </button>
                  </div>

                  <div className="v3-decision-card">
                    <h3>Start fresh</h3>
                    <p>
                      Do not use the existing data. The existing organisation&apos;s data is
                      never deleted — your choice is recorded and you create a new
                      organisation.
                    </p>
                    <button
                      type="button"
                      className="btn-secondary"
                      disabled={loading}
                      onClick={() => onChoose('discard')}
                    >
                      Start fresh — don&apos;t use existing data
                    </button>
                  </div>
                </div>
              </div>
            )}

            <p className="v3-onboarding-help">
              Have an access code? <Link to="/beta/signup">Use your beta access code</Link>
            </p>
          </div>
        </div>
      </main>
      <footer className="v3-shell-footer">
        © {new Date().getFullYear()} CarbonTally (UK) Ltd. All rights reserved.
      </footer>
    </div>
  );
}

