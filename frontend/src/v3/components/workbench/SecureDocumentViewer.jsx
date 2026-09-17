// frontend/src/v3/components/workbench/SecureDocumentViewer.jsx
// D19/D32 — secure, view-only source document container. Renders a signed URL
// inside an iframe with the PE no-download boundary preserved: when
// `allowDownload` is false the control bar shows an explicit "View only — no
// download" affordance and no download control is rendered.
//
// P0-1 — inline rendering fix:
// * Chromium disables its PDF viewer inside sandboxed iframes, so PDFs must be
//   rendered in a NON-sandboxed frame. The iframe only ever points at a
//   server-authorized, short-lived, private-bucket signed URL (never an
//   unrestricted original-document URL), and the content is classified here by
//   file name before any frame is created.
// * Non-PDF content (images) stays in a sandboxed frame. Structured data
//   (CSV/TSV/XLSX) is NOT framed — it renders through StructuredDataPreview
//   (Step 2C / POD-3): a bounded, read-only tabular/workbook preview, because a
//   CSV/Excel upload previously showed "preview not available" while the file
//   was perfectly readable. Truly unknown types keep the explicit placeholder.
//
// NOTE: the security boundary is server-side (signed URLs + RLS). This
// component never fabricates a security guarantee — it is UX presentation of
// the backend-enforced boundary.
import React, { useState } from 'react';
import Icon from '../ui/Icon';
import { Button } from '../ui';
import StructuredDataPreview from './StructuredDataPreview';

/**
 * Classify the source file so the viewer only frames content that can render
 * inline safely. `title` is the source file name in every workbench caller
 * (`source.file_name` / `item.file_name`); when absent, the signed-URL path is
 * inspected as a fallback.
 */
function detectKind(title, src) {
  const urlName = String(src || '').split('?')[0].split('#')[0].toLowerCase();
  const name = String(title || urlName).toLowerCase();
  if (name.endsWith('.pdf')) return 'pdf';
  if (/\.(png|jpe?g|gif|webp|bmp|tiff?)$/.test(name)) return 'image';
  if (/\.(csv|xlsx?|tsv)$/.test(name)) return 'data';
  return 'other';
}

export default function SecureDocumentViewer({ src, title, allowDownload = false, zoomable = true }) {
  const [zoom, setZoom] = useState(1);
  const kind = src ? detectKind(title, src) : 'none';
  // PDFs render inline only in a non-sandboxed frame (Chromium PDF viewer
  // limitation). Images render inside a sandboxed frame. Non-renderable types
  // are never framed.
  const canInlineRender = kind === 'pdf' || kind === 'image';
  const sandbox = kind === 'pdf' ? undefined : 'allow-same-origin';

  if (!src) {
    return (
      <div className="ct-wb-viewer">
        <div className="ct-wb-viewer__empty">
          <Icon name="documents" size={20} /> No source document available for this item.
        </div>
      </div>
    );
  }

  if (kind === 'data') {
    // Step 2C / POD-3 — CSV/TSV/XLSX get a real structured preview instead of a
    // "not available" placeholder.
    return (
      <div className="ct-wb-viewer">
        <StructuredDataPreview src={src} title={title} />
        {!allowDownload && (
          <div className="ct-wb-viewer__controls">
            <span className="ct-wb-viewer__no-download">
              <Icon name="lock" size={12} aria-hidden="true" />
              View only — download disabled for this role
            </span>
          </div>
        )}
      </div>
    );
  }

  if (!canInlineRender) {
    return (
      <div className="ct-wb-viewer">
        <div className="ct-wb-viewer__empty">
          <Icon name="lock" size={20} aria-hidden="true" />
          <span style={{ marginLeft: 8 }}>
            Document preview is not available for this file type.
            {!allowDownload && ' Download is restricted for this role.'}
          </span>
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
        // P0-1: no sandbox for PDFs (Chromium's PDF viewer is disabled in
        // sandboxed frames). The frame content is a private, expiring signed
        // URL; non-PDF content remains sandboxed.
        sandbox={sandbox}
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

