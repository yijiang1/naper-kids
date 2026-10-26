// Runs the Worker against a real in-memory SQLite (node:sqlite, Node 22+)
// wrapped to look like D1. Usage: node worker/test.mjs
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import worker from './src/index.js';

const sql = new DatabaseSync(':memory:');
sql.exec(readFileSync(new URL('./schema.sql', import.meta.url), 'utf8'));
const DB = {
  prepare(q) {
    const st = sql.prepare(q);
    const mk = (args) => ({
      bind: (...a) => mk(a),
      all: async () => ({ results: st.all(...args) }),
      first: async () => st.get(...args) || null,
      run: async () => { st.run(...args); return {}; },
    });
    return mk([]);
  },
};
const env = { DB, ALLOWED_ORIGINS: 'https://yijiang1.github.io,http://localhost:8000' };
const SITE = 'https://yijiang1.github.io';
const A = 'a'.repeat(32), B = 'b'.repeat(32);

let failed = 0;
const eq = (got, want, msg) => {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (!ok) failed++;
  console.log(ok ? 'ok  ' : 'FAIL', msg, ok ? '' : JSON.stringify(got) + ' != ' + JSON.stringify(want));
};
const call = async (method, body, origin = SITE) => {
  const headers = origin ? { Origin: origin, 'Content-Type': 'text/plain;charset=UTF-8' } : {};
  const res = await worker.fetch(new Request('https://w.example/', {
    method, headers, body: body === undefined ? undefined : JSON.stringify(body) }), env);
  return { status: res.status, headers: res.headers, json: res.status === 204 ? null : await res.json() };
};
const post = (o, origin) => call('POST', o, origin);

eq((await post({ venue: 'knoch-park', voter: A, rating: 2 })).json.counts, [0, 1, 0, 0, 0], 'first rating');
eq((await post({ venue: 'knoch-park', voter: B, rating: 2 })).json.counts, [0, 2, 0, 0, 0], 'second voter');
eq((await post({ venue: 'knoch-park', voter: A, rating: 4 })).json.counts, [0, 1, 0, 1, 0], 'changing replaces, not adds');
eq((await call('GET')).json.ratings['knoch-park'], [0, 1, 0, 1, 0], 'summary');
eq((await post({ venue: 'knoch-park', voter: A, rating: 0 })).json.counts, [0, 1, 0, 0, 0], 'clear');
eq((await post({ venue: 'knoch-park', voter: A, rating: 0 })).json.counts, [0, 1, 0, 0, 0], 'clearing twice is a no-op');
for (const bad of [{ venue: 'X y', voter: A, rating: 1 }, { venue: 'k', voter: 'zz', rating: 1 },
  { venue: 'k', voter: A, rating: 6 }, { venue: 'k', voter: A, rating: 2.5 }, { venue: 'k', voter: A, rating: 'x' }, {}])
  eq((await post(bad)).status, 400, 'rejects ' + JSON.stringify(bad));
const r = await post({ venue: 'knoch-park', voter: A, rating: 1 }, 'https://evil.example');
eq(r.status, 403, 'POST from another origin is refused');
eq((await post({ venue: 'knoch-park', voter: A, rating: 1 }, null)).status, 403, 'POST with no Origin is refused');
const ok = await post({ venue: 'a-park', voter: A, rating: 3 });
eq(ok.headers.get('access-control-allow-origin'), SITE, 'CORS header for the site');
eq((await call('OPTIONS')).status, 204, 'preflight');
for (let i = 0; i < 149; i++) await post({ venue: 'p' + i, voter: B, rating: 3 });   // B has knoch-park + 149 = 150
eq((await post({ venue: 'one-too-many', voter: B, rating: 3 })).json.error, 'limit', 'per-browser cap');
eq((await post({ venue: 'p3', voter: B, rating: 5 })).json.ok, true, 'cap does not block changing an existing rating');
process.exit(failed ? 1 : 0);
