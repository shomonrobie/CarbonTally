// frontend/src/public/demos/ConsultantWorkspaceDemo.jsx
// A realistic Consultant workspace demonstration. The visitor can view the
// consultant firm's clients, open one Customer Organisation, see its
// processing status and evidence, then switch to another organisation.
// Everything is local, deterministic, fabricated data. Client access follows
// the CarbonTally role model: an ACTIVE client grant is the source of access.
import React, { useEffect, useRef, useState } from 'react';
import { DemoFrame, useCountUp } from './demoCore';
import { CONSULTANT, WORKSPACES } from './demoData';
import './workspace-demos.css';

function Stat({ label, value, active, decimals = 0, suffix = '', sub }) {
  const v = useCountUp(value, { active, duration: 1100, decimals });
  return (
    <div className="ws-stat">
      <span className="ws-stat-label">{label}</span>
      <span className="ws-stat-value">{decimals ? v.toFixed(decimals) : Math.round(v).toLocaleString('en-GB')}<small>{suffix}</small></span>
      {sub ? <span className="ws-stat-sub">{sub}</span> : null}
    </div>
  );
}

export default function ConsultantWorkspaceDemo() {
  const [clientId, setClientId] = useState('aurora');
  const [view, setView] = useState('clients'); // 'clients' | 'client'
  const panelRef = useRef(null);

  const client = CONSULTANT.clients.find((c) => c.id === clientId);
  const workspace = WORKSPACES.find((w) => w.id === clientId);

  const selectClient = (id) => {
    setClientId(id);
    setView('client');
  };

  useEffect(() => {
    if (view === 'client' && panelRef.current) panelRef.current.focus();
  }, [view]);

  return (
    <DemoFrame
      className="ws-frame ws-frame-consultant"
      title={`${CONSULTANT.firm} — consultant workspace`}
      note="Product demonstration — sample firm, clients and data."
    >
      <div className="ws-app">
        <div className="ws-header">
          <div className="ws-header-id">
            <span className="ws-app-name">CarbonTally</span>
            <span className="ws-header-divider" aria-hidden="true">/</span>
            <strong className="ws-org-name">Consultant workspace</strong>
            <span className="ws-badge ws-badge-demo">DEMO</span>
          </div>
          <div className="ws-header-meta">
            {CONSULTANT.firm} · {CONSULTANT.partner}
          </div>
        </div>

        {view === 'clients' ? (
          <ClientsBody onSelect={selectClient} activeClient={clientId} />
        ) : (
          <ClientBody
            client={client}
            workspace={workspace}
            onBack={() => setView('clients')}
            onSwitch={selectClient}
            panelRef={panelRef}
          />
        )}
      </div>
    </DemoFrame>
  );
}

function ClientsBody({ onSelect, activeClient }) {
  const active = true;
  const total = CONSULTANT.clients.reduce((sum, c) => sum + c.emissions, 0);
  const outstanding = CONSULTANT.clients.reduce((sum, c) => sum + c.reviews, 0);
  return (
    <div className="ws-dash">
      <div className="ws-stats">
        <Stat label="Client organisations" value={CONSULTANT.clients.length} active={active} />
        <Stat label="Active engagements" value={CONSULTANT.clients.filter((c) => c.status === 'active').length} active={active} />
        <Stat label="Emissions under management" value={total} active={active} decimals={1} suffix=" t CO₂e" />
        <Stat label="Outstanding reviews" value={outstanding} active={active} />
      </div>

      <section className="ws-panel" aria-labelledby="ws-clients">
        <div className="ws-panel-head">
          <h4 id="ws-clients">Client organisations</h4>
          <span className="ws-panel-sub">Select a client to open its workspace</span>
        </div>
        <ul className="ws-client-list">
          {CONSULTANT.clients.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                className={`ws-client-row${c.id === activeClient ? ' is-active' : ''}`}
                onClick={() => onSelect(c.id)}
              >
                <span className="ws-client-name">{c.name}</span>
                <span className={`ws-badge ${c.status === 'active' ? 'ws-badge-ok' : 'ws-badge-warn'}`}>
                  {c.status === 'active' ? 'Active' : 'Suspended'}
                </span>
                <span className="ws-client-progress" aria-label={`Processing progress ${c.progress}%`}>
                  <span className="ws-track"><span className="ws-fill" style={{ width: `${c.progress}%` }} /></span>
                  <span className="ws-client-progress-val">{c.progress}%</span>
                </span>
                <span className="ws-client-meta">{c.emissions.toFixed(1)} t CO₂e · {c.dataQuality}% data quality · {c.reviews} review{c.reviews === 1 ? '' : 's'}</span>
                <span className="ws-work-open" aria-hidden="true">Open →</span>
              </button>
            </li>
          ))}
        </ul>
        <p className="ws-muted-note">
          Access to each client is granted by the client organisation, and is withdrawn
          immediately when an engagement is suspended or ended.
        </p>
      </section>

      <section className="ws-panel" aria-labelledby="ws-consultant-recent">
        <div className="ws-panel-head">
          <h4 id="ws-consultant-recent">Recent Processing Work across clients</h4>
        </div>
        <ul className="ws-list">
          {CONSULTANT.clients.map((c) => (
            <li key={c.id} className="ws-list-item">
              <span className="ws-list-main">{c.name} — {c.recent}</span>
              <span className={`ws-badge ${c.status === 'active' ? 'ws-badge-ok' : 'ws-badge-warn'}`}>
                {c.status === 'active' ? 'In progress' : 'Paused'}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function ClientBody({ client, workspace, onBack, onSwitch, panelRef }) {
  const active = true;
  const max = Math.max(...workspace.pipeline.map((p) => p.count), 1);
  return (
    <div className="ws-dash" ref={panelRef} tabIndex={-1}>
      <div className="ws-client-top">
        <button type="button" className="ws-link-btn" onClick={onBack}>← Back to client list</button>
        <span className="ws-work-loc">
          {client.name} ·{' '}
          <select
            className="ws-select"
            value={client.id}
            onChange={(e) => onSwitch(e.target.value)}
            aria-label="Switch to another organisation"
          >
            {CONSULTANT.clients.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </span>
      </div>

      <div className="ws-client-head">
        <div>
          <h4>{workspace.name}</h4>
          <p className="ws-client-tag">{workspace.tag} · {workspace.period}</p>
        </div>
        <span className={`ws-badge ${client.status === 'active' ? 'ws-badge-ok' : 'ws-badge-warn'}`}>
          Client grant: {client.status}
        </span>
      </div>

      <div className="ws-stats">
        <Stat label="Emissions (period)" value={workspace.total} active={active} decimals={1} suffix=" t CO₂e" />
        <Stat label="Verified & approved" value={workspace.verified} active={active} />
        <Stat label="Flagged for review" value={workspace.flagged} active={active} />
        <Stat label="Data quality" value={client.dataQuality} active={active} suffix="%" />
      </div>

      <div className="ws-grid ws-grid-2">
        <section className="ws-panel" aria-labelledby="ws-c-emissions">
          <div className="ws-panel-head">
            <h4 id="ws-c-emissions">Emissions overview</h4>
          </div>
          <div className="ws-scopes">
            {workspace.scopes.map((s, i) => (
              <div key={s.name} className="ws-scope">
                <div className="ws-scope-head">
                  <span className="ws-scope-name">{s.name}</span>
                  <span className="ws-scope-value">{s.value.toFixed(1)} <small>t CO₂e</small></span>
                </div>
                <div className="ws-track">
                  <span className="ws-fill" style={{ width: `${(s.value / Math.max(...workspace.scopes.map((x) => x.value))) * 100}%` }} />
                </div>
                <span className="ws-scope-note">{s.note}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="ws-panel" aria-labelledby="ws-c-processing">
          <div className="ws-panel-head">
            <h4 id="ws-c-processing">Processing progress</h4>
          </div>
          <ol className="ws-pipeline" aria-label="Processing pipeline">
            {workspace.pipeline.map((p, i) => (
              <li key={p.stage} className={p.count > 0 ? 'has' : ''} style={{ '--i': i }}>
                <div className="ws-pipeline-bar">
                  <span className="ws-pipeline-fill" style={{ height: `${(p.count / max) * 100}%` }} />
                </div>
                <span className="ws-pipeline-count">{p.count}</span>
                <span className="ws-pipeline-stage">{p.stage}</span>
              </li>
            ))}
          </ol>
        </section>
      </div>

      <section className="ws-panel" aria-labelledby="ws-c-work">
        <div className="ws-panel-head">
          <h4 id="ws-c-work">Processing Work</h4>
        </div>
        <ul className="ws-list">
          {workspace.workItems.map((wi) => (
            <li key={wi.id} className="ws-list-item">
              <span className="ws-list-main">{wi.batch} — {wi.title}</span>
              <span className="ws-list-meta">{wi.items} items · {wi.assigned}</span>
              <span className={`ws-badge ${wi.status === 'approved' ? 'ws-badge-ok' : 'ws-badge-warn'}`}>{wi.status.replace('_', ' ')}</span>
            </li>
          ))}
        </ul>
        <p className="ws-muted-note">
          The same evidence workflow shown on the Platform page applies here — every
          client result traces to its source document, factor and calculation snapshot.
        </p>
      </section>
    </div>
  );
}
