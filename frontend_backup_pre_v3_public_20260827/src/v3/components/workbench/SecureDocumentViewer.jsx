// frontend/src/v3/components/workbench/SecureDocumentViewer.jsx
// D19/D32 — secure, view-only source document container. Renders a signed URL
// inside a sandboxed iframe. The PE no-download boundary is preserved: when
// `allowDownload` is false the control bar shows an explicit "View only — no
// download" affordance and no download control is rendered.
//
// NOTE: the security boundary is server-side (signed URLs + RLS). This
// component never fabricates a security guarantee — it is UX presentation of
// the backend-enforced boundary.
import React, { useState } from 'react';
import Icon from '../ui/Icon';
import { Button } from '../ui';

export default function SecureDocumentViewer({ src, title, allowDownload = false, zoomable = true }) {
  const [zoom, setZoom] = useState(1);

  if (!src) {
    return (
      <div className="ct-wb-viewer">
        <div className="ct-wb-viewer__empty">
          <Icon name="documents" size={20} /> No source document available for this item.
        </div>
      </div>
    );
  }

  return (
    <div className="ct-wb-viewer">
      <iframe
        className="ct-wb-viewer__frame"
        src={src}
        title={title || 'Source document (view only)'}
        sandbox="allow-same-origin"
        style={{ transform: `scale(${zoom})`, transformOrigin: 'top left', width: `${100 / zoom}%`, height: `${100 / zoom}%` }}
      />
      <div className="ct-wb-viewer__controls">
        {zoomable && (
          <>
            <Button variant="secondary" size="sm" icon="x" aria-label="Zoom out" onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.25).toFixed(2)))} />
            <span>{Math.round(zoom * 100)}%</span>
            <Button variant="secondary" size="sm" icon="plus" aria-label="Zoom in" onClick={() => setZoom((z) => Math.min(2, +(z + 0.25).toFixed(2)))} />
          </>
        )}
        {!allowDownload && (
          <span className="ct-wb-viewer__no-download">
            <Icon name="lock" size={12} aria-hidden="true" />
            View only — download disabled for this role
          </span>
        )}
      </div>
    </div>
  );
}
