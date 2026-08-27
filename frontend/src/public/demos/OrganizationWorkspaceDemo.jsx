// frontend/src/public/demos/OrganizationWorkspaceDemo.jsx
// A realistic Customer Organisation workspace demonstration. The visitor can
// select a demo organisation, open a Processing Work item and walk it through
// document -> extracted data -> emission factor -> calculation -> evidence ->
// result. Everything is local, deterministic, fabricated data.
import React, { useEffect, useRef, useState } from 'react';
import { DemoFrame, useCountUp, usePrefersReducedMotion } from './demoCore';
import { WORKSPACES, WORKFLOW_STEPS } from './demoData';
import './workspace-demos.css';

const STEP_IDS = WORKFLOW_STEPS.map((s) => s.id);

function Stat({ label, value, active, sub }) {
  const v = useCountUp(value, { active, duration: 1100, decimals: 0 });
  return (
    <div className="ws-stat">
      <span className="ws-stat-label">{label}</span>
      <span className="ws-stat-value">{Math.round(v).toLocaleString('en-GB')}</span>
      {sub ? <span className="ws-stat-sub">{sub}</span> : null}
    </div>
  );
}

function ScopeRow({ scope, active, index }) {
  const v = useCountUp(scope.value, { active, duration: 900 + index * 120, decimals: 1 });
  const max = 80; // fixed scale so all demo orgs render comparable bars
  return (
    <div className="ws-scope">
      <div className="ws-scope-head">
        <span className="ws-scope-name">{scope.name}</span>
        <span className="ws-scope-value">{v.toFixed(1)} <small>t CO₂e</small></span>
      </div>
      <div className="ws-track">
        <span className="ws-fill" style={{ width: active ? `${Math.min((v / max) * 100, 100)}%` : '0%' }} />
      </div>
      <span className="ws-scope-note">{scope.note}</span>
    </div>
  );
}

function PipelineRail({ org, active }) {
  const max = Math.max(1, ...org.pipeline.map((p) => p.count));
  return (
    <ol className="ws-pipeline" aria-label="Processing pipeline">
      {org.pipeline.map((p, i) => (
        <li key={p.stage} className={p.count > 0 ? 'has' : ''} style={{ '--i': i }}>
          <div className="ws-pipeline-bar">
            <span className="ws-pipeline-fill" style={{ height: active ? `${(p.count / max) * 100}%` : '6%' }} />
          </div>
          <span className="ws-pipeline-count">{p.count}</span>
          <span className="ws-pipeline-stage">{p.stage}</span>
        </li>
      ))}
    </ol>
  );
}

function EvidenceChain({ item }) {
  const chain = [
    { title: 'Source document', detail: `${item.doc.supplier} — ${item.doc.ref}, page ${item.doc.page} (${item.doc.format})` },
    { title: 'Extracted line', detail: `${item.extracted.line.qty} ${item.extracted.line.unit} — ${item.extracted.line.activity}` },
    { title: 'Emission factor', detail: `${item.factor.provider} ${item.factor.year} — ${item.factor.name} — ${item.factor.rate} kg CO₂e / ${item.factor.unit}` },
    { title: 'Calculation', detail: `${item.calc} — snapshot ${item.result.snapshot}` },
    { title: 'Emission result', detail: `${item.result.kg.toLocaleString('en-GB')} kg CO₂e (≈ ${item.result.tonnes} t CO₂e)` },
  ];
  return (
    <ol className="ws-evidence" aria-label="Evidence chain">
      {chain.map((c, i) => (
        <li key={c.title} style={{ '--i': i }}>
          <span className="ws-evidence-dot" aria-hidden="true">{i + 1}</span>
          <span className="ws-evidence-body">
            <strong>{c.title}</strong>
            <span>{c.detail}</span>
          </span>
        </li>
      ))}
    </ol>
  );
}

function WorkflowStep({ item, stepId }) {
  if (stepId === 'document') {
    return (
      <div className="ws-doc-card" aria-live="polite">
        <div className="ws-doc-head">
          <span className="ws-kicker">Source document</span>
          <span className="ws-badge ws-badge-neutral">{item.doc.format}</span>
        </div>
        <h4>{item.doc.supplier}</h4>
        <dl className="ws-dl">
          <div><dt>Reference</dt><dd>{item.doc.ref}</dd></div>
          <div><dt>Date</dt><dd>{item.doc.date}</dd></div>
          <div><dt>Site</dt><dd>{item.doc.site}</dd></div>
          <div><dt>Page</dt><dd>{item.doc.page}</dd></div>
        </dl>
        <p className="ws-muted-note">Stored in private, organisation-scoped storage. Accessed through a short-lived signed URL only.</p>
      </div>
    );
  }
  if (stepId === 'extracted') {
    return (
      <div aria-live="polite">
        <div className="ws-doc-head">
          <span className="ws-kicker">Extracted activity data</span>
          <span className="ws-badge ws-badge-ok">Extracted · reviewed</span>
        </div>
        <table className="ws-table">
          <thead>
            <tr><th>Field</th><th>Value</th><th>Confidence</th></tr>
          </thead>
          <tbody>
            {item.extracted.fields.map((f) => (
              <tr key={f.label}>
                <td>{f.label}</td>
                <td>{f.value}</td>
                <td>{Math.round(f.confidence * 100)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="ws-muted-note">Every field is reviewed by a specialist before it moves on.</p>
      </div>
    );
  }
  if (stepId === 'factor') {
    return (
      <div aria-live="polite">
        <div className="ws-doc-head">
          <span className="ws-kicker">Emission factor</span>
          <span className="ws-badge ws-badge-ok">Selected &amp; retained</span>
        </div>
        <div className="ws-factor-card">
          <h4>{item.factor.name}</h4>
          <dl className="ws-dl">
            <div><dt>Provider</dt><dd>{item.factor.provider}</dd></div>
            <div><dt>Year</dt><dd>{item.factor.year}</dd></div>
            <div><dt>Rate</dt><dd>{item.factor.rate} kg CO₂e / {item.factor.unit}</dd></div>
          </dl>
        </div>
        <p className="ws-muted-note">
          Matched by activity and unit. Every candidate factor and its score stays on
          the record, so the choice can be explained later.
        </p>
      </div>
    );
  }
  if (stepId === 'calculation') {
    return (
      <div className="ws-calc" aria-live="polite">
        <div className="ws-doc-head">
          <span className="ws-kicker">Calculation</span>
          <span className="ws-badge ws-badge-neutral">Snapshot {item.result.snapshot}</span>
        </div>
        <p className="ws-formula">{item.calc} <span>→</span> <strong>{item.result.kg.toLocaleString('en-GB')} kg CO₂e</strong></p>
        <p className="ws-muted-note">
          The calculation is snapshotted with the factor, the extracted line and the
          source document reference, so the number can be reproduced exactly.
        </p>
      </div>
    );
  }
  if (stepId === 'evidence') {
    return (
      <div aria-live="polite">
        <div className="ws-doc-head">
          <span className="ws-kicker">Evidence &amp; traceability</span>
          <span className="ws-badge ws-badge-ok">Full trace</span>
        </div>
        <EvidenceChain item={item} />
        <p className="ws-muted-note">
          Every emission result traces to its source document, extracted line, factor
          and calculation snapshot. Nothing is a single unexplained number.
        </p>
      </div>
    );
  }
  // result
  return (
    <div className="ws-result" aria-live="polite">
      <div className="ws-doc-head">
        <span className="ws-kicker">Final result</span>
        <span className="ws-badge ws-badge-ok">Customer review · ready to approve</span>
      </div>
      <div className="ws-result-number">
        {item.result.kg.toLocaleString('en-GB')}
        <span>kg CO₂e</span>
      </div>
      <p className="ws-result-sub">≈ {item.result.tonnes} t CO₂e · {item.extracted.line.qty} {item.extracted.line.unit} {item.extracted.line.activity}</p>
      <div className="ws-result-actions">
        <span className="ws-muted-note">Demo controls</span>
        <div className="ws-btn-row">
          <button type="button" className="ws-btn" disabled>Export CSV</button>
          <button type="button" className="ws-btn" disabled>Open evidence</button>
        </div>
      </div>
    </div>
  );
}

export default function OrganizationWorkspaceDemo() {
  const reduced = usePrefersReducedMotion();
  const [orgId, setOrgId] = useState('aurora');
  const [view, setView] = useState('dashboard'); // 'dashboard' | 'organisation' | 'work'
  const [itemId, setItemId] = useState(null);
  const [step, setStep] = useState(0);
  const [guided, setGuided] = useState(false);
  const panelRef = useRef(null);

  const org = WORKSPACES.find((w) => w.id === orgId);
  const item = org.workItems.find((i) => i.id === itemId);

  const openWork = (id) => {
    setItemId(id);
    setStep(0);
    setView('work');
    setGuided(false);
  };

  const backToDashboard = () => {
    setView('dashboard');
    setGuided(false);
  };

  const selectOrg = (id) => {
    setOrgId(id);
    setView('dashboard');
    setGuided(false);
  };

  const goTab = (tab) => {
    setView(tab);
    setGuided(false);
  };

  const goStep = (next) => {
    setStep(Math.max(0, Math.min(STEP_IDS.length - 1, next)));
  };

  // Guided tour: open the org's first work item and advance through the steps.
  useEffect(() => {
    if (!guided) return undefined;
    const target = org.workItems[0];
    if (view !== 'work' || itemId !== target.id) {
      setItemId(target.id);
      setView('work');
      setStep(0);
      return undefined;
    }
    if (reduced) {
      setStep(STEP_IDS.length - 1);
      setGuided(false);
      return undefined;
    }
    if (step >= STEP_IDS.length - 1) {
      setGuided(false);
      return undefined;
    }
    const t = setTimeout(() => setStep((s) => s + 1), 1500);
    return () => clearTimeout(t);
  }, [guided, view, itemId, step, org, reduced]);

  // Focus the step panel heading when the view or step changes (keyboard use).
  useEffect(() => {
    if (view === 'work' && panelRef.current) panelRef.current.focus();
  }, [view, step]);

  return (
    <DemoFrame
      className="ws-frame"
      title="Customer Organisation workspace — full interactive demo"
      note="Product demonstration — sample organisation and data."
    >
      <div className="ws-app">
        {/* Workspace header */}
        <div className="ws-header">
          <div className="ws-header-id">
            <span className="ws-app-name">CarbonTally</span>
            <span className="ws-header-divider" aria-hidden="true">/</span>
            <strong className="ws-org-name">{org.name}</strong>
            <span className="ws-badge ws-badge-demo">DEMO</span>
          </div>
          <div className="ws-org-switch" role="group" aria-label="Choose a demo organisation">
            {WORKSPACES.map((w) => (
              <button
                key={w.id}
                type="button"
                className={w.id === orgId ? 'is-active' : ''}
                aria-pressed={w.id === orgId}
                onClick={() => selectOrg(w.id)}
              >
                {w.name}
              </button>
            ))}
          </div>
        </div>

        {view !== 'work' ? (
          <div className="ws-tabs" role="tablist" aria-label="Organisation workspace sections">
            <button
              type="button"
              role="tab"
              aria-selected={view === 'dashboard'}
              className={view === 'dashboard' ? 'is-active' : ''}
              onClick={() => goTab('dashboard')}
            >
              Dashboard
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={view === 'organisation'}
              className={view === 'organisation' ? 'is-active' : ''}
              onClick={() => goTab('organisation')}
            >
              Organisation
            </button>
          </div>
        ) : null}

        {view === 'dashboard' && <DashboardBody org={org} onOpenWork={openWork} />}
        {view === 'organisation' && <OrganisationBody org={org} onBack={backToDashboard} />}
        {view === 'work' && (
          <WorkBody
            org={org}
            item={item}
            step={step}
            guided={guided}
            onToggleGuided={() => setGuided((g) => !g)}
            onGoStep={goStep}
            onBack={backToDashboard}
            onSwitchItem={setItemId}
            panelRef={panelRef}
          />
        )}
      </div>

      <div className="ct-demo-controls">
        <button type="button" className="ct-btn ct-btn-primary" onClick={() => openWork(org.workItems[0].id)}>
          Open Processing Work
        </button>
        <span className="ct-demo-hint">Open a work item on the dashboard, or start here.</span>
      </div>
    </DemoFrame>
  );
}

function DashboardBody({ org, onOpenWork }) {
  const active = true;
  return (
    <div className="ws-dash">
      <div className="ws-stats">
        <Stat label="Records processed" value={org.records} active={active} sub={org.period} />
        <Stat label="Verified & approved" value={org.verified} active={active} />
        <Stat label="Flagged for review" value={org.flagged} active={active} />
        <Stat label="In customer review" value={org.inReview} active={active} />
      </div>

      <div className="ws-grid ws-grid-2">
        <section className="ws-panel" aria-labelledby="ws-emissions">
          <div className="ws-panel-head">
            <h3 id="ws-emissions">Emissions summary</h3>
            <span className="ws-panel-sub">{org.period}</span>
          </div>
          <div className="ws-scopes">
            {org.scopes.map((s, i) => (
              <ScopeRow key={s.name} scope={s} active={active} index={i} />
            ))}
          </div>
          <div className="ws-total">
            Total <strong>{org.total.toFixed(1)} t CO₂e</strong>
          </div>
        </section>

        <section className="ws-panel" aria-labelledby="ws-processing">
          <div className="ws-panel-head">
            <h3 id="ws-processing">Processing status</h3>
            <span className="ws-panel-sub">Across all Processing Work</span>
          </div>
          <PipelineRail org={org} active={active} />
          <p className="ws-muted-note">
            Records move through extraction → mapping → validation → customer review →
            approval. Every step is tracked, and every change is audited.
          </p>
        </section>

        <section className="ws-panel" aria-labelledby="ws-documents">
          <div className="ws-panel-head">
            <h3 id="ws-documents">Documents</h3>
            <span className="ws-panel-sub">Private org-scoped storage</span>
          </div>
          <ul className="ws-list">
            {org.documents.map((d) => (
              <li key={d.name} className="ws-list-item">
                <span className="ws-list-main">{d.name}</span>
                <span className="ws-list-meta">{d.type} · {d.pages} page{d.pages > 1 ? 's' : ''}</span>
                <span className="ws-badge ws-badge-neutral">{d.status}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="ws-panel" aria-labelledby="ws-factors">
          <div className="ws-panel-head">
            <h3 id="ws-factors">Emission factors</h3>
            <span className="ws-panel-sub">Approved factor sets</span>
          </div>
          <ul className="ws-list">
            {org.factors.map((f) => (
              <li key={f.name} className="ws-list-item">
                <span className="ws-list-main">{f.name}</span>
                <span className="ws-list-meta">{f.note}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="ws-panel ws-panel-work" aria-labelledby="ws-work">
        <div className="ws-panel-head">
          <h3 id="ws-work">Processing Work</h3>
          <span className="ws-panel-sub">Select an item to walk it through the pipeline</span>
        </div>
        <ul className="ws-work-list">
          {org.workItems.map((wi) => (
            <li key={wi.id}>
              <button type="button" className="ws-work-row" onClick={() => onOpenWork(wi.id)}>
                <span className="ws-work-batch">{wi.batch}</span>
                <span className="ws-work-title">{wi.title}</span>
                <span className="ws-work-meta">{wi.items} items · {wi.assigned}</span>
                <span className={`ws-badge ws-badge-${wi.status === 'approved' ? 'ok' : 'warn'}`}>{wi.status.replace('_', ' ')}</span>
                <span className="ws-work-open" aria-hidden="true">Open →</span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <div className="ws-grid ws-grid-3">
        <section className="ws-panel" aria-labelledby="ws-review">
          <div className="ws-panel-head">
            <h3 id="ws-review">Validation &amp; review</h3>
          </div>
          <ul className="ws-list">
            {org.workItems[0].findings.map((f) => (
              <li key={f.title} className="ws-list-item">
                <span className="ws-list-main">{f.title}</span>
                <span className="ws-list-meta">{f.detail}</span>
              </li>
            ))}
          </ul>
          <p className="ws-muted-note">Findings are surfaced to reviewers and resolved before approval.</p>
        </section>

        <section className="ws-panel" aria-labelledby="ws-reports">
          <div className="ws-panel-head">
            <h3 id="ws-reports">Reports</h3>
          </div>
          <ul className="ws-list">
            {org.reports.map((r) => (
              <li key={r.name} className="ws-list-item">
                <span className="ws-list-main">{r.name}</span>
                <span className="ws-list-meta">{r.status} · {r.date}</span>
              </li>
            ))}
          </ul>
          <p className="ws-muted-note">Versioned, evidence-backed reports with branded PDF export.</p>
        </section>

        <section className="ws-panel" aria-labelledby="ws-team">
          <div className="ws-panel-head">
            <h3 id="ws-team">Team members</h3>
          </div>
          <ul className="ws-list">
            {org.team.map((m) => (
              <li key={m.email} className="ws-list-item">
                <span className="ws-list-main">{m.name}</span>
                <span className="ws-list-meta">{m.role}</span>
              </li>
            ))}
          </ul>
          <p className="ws-muted-note">Role-based access — owner, admin, member and viewer.</p>
        </section>
      </div>
    </div>
  );
}

function MasterDataSection({ title, sub, items, render }) {
  return (
    <section className="ws-panel" aria-labelledby={`ws-md-${title}`}>
      <div className="ws-panel-head">
        <h4 id={`ws-md-${title}`}>{title}</h4>
        {sub ? <span className="ws-panel-sub">{sub}</span> : null}
      </div>
      <ul className="ws-list">
        {items.map((item) => (
          <li key={`${title}-${item.name}`} className="ws-list-item">
            {render(item)}
          </li>
        ))}
      </ul>
    </section>
  );
}

function OrganisationBody({ org, onBack }) {
  const md = org.masterData || { facilities: [], assets: [], suppliers: [], customFactors: [] };
  const statusTone = (status) => {
    if (status === 'active' || status === 'verified') return 'ok';
    if (status === 'draft' || status === 'pending' || status === 'remediation') return 'warn';
    return 'neutral';
  };
  return (
    <div className="ws-dash">
      <div className="ws-client-top">
        <button type="button" className="ws-link-btn" onClick={onBack}>← Back to {org.name} dashboard</button>
      </div>
      <div className="ws-client-head">
        <div>
          <h3 className="ws-client-h3">Organisation</h3>
          <p className="ws-client-tag">Master data, custom factors and team — all scoped to {org.name}</p>
        </div>
        <span className="ws-badge ws-badge-neutral">Org-scoped · owner/admin manage</span>
      </div>

      <div className="ws-grid ws-grid-2">
        <MasterDataSection
          title="Facilities"
          sub="Sites that generate activity (facilities/locations)"
          items={md.facilities}
          render={(f) => (
            <>
              <span className="ws-list-main">{f.name}</span>
              <span className="ws-list-meta">{f.type}</span>
              <span className={`ws-badge ws-badge-${statusTone(f.status)}`}>{f.status}</span>
            </>
          )}
        />
        <MasterDataSection
          title="Assets"
          sub="Equipment and fleets attached to facilities"
          items={md.assets}
          render={(a) => (
            <>
              <span className="ws-list-main">{a.name}</span>
              <span className="ws-list-meta">{a.type} · {a.facility}</span>
            </>
          )}
        />
        <MasterDataSection
          title="Suppliers"
          sub="Used as mapping candidates during extraction"
          items={md.suppliers}
          render={(s) => (
            <>
              <span className="ws-list-main">{s.name}</span>
              <span className="ws-list-meta">{s.category}</span>
              <span className={`ws-badge ws-badge-${statusTone(s.status)}`}>{s.status}</span>
            </>
          )}
        />
        <MasterDataSection
          title="Custom factors"
          sub="Customer-approved factors (D9 lifecycle: draft → review → active)"
          items={md.customFactors}
          render={(f) => (
            <>
              <span className="ws-list-main">{f.name}</span>
              <span className="ws-list-meta">{f.activity}</span>
              <span className={`ws-badge ws-badge-${statusTone(f.status)}`}>{f.status}</span>
            </>
          )}
        />
      </div>

      <div className="ws-grid ws-grid-2">
        <MasterDataSection
          title="Team members"
          sub="Role-based access — owner, admin, member, viewer"
          items={org.team}
          render={(m) => (
            <>
              <span className="ws-list-main">{m.name}</span>
              <span className="ws-list-meta">{m.role}</span>
            </>
          )}
        />
        <section className="ws-panel" aria-labelledby="ws-md-planned">
          <div className="ws-panel-head">
            <h4 id="ws-md-planned">Locations &amp; vehicles</h4>
            <span className="ws-panel-sub">Planned organisation master data</span>
          </div>
          <ul className="ws-list">
            <li className="ws-list-item">
              <span className="ws-list-main">Locations</span>
              <span className="ws-badge ws-badge-neutral">Planned</span>
            </li>
            <li className="ws-list-item">
              <span className="ws-list-main">Vehicles</span>
              <span className="ws-badge ws-badge-neutral">Planned</span>
            </li>
          </ul>
          <p className="ws-muted-note">
            Master data is secondary to processing: nothing is forced before you upload
            and process. Custom factors are approved by an owner/admin and used in
            calculations ahead of standard factors for the same activity.
          </p>
        </section>
      </div>
    </div>
  );
}

function WorkBody({ org, item, step, guided, onToggleGuided, onGoStep, onBack, onSwitchItem, panelRef }) {
  const stepId = STEP_IDS[step];
  const isLast = step >= STEP_IDS.length - 1;
  return (
    <div className="ws-work">
      <div className="ws-work-top">
        <button type="button" className="ws-link-btn" onClick={onBack}>← Back to {org.name} dashboard</button>
        <span className="ws-work-loc">{item.batch} · {item.title}</span>
      </div>

      <ol className="ws-stepper" aria-label="Processing workflow steps">
        {WORKFLOW_STEPS.map((s, i) => (
          <li key={s.id} className={i === step ? 'current' : i < step ? 'done' : ''} aria-current={i === step ? 'step' : undefined}>
            <button type="button" onClick={() => onGoStep(i)} aria-label={`Step ${i + 1}: ${s.label}`}>
              <span className="ws-stepper-dot" aria-hidden="true">{i < step ? '✓' : i + 1}</span>
              <span className="ws-stepper-label">{s.label}</span>
            </button>
          </li>
        ))}
      </ol>

      <div className="ws-work-panel" ref={panelRef} tabIndex={-1}>
        <WorkflowStep item={item} stepId={stepId} />
      </div>

      <div className="ws-work-actions">
        <button type="button" className="ws-btn" disabled={step === 0} onClick={() => onGoStep(step - 1)}>
          ← Back
        </button>
        <button type="button" className="ws-btn ws-btn-primary" disabled={isLast} onClick={() => onGoStep(step + 1)}>
          {isLast ? 'Complete' : 'Next →'}
        </button>
        <button type="button" className={`ws-btn ws-btn-ghost${guided ? ' is-guided' : ''}`} onClick={onToggleGuided} aria-pressed={guided}>
          {guided ? 'Pause guided tour' : 'Guided tour'}
        </button>
      </div>
    </div>
  );
}
