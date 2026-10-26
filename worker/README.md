# Shared "Music volume" ratings: Cloudflare Worker + D1

The page works without this: with `SOUND_API` empty in `index_template.html`, a
rating stays in the visitor's own browser. To share ratings between visitors,
deploy this Worker (free tier is plenty). One-time setup, from this folder:

```bash
npx wrangler login                     # opens the browser to sign in to Cloudflare
npx wrangler d1 create naper-kids      # prints a database_id
```

1. Paste that `database_id` into `wrangler.toml`.
2. Create the table and deploy:

```bash
npx wrangler d1 execute naper-kids --remote --file=schema.sql
npx wrangler deploy                    # prints https://naper-kids-sound.<you>.workers.dev
```

3. Put that URL in `const SOUND_API = '';` in `../index_template.html`, run
   `python3 ../build.py`, then commit and push.

If the site is ever hosted somewhere other than `https://yijiang1.github.io` or
`http://localhost:8000`, add its origin to `ALLOWED_ORIGINS` in `wrangler.toml`
and redeploy.

## Looking at and cleaning the data

Cloudflare dashboard > **Storage & Databases > D1 > naper-kids > Explore data**,
or from the command line:

```bash
npx wrangler d1 execute naper-kids --remote --command "SELECT venue, COUNT(*) n, ROUND(AVG(rating),1) avg FROM ratings GROUP BY venue ORDER BY n DESC"
npx wrangler d1 execute naper-kids --remote --command "DELETE FROM ratings WHERE voter = '<a spammer's id>'"
```

(Summaries are cached for ~20 seconds, so deletions show up after that.)

## What it stores, and its limits

- A `ratings` table: `venue, voter, rating, time`. `voter` is a random id the
  browser generates; there are no names, accounts or IP addresses stored.
- One rating per browser per place; tapping the same number again clears it.
- It is **not** tamper-proof. The Worker URL ships in a public page, and anyone
  who clears their site data gets a new voter id. Guard rails: writes are only
  accepted from the origins in `ALLOWED_ORIGINS` (a browser on another site is
  refused; a script that fakes the `Origin` header is not), ids and ratings are
  validated, a browser can rate at most 150 places, and the table stops growing
  at 50,000 rows. For real abuse, add a rate-limiting rule in the Cloudflare
  dashboard (Security > WAF > Rate limiting rules).
- Reads return only per-place counts, never voter ids.

## Tests

`node --no-warnings test.mjs` runs the Worker's real SQL against an in-memory
SQLite (needs Node 22+). It doesn't cover Cloudflare itself (D1 quirks, CORS as
seen by a real browser), so after deploying, rate a place on the live page and
check that a row appears in the dashboard.
