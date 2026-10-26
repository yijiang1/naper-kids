/**
 * Naper Kids: shared "Music volume" ratings, as a Cloudflare Worker + D1.
 *
 *   GET  /                      -> {ok, ratings: {venueId: [n1..n5]}}
 *   POST / {venue, voter, rating} -> {ok, counts: [n1..n5]}   rating 0 clears
 *
 * The page sends the POST body as text/plain (no CORS preflight needed), but
 * JSON content types and OPTIONS are handled too.
 */
const MAX_ROWS = 50000;      // refuse new rows past this
const MAX_PER_VOTER = 150;   // one browser can rate at most this many places

function allowedOrigin(request, env) {
  const origin = request.headers.get('Origin');
  const list = String(env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
  return origin && list.indexOf(origin) !== -1 ? origin : null;
}

function reply(body, status, origin, extra) {
  const headers = Object.assign({
    'Content-Type': 'application/json; charset=utf-8',
    'Vary': 'Origin',
  }, extra || {});
  if (origin) {
    headers['Access-Control-Allow-Origin'] = origin;
    headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS';
    headers['Access-Control-Allow-Headers'] = 'Content-Type';
    headers['Access-Control-Max-Age'] = '86400';
  }
  return new Response(body === null ? null : JSON.stringify(body), { status, headers });
}

async function countsFor(db, venue) {
  const { results } = await db
    .prepare('SELECT rating, COUNT(*) AS n FROM ratings WHERE venue = ? GROUP BY rating')
    .bind(venue).all();
  const c = [0, 0, 0, 0, 0];
  for (const r of results) c[r.rating - 1] = r.n;
  return c;
}

async function summary(db) {
  const { results } = await db
    .prepare('SELECT venue, rating, COUNT(*) AS n FROM ratings GROUP BY venue, rating')
    .all();
  const out = {};
  for (const r of results) {
    if (!out[r.venue]) out[r.venue] = [0, 0, 0, 0, 0];
    out[r.venue][r.rating - 1] = r.n;
  }
  return out;
}

async function rate(db, body) {
  const venue = String(body.venue || '');
  const voter = String(body.voter || '');
  const rating = Number(body.rating);
  // The shapes the page produces: slug ids, a hex browser id, a whole 0-5.
  if (!/^[a-z0-9][a-z0-9-]{0,79}$/.test(venue)) return { error: 'bad venue' };
  if (!/^[a-f0-9]{16,64}$/.test(voter)) return { error: 'bad voter' };
  if (!(Number.isInteger(rating) && rating >= 0 && rating <= 5)) return { error: 'bad rating' };

  if (rating === 0) {
    await db.prepare('DELETE FROM ratings WHERE venue = ? AND voter = ?').bind(venue, voter).run();
  } else {
    const have = await db
      .prepare('SELECT 1 AS x FROM ratings WHERE venue = ? AND voter = ?').bind(venue, voter).first();
    if (!have) {
      const total = await db.prepare('SELECT COUNT(*) AS n FROM ratings').first();
      if (total.n >= MAX_ROWS) return { error: 'full' };
      const mine = await db.prepare('SELECT COUNT(*) AS n FROM ratings WHERE voter = ?').bind(voter).first();
      if (mine.n >= MAX_PER_VOTER) return { error: 'limit' };
    }
    await db
      .prepare(`INSERT INTO ratings (venue, voter, rating) VALUES (?, ?, ?)
                ON CONFLICT (venue, voter) DO UPDATE SET rating = excluded.rating, time = datetime('now')`)
      .bind(venue, voter, rating).run();
  }
  return { ok: true, counts: await countsFor(db, venue) };
}

export default {
  async fetch(request, env) {
    const origin = allowedOrigin(request, env);
    if (request.method === 'OPTIONS') return reply(null, 204, origin);

    if (request.method === 'GET') {
      // Reads are public aggregates (no voter ids), so any origin may read them,
      // but only the listed pages get the CORS header that lets a browser use them.
      return reply({ ok: true, ratings: await summary(env.DB) }, 200, origin,
        { 'Cache-Control': 'public, max-age=20' });
    }

    if (request.method === 'POST') {
      if (!origin) return reply({ ok: false, error: 'origin not allowed' }, 403, null);
      let body;
      try { body = JSON.parse(await request.text()); }
      catch (e) { return reply({ ok: false, error: 'bad json' }, 400, origin); }
      const res = await rate(env.DB, body);
      return res.error
        ? reply({ ok: false, error: res.error }, 400, origin)
        : reply(res, 200, origin);
    }
    return reply({ ok: false, error: 'method not allowed' }, 405, origin);
  },
};
