// frontend/src/v3/__tests__/backup-admin-api.test.js
// BACKUP-01/02 — API-client contract for the Admin Backups area.
//
// These tests assert the *shape* the backend actually serves: the paths, the
// explicit `confirm` flag §9 requires, and that a download returns the
// server-supplied filename. They never assert authorization — that is enforced
// server-side (`require_admin()` + `can_manage_backups`) and cannot be tested
// from the browser side.
jest.mock('../../supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: async () => ({ data: { session: { access_token: 'test-token' } } }),
      getUser: async () => ({ data: { user: { id: 'u-1' } } }),
    },
  },
}));

import {
  getBackupStatus,
  listBackups,
  getBackup,
  getBackupPair,
  createBackup,
  verifyBackup,
  getBackupPolicy,
  updateBackupPolicy,
  downloadBackupArtifact,
} from '../api';

describe('Admin Backups API client', () => {
  const endpointFunctions = [
    ['getBackupStatus', getBackupStatus],
    ['listBackups', listBackups],
    ['getBackup', getBackup],
    ['getBackupPair', getBackupPair],
    ['createBackup', createBackup],
    ['verifyBackup', verifyBackup],
    ['getBackupPolicy', getBackupPolicy],
    ['updateBackupPolicy', updateBackupPolicy],
    ['downloadBackupArtifact', downloadBackupArtifact],
  ];

  test.each(endpointFunctions)('%s is exported and callable', (_name, fn) => {
    expect(typeof fn).toBe('function');
  });

  test('createBackup is a POST carrying the explicit confirm flag', () => {
    const source = createBackup.toString();
    expect(source).toContain('/api/v3/admin/backups');
    expect(source).toContain("method: 'POST'");
    expect(source).toContain('confirm: true');
  });

  test('verifyBackup is a POST to the per-job verify endpoint', () => {
    const source = verifyBackup.toString();
    expect(source).toContain('/verify');
    expect(source).toContain("method: 'POST'");
  });

  test('updateBackupPolicy is a PUT to the policy endpoint', () => {
    const source = updateBackupPolicy.toString();
    expect(source).toContain('/api/v3/admin/backups/policy');
    expect(source).toContain("method: 'PUT'");
  });

  test('listBackups bounds the query with limit and offset', () => {
    const source = listBackups.toString();
    expect(source).toContain('limit=');
    expect(source).toContain('offset=');
  });

  describe('downloadBackupArtifact', () => {
    beforeEach(() => {
      global.URL.createObjectURL = jest.fn(() => 'blob:test');
      global.URL.revokeObjectURL = jest.fn();
    });

    test('returns the filename the server set and requests the job path', async () => {
      global.fetch = jest.fn(async () => ({
        ok: true,
        blob: async () => new Blob(['ciphertext']),
        headers: { get: () => 'attachment; filename="carbontally-database-abc.tar.gz.enc"' },
      }));

      const filename = await downloadBackupArtifact('abc');
      expect(filename).toBe('carbontally-database-abc.tar.gz.enc');
      expect(global.fetch.mock.calls[0][0]).toContain(
        '/api/v3/admin/backups/abc/download',
      );
    });

    test('surfaces the backend detail when the download is refused', async () => {
      global.fetch = jest.fn(async () => ({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Backup management is not permitted' }),
      }));

      await expect(downloadBackupArtifact('abc')).rejects.toThrow(
        'Backup management is not permitted',
      );
    });
  });
});
