/**
 * H2 — the admin console must never render a blank page when its deployment
 * configuration is missing or unusable (P18 · PUBLIC-TRUTH-02).
 *
 * The pre-fix behaviour was `createClient(undefined, undefined)` evaluated at
 * module scope, which threw before React could mount: `/admin` was blank with no
 * explanation, and a malformed project URL behaved the same way.
 */
const ENV_KEYS = ['REACT_APP_SUPABASE_URL', 'REACT_APP_SUPABASE_ANON_KEY'];

const originalEnv = ENV_KEYS.reduce((acc, key) => {
  acc[key] = process.env[key];
  return acc;
}, {});

/** Import the module under a specific configuration, asserting it cannot throw. */
const loadClient = ({ url, key } = {}) => {
  jest.resetModules();
  ENV_KEYS.forEach((name) => delete process.env[name]);
  if (url !== undefined) process.env.REACT_APP_SUPABASE_URL = url;
  if (key !== undefined) process.env.REACT_APP_SUPABASE_ANON_KEY = key;

  let loaded;
  expect(() => {
    // eslint-disable-next-line global-require
    loaded = require('./supabaseClient');
  }).not.toThrow();

  return loaded;
};

afterAll(() => {
  ENV_KEYS.forEach((name) => {
    if (originalEnv[name] === undefined) delete process.env[name];
    else process.env[name] = originalEnv[name];
  });
});

describe('admin Supabase configuration (H2)', () => {
  let consoleError;

  beforeEach(() => {
    consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleError.mockRestore();
  });

  describe('no configuration in the deployed bundle', () => {
    it('imports without throwing and reports both settings as missing', () => {
      const module = loadClient();

      expect(module.isSupabaseConfigured).toBe(false);
      expect(module.isSupabaseReady).toBe(false);
      expect(module.missingSupabaseConfig).toEqual(ENV_KEYS);
      expect(module.supabase).toBeNull();
    });

    it('explains the problem on the console without echoing any value', () => {
      loadClient({ url: 'https://secret-project.supabase.co' });

      const messages = consoleError.mock.calls.map((call) => String(call[0])).join('\n');
      expect(messages).toContain('REACT_APP_SUPABASE_ANON_KEY');
      expect(messages).not.toContain('secret-project');
    });
  });

  describe('partial configuration', () => {
    it('names only the setting that is actually absent', () => {
      const module = loadClient({ url: 'https://project.supabase.co' });

      expect(module.missingSupabaseConfig).toEqual(['REACT_APP_SUPABASE_ANON_KEY']);
      expect(module.isSupabaseReady).toBe(false);
      expect(module.supabase).toBeNull();
    });

    it('treats blank and whitespace-only values as absent', () => {
      const module = loadClient({ url: '   ', key: '' });

      expect(module.missingSupabaseConfig).toEqual(ENV_KEYS);
      expect(module.supabase).toBeNull();
    });
  });

  describe('unusable configuration', () => {
    it('reports a reason instead of throwing when the project URL is malformed', () => {
      const module = loadClient({ url: 'not-a-valid-url', key: 'anon-key' });

      expect(module.isSupabaseReady).toBe(false);
      expect(module.supabase).toBeNull();
      expect(module.supabaseConfigurationError).toBeTruthy();
      expect(module.missingSupabaseConfig).toEqual([]);
    });
  });

  describe('valid configuration', () => {
    it('creates the client and reports no configuration problem', () => {
      const module = loadClient({ url: 'https://project.supabase.co', key: 'anon-key' });

      expect(module.isSupabaseReady).toBe(true);
      expect(module.isSupabaseConfigured).toBe(true);
      expect(module.missingSupabaseConfig).toEqual([]);
      expect(module.supabaseConfigurationError).toBeNull();
      expect(module.supabase).toBeTruthy();
      expect(typeof module.supabase.auth.getSession).toBe('function');
      expect(consoleError).not.toHaveBeenCalled();
    });
  });

  describe('authorization helper fails closed', () => {
    it('does not attempt a lookup and reports no privilege when unconfigured', async () => {
      const module = loadClient();

      await expect(module.isAdminOrStaff('11111111-2222-3333-4444-555555555555')).resolves.toEqual({
        isStaff: false,
        role: 'user',
      });
    });

    it('returns false for an absent user id', async () => {
      const module = loadClient({ url: 'https://project.supabase.co', key: 'anon-key' });

      await expect(module.isAdminOrStaff(null)).resolves.toBe(false);
    });
  });
});
