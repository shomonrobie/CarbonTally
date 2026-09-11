// CarbonTally P6-2F — minimal static server for a locally built SPA.
//
// Serves a Create-React-App build with single-page-app fallback (deep links such
// as /consultant resolve to index.html so client routing can run). Intended only
// for the isolated browser E2E environment — never production.
//
// Usage: node tests/e2e/static-server.mjs [buildDir] [port]
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

const root = process.argv[2] || './frontend/build';
const port = Number(process.argv[3] || process.env.E2E_PORT || 3000);

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
};

const server = http.createServer(async (req, res) => {
  const urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
  const candidate = normalize(join(root, urlPath));
  if (!candidate.startsWith(normalize(root))) {
    res.writeHead(403).end('Forbidden');
    return;
  }
  try {
    const body = await readFile(candidate);
    res.writeHead(200, { 'content-type': TYPES[extname(candidate)] || 'application/octet-stream' });
    res.end(body);
  } catch {
    // SPA fallback
    try {
      const html = await readFile(join(root, 'index.html'));
      res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      res.end(html);
    } catch {
      res.writeHead(404).end('Not found');
    }
  }
});

server.listen(port, () => {
  console.log(`CarbonTally static E2E server: http://localhost:${port} (root: ${root})`);
});
