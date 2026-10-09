// frontend/src/v3/__tests__/direct-upload.test.js
//
// Storage Management Step 2A — the browser-facing direct-upload contract.
//
// The browser must: ask CarbonTally for an object-scoped upload authorisation,
// PUT the bytes straight to private storage, then confirm completion so the
// backend can verify the object and run the security gate. It must never hold a
// storage credential, and it must report the BACKEND's verdict — including a
// rejection — instead of assuming success.
jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: async () => ({ data: { session: null } }) } },
}));

import {
  putBytesToSignedUrl,
  uploadConsultantDocument,
  v3CompleteConsultantDirectUpload,
  v3CompleteDirectUpload,
  v3StartConsultantDirectUpload,
  v3StartDirectUpload,
  v3UploadConsultantDocumentDirect,
  v3UploadDocumentDirect,
} from '../api';

const START_PAYLOAD = {
  document_id: 'doc-1',
  organization_id: 'org-a',
  storage_path: 'uploads/org-a/2026/09/30/abc123.pdf',
  status: 'pending_upload',
  max_size_bytes: 6291456,
  security_gate: { built_in_scanner: 'structural', external_scan_available: false },
  upload: {
    url: 'https://storage.test/object/upload/sign/documents/uploads/org-a/abc123.pdf?token=t',
    token: 't',
    method: 'PUT',
    expires_in_seconds: 900,
    headers: { 'x-upsert': 'false', 'content-type': 'application/pdf' },
  },
  completion: { method: 'POST', path: '/api/v3/documents/{document_id}/upload-complete' },
};

const COMPLETION_PAYLOAD = {
  document_id: 'doc-1',
  organization_id: 'org-a',
  status: 'clean',
  scan_state: 'clean',
  virus_scanned: false,
  external_scan_available: false,
  security_gate: { verdict: 'clean', scanner: 'structural', scan_state: 'clean' },
};

class FakeXHR {
  static instances = [];

  constructor() {
    this.headers = {};
    this.upload = {};
    FakeXHR.instances.push(this);
  }

  open(method, url) {
    this.method = method;
    this.url = url;
  }

  setRequestHeader(key, value) {
    this.headers[key] = value;
  }

  send(body) {
    this.body = body;
    this.status = FakeXHR.nextStatus;
    if (this.onload) this.onload();
  }

  abort() {
    if (this.onabort) this.onabort();
  }
}

const jsonResponse = (status, body) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => body,
});

beforeEach(() => {
  FakeXHR.instances = [];
  FakeXHR.nextStatus = 200;
  global.XMLHttpRequest = FakeXHR;
  global.fetch = jest.fn();
});

const file = new File([new Uint8Array([1, 2, 3])], 'invoice.pdf', {
  type: 'application/pdf',
});

describe('Storage Management Step 2A — direct upload client', () => {
  test('the authorisation request is a JSON POST of file metadata only', async () => {
    global.fetch = jest.fn(async () => jsonResponse(201, START_PAYLOAD));
    const started = await v3StartDirectUpload({
      organization_id: 'org-a',
      file,
      data_type: 'utility',
    });
    expect(started.document_id).toBe('doc-1');
    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toContain('/api/v3/documents/upload-url');
    expect(options.method).toBe('POST');
    // No bytes are sent to the backend.
    expect(options.body).not.toBe(file);
    expect(JSON.parse(options.body)).toMatchObject({
      organization_id: 'org-a',
      filename: 'invoice.pdf',
      size_bytes: 3,
      content_type: 'application/pdf',
    });
  });

  test('the bytes go straight to the signed URL with the declared headers', async () => {
    await putBytesToSignedUrl(START_PAYLOAD.upload, file);
    const xhr = FakeXHR.instances[0];
    expect(xhr.method).toBe('PUT');
    expect(xhr.url).toBe(START_PAYLOAD.upload.url);
    expect(xhr.headers['x-upsert']).toBe('false');
    expect(xhr.headers['content-type']).toBe('application/pdf');
    expect(xhr.body).toBe(file);
    // The authorisation is object-scoped: no project/service credential is used.
    expect(xhr.url).not.toContain('service_role');
    expect(xhr.headers).not.toHaveProperty('apikey');
    expect(xhr.headers).not.toHaveProperty('authorization');
  });

  test('start → PUT → complete resolves with the backend verdict', async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse(201, START_PAYLOAD))
      .mockResolvedValueOnce(jsonResponse(200, COMPLETION_PAYLOAD));
    const result = await v3UploadDocumentDirect({
      organization_id: 'org-a',
      data_type: 'utility',
      file,
    });
    expect(result.status).toBe('clean');
    expect(result.scan_state).toBe('clean');
    // The platform never claims a virus scan the deployment did not perform.
    expect(result.virus_scanned).toBe(false);
    const [completionUrl, completionOptions] = global.fetch.mock.calls[1];
    expect(completionUrl).toContain('/api/v3/documents/doc-1/upload-complete');
    expect(completionOptions.method).toBe('POST');
  });

  test('progress is reported while the bytes upload', async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse(201, START_PAYLOAD))
      .mockResolvedValueOnce(jsonResponse(200, COMPLETION_PAYLOAD));
    const seen = [];
    const promise = v3UploadDocumentDirect({
      organization_id: 'org-a',
      data_type: 'utility',
      file,
      onProgress: (pct) => seen.push(pct),
    });
    await promise;
    FakeXHR.instances[0].upload.onprogress({ lengthComputable: true, loaded: 1, total: 4 });
    expect(seen).toEqual([25]);
  });

  test('a 413 is reported as UPLOAD_TOO_LARGE before any byte is uploaded', async () => {
    global.fetch = jest.fn(async () =>
      jsonResponse(413, { detail: 'UPLOAD_FILE_TOO_LARGE: 11.0MB; limit is 6MB' })
    );
    await expect(
      v3UploadDocumentDirect({ organization_id: 'org-a', data_type: 'utility', file })
    ).rejects.toMatchObject({ code: 'UPLOAD_TOO_LARGE', status: 413 });
    expect(FakeXHR.instances).toHaveLength(0);
  });

  test('an unsupported type is reported distinctly from a size failure', async () => {
    global.fetch = jest.fn(async () =>
      jsonResponse(422, { detail: "'.exe' is not an allowed document extension" })
    );
    await expect(
      v3UploadDocumentDirect({ organization_id: 'org-a', data_type: 'utility', file })
    ).rejects.toMatchObject({ code: 'UPLOAD_UNSUPPORTED_TYPE' });
  });

  test('a security rejection at completion is surfaced, not swallowed', async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse(201, START_PAYLOAD))
      .mockResolvedValueOnce(
        jsonResponse(422, {
          detail: 'Document rejected by the security gate: malware signature detected',
        })
      );
    await expect(
      v3UploadDocumentDirect({ organization_id: 'org-a', data_type: 'utility', file })
    ).rejects.toMatchObject({ code: 'UPLOAD_SECURITY_REJECTED' });
  });

  test('an expired authorisation is reported and the abandonment is recorded', async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse(201, START_PAYLOAD))
      .mockResolvedValueOnce(
        jsonResponse(200, {
          document_id: 'doc-1',
          status: 'upload_expired',
          abandoned: true,
          idempotent: false,
        })
      );
    FakeXHR.nextStatus = 403;
    await expect(
      v3UploadDocumentDirect({ organization_id: 'org-a', data_type: 'utility', file })
    ).rejects.toMatchObject({ code: 'UPLOAD_AUTHORIZATION_EXPIRED' });
    // Start + abandonment only — the bytes never landed, so completion is not
    // attempted and the pending row is moved to its terminal state.
    expect(global.fetch).toHaveBeenCalledTimes(2);
    const [abandonUrl, abandonOptions] = global.fetch.mock.calls[1];
    expect(abandonUrl).toContain('/api/v3/documents/doc-1/upload-abandon');
    expect(abandonOptions.method).toBe('POST');
  });

  test('the abandonment record is best-effort and never masks the real failure', async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse(201, START_PAYLOAD))
      .mockRejectedValueOnce(new Error('abandon endpoint unreachable'));
    FakeXHR.nextStatus = 403;
    await expect(
      v3UploadDocumentDirect({ organization_id: 'org-a', data_type: 'utility', file })
    ).rejects.toMatchObject({ code: 'UPLOAD_AUTHORIZATION_EXPIRED' });
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  test('an authorisation that carries no upload URL is refused', async () => {
    global.fetch = jest.fn(async () => jsonResponse(201, { document_id: 'doc-1' }));
    await expect(
      v3UploadDocumentDirect({ organization_id: 'org-a', data_type: 'utility', file })
    ).rejects.toMatchObject({ code: 'UPLOAD_STORAGE' });
    expect(FakeXHR.instances).toHaveLength(0);
  });
});

describe('Storage Management Step 2A — consultant client', () => {
  const CONSULTANT_START = {
    ...START_PAYLOAD,
    completion: {
      method: 'POST',
      path: '/api/v3/consultants/clients/client-a/documents/{document_id}/upload-complete',
    },
  };

  test('the consultant authorisation is scoped to the authorized client', async () => {
    global.fetch = jest.fn(async () => jsonResponse(201, CONSULTANT_START));
    await v3StartConsultantDirectUpload('client-a', file, 'utility');
    expect(global.fetch.mock.calls[0][0]).toContain(
      '/api/v3/consultants/clients/client-a/documents/upload-url'
    );
  });

  test('completion is re-authorized against the active client grant', async () => {
    global.fetch = jest.fn(async () => jsonResponse(200, COMPLETION_PAYLOAD));
    await v3CompleteConsultantDirectUpload('client-a', 'doc-1');
    expect(global.fetch.mock.calls[0][0]).toContain(
      '/api/v3/consultants/clients/client-a/documents/doc-1/upload-complete'
    );
  });

  test('the existing consultant helper uses the direct flow and keeps its shape', async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse(201, CONSULTANT_START))
      .mockResolvedValueOnce(jsonResponse(200, COMPLETION_PAYLOAD));
    const result = await uploadConsultantDocument('client-a', file, 'utility');
    // The consultant workspace still reads `document.id` (unchanged contract).
    expect(result.document.id).toBe('doc-1');
    expect(result.document.organization_id).toBe('org-a');
    expect(result.status).toBe('clean');
    // The old multipart proxied upload is no longer used by the browser.
    expect(global.fetch.mock.calls[0][0]).toContain('/documents/upload-url');
    expect(global.fetch.mock.calls[0][0]).not.toMatch(/\/clients\/client-a\/documents$/);
  });

  test('the direct upload is a PUT straight to storage, never through the backend', async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse(201, CONSULTANT_START))
      .mockResolvedValueOnce(jsonResponse(200, COMPLETION_PAYLOAD));
    await v3UploadConsultantDocumentDirect({
      clientId: 'client-a',
      file,
      data_type: 'utility',
    });
    expect(FakeXHR.instances).toHaveLength(1);
    expect(FakeXHR.instances[0].method).toBe('PUT');
    expect(FakeXHR.instances[0].url).toContain('/object/upload/sign/documents/');
    // Exactly two backend calls: authorisation and completion.
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  test('a consultant PUT failure records the abandonment for the client document', async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse(201, CONSULTANT_START))
      .mockResolvedValueOnce(
        jsonResponse(200, {
          document_id: 'doc-1',
          status: 'upload_expired',
          abandoned: true,
          idempotent: false,
        })
      );
    FakeXHR.nextStatus = 403;
    await expect(
      v3UploadConsultantDocumentDirect({ clientId: 'client-a', file, data_type: 'utility' })
    ).rejects.toMatchObject({ code: 'UPLOAD_AUTHORIZATION_EXPIRED' });
    const [abandonUrl, abandonOptions] = global.fetch.mock.calls[1];
    expect(abandonUrl).toContain(
      '/api/v3/consultants/clients/client-a/documents/doc-1/upload-abandon'
    );
    expect(abandonOptions.method).toBe('POST');
  });
});

describe('Storage Management Step 2A — no credential is ever needed', () => {
  test('the client functions never reference a service-role key or a public URL', () => {
    for (const fn of [
      v3UploadDocumentDirect,
      v3UploadConsultantDocumentDirect,
      v3StartDirectUpload,
      v3CompleteDirectUpload,
      v3StartConsultantDirectUpload,
      v3CompleteConsultantDirectUpload,
      putBytesToSignedUrl,
    ]) {
      const source = fn.toString();
      expect(source).not.toContain('service_role');
      expect(source).not.toContain('SERVICE_KEY');
      expect(source).not.toContain('SUPABASE_SERVICE');
      expect(source).not.toContain('get_public_url');
    }
  });
});
