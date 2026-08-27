// frontend/src/v3/components/workbench/WorkbenchShell.jsx
// D19 — the processing-workbench shell: TOP WORKFLOW NAVIGATION + adjustable
// split panes with the approved presets (40/60 · 50/50 · 60/40) + secure
// view-only source pane + status / lock / autosave indicators + action area.
//
// No permanent left sidebar inside the workbench (D19). On tablet/mobile the
// panes become a tray flow: a Source/Data toggle switches the visible pane
// instead of squeezing the desktop split view (D20).
//
// `sourceUrl` is expected to be a backend-signed, role-scoped URL. The PE
// no-download boundary is enforced server-side; `allowDownload` only controls
// whether a download affordance is rendered.
import React, { useState } from 'react';
import { StatusBadge, Icon } from '../ui';
import WorkflowNav, { DEFAULT_STAGES } from './WorkflowNav';
import SplitPane, { PRESETS, presetToRatio } from './SplitPane';
import SecureDocumentViewer from './SecureDocumentViewer';
import AutosaveIndicator from './AutosaveIndicator';
import './workbench.css';

export default function WorkbenchShell({
  stages = DEFAULT_STAGES,
  currentStage,
  onStageChange,
  preset = '50-50',
  onPresetChange,
  sourceUrl,
  sourceTitle,
  allowDownload = false,
  sourceContent,
  data,
  dataLabel = 'Structured data',
  status,
  locked = false,
  autosaveState,
  autosaveAt,
  actions,
  header,
}) {
  const [tray, setTray] = useState('source');

  const sourcePane = sourceContent || (
    <SecureDocumentViewer src={sourceUrl} title={sourceTitle} allowDownload={allowDownload} />
  );

  return (
    <div className="ct-wb">
      <div className="ct-wb-nav">
        <WorkflowNav stages={stages} current={currentStage} onStep={onStageChange} />
        <div className="ct-wb-presets" role="group" aria-label="Pane split presets">
          <span className="ct-wb-preset-label">Panels</span>
          {PRESETS.map((p) => (
            <button
              key={p}
              type="button"
              className="ct-wb-preset"
              aria-pressed={preset === p}
              onClick={() => onPresetChange && onPresetChange(p)}
              title={`${presetToRatio(p)} split`}
            >
              {presetToRatio(p)}
            </button>
          ))}
        </div>
        <div className="ct-wb-meta">
          {status && <StatusBadge status={status} />}
          {locked && (
            <span className="ct-wb-lock ct-wb-lock--locked">
              <Icon name="lock" size={12} aria-hidden="true" />
              Locked
            </span>
          )}
          {autosaveState && <AutosaveIndicator state={autosaveState} lastSavedAt={autosaveAt} />}
        </div>
      </div>

      {header}

      <div className={`ct-wb-panes-wrap ct-wb-tray--${tray}`}>
        <div className="ct-wb-tray-toggle-row">
          <button
            type="button"
            className="ct-wb-tray-toggle"
            aria-pressed={tray === 'source'}
            onClick={() => setTray('source')}
          >
            <Icon name="documents" size={14} aria-hidden="true" /> Source
          </button>
          <button
            type="button"
            className="ct-wb-tray-toggle"
            aria-pressed={tray === 'data'}
            onClick={() => setTray('data')}
          >
            <Icon name="grid" size={14} aria-hidden="true" /> {dataLabel}
          </button>
        </div>

        <SplitPane
          preset={preset}
          left={sourcePane}
          right={<div className="ct-wb-pane-data">{data}</div>}
          leftLabel="Source document"
          rightLabel={dataLabel}
        />
      </div>

      {actions && <div className="ct-wb-actions">{actions}</div>}
    </div>
  );
}
