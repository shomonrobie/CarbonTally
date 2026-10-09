// frontend/src/v3/uploadsCopy.js
//
// Storage Management Step 2A — user-facing copy for the direct-upload outcomes.
// Shared by the single-upload form and the restored V3 batch-upload panel
// (CT-PO-UPLOAD-BATCH-REMEDIATION-001) so both explain the SAME backend answer.
// Every string describes what the backend actually decided; nothing here invents
// a success, and nothing claims a failed upload "added" a document.

/** The supported document types (mirrors the server-side allow-list). */
export const ACCEPTED_DOCUMENT_TYPES =
  '.pdf,.jpg,.jpeg,.png,.gif,.webp,.bmp,.csv,.xlsx,.xls';

export const describeUploadError = (e) => {
  switch (e?.code) {
    case 'UPLOAD_TOO_LARGE':
      return (
        e.message ||
        'That file is larger than the platform per-file limit. The original is never compressed server-side — please upload a smaller file or split the document.'
      );
    case 'UPLOAD_UNSUPPORTED_TYPE':
      return (
        e.message ||
        'That file type is not supported. Supported: PDF, JPG/PNG/GIF/WEBP/BMP, CSV, XLSX/XLS.'
      );
    case 'UPLOAD_SECURITY_REJECTED':
      return (
        e.message ||
        'The document was rejected by the security check, so it did not enter processing.'
      );
    case 'UPLOAD_AUTHORIZATION_EXPIRED':
      return (
        'The upload authorisation expired or was refused before the file reached storage. No document was added — please start the upload again.'
      );
    case 'UPLOAD_STORAGE':
      return (
        'The file did not reach storage, so no document was added. The failed attempt is recorded as an abandoned upload and will not be processed — please try again.'
      );
    case 'UPLOAD_NETWORK':
      return (
        'The upload was interrupted before the file reached storage. No document was added; the attempt is recorded as abandoned — please try again.'
      );
    default:
      return e?.message || 'Upload failed';
  }
};

export const describeSecurityGate = (result) => {
  const gate = result?.security_gate || {};
  if (result?.virus_scanned) return `virus scan reported by ${gate.scanner}`;
  const state = result?.scan_state || gate.scan_state;
  if (state === 'clean') {
    return 'structural validation passed — no external virus scanner is configured for this deployment';
  }
  return state || 'recorded by the backend';
};

/**
 * CT-PO-UPLOAD-UNIFY-001 — how CarbonTally describes the type of a single
 * uploaded document.
 *
 * The verdict is decided SERVER-SIDE against the CarbonTally document taxonomy
 * (`utils.document_classifier` over the `document_types` reference table); this
 * helper only explains it. It never invents a type: when the taxonomy could not
 * be consulted, or nothing in the document identified it, the user is told that
 * plainly and that CarbonTally will confirm the type during processing.
 */
export const describeClassification = (classification) => {
  if (!classification) return '';
  const { source, suggested_type: suggested, confidence } = classification;
  if (source === 'user_selected') {
    return suggested ? `Type set to ${suggested}.` : 'Type set by the uploader.';
  }
  if (source === 'unavailable' || source === 'error') {
    return 'Type not detected — CarbonTally will confirm the document type during processing.';
  }
  if (!suggested || classification.document_type_code === 'other') {
    return 'Type not recognised from this document — CarbonTally will confirm it during processing.';
  }
  const percent = Math.round((confidence || 0) * 100);
  return `Detected: ${suggested} (${percent}% confidence — confirmed during processing).`;
};
