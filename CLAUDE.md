# Naper Kids — dev notes

A single-file personal dashboard of kid-friendly places in Naperville, IL.
No build system beyond a tiny Python script — this stays plain HTML/CSS/JS
on purpose so it keeps working as one portable, offline-capable file.

## How the pieces fit together

- **`venues.json`** — the actual content (22 venues: name, category, lat/lng,
  address, rating, phone, website, hours, cost, age, note). This is what
  changes most often.
- **`index_template.html`** — the real source of the page: markup, CSS, and
  all JS logic (filtering, the map, voting). Has one placeholder,
  `__VENUES_JSON__`, where the data gets inlined at build time.
- **`build.py`** — reads `venues.json` + `index_template.html`, substitutes
  the placeholder, writes `index.html`. Run this after editing either
  source file.
- **`index.html`** — the generated, self-contained output. This is what
  actually gets opened / hosted / shared. **Don't hand-edit this file** —
  edits get overwritten on the next build. Edit `index_template.html` or
  `venues.json` instead, then rebuild.
- **`update_venues.py`** — refreshes `venues.json` from the Google Places
  API (needs a `GOOGLE_PLACES_API_KEY` env var). Preserves the hand-curated
  `note`, `hours`, `cost`, and `age` fields; only refreshes
  rating/address/phone/website.
- **`.github/workflows/update-venues.yml`** — optional GitHub Actions job
  that runs `update_venues.py` on a schedule, if this repo ever gets pushed
  to GitHub with Pages enabled.

## Workflow

```bash
# after editing venues.json or index_template.html:
python3 build.py

# then check it locally:
python3 -m http.server 8000   # visit http://localhost:8000
```

## Constraints worth keeping in mind

- **Zero build tooling** (no npm, no bundler) — keep it that way. It should
  always be openable by just double-clicking `index.html`.
- **Works fully offline.** All venue data is embedded inline in
  `index.html` as a JS fallback (`VENUES_FALLBACK`). When hosted, the page
  tries `fetch('./venues.json')` first and only falls back to the embedded
  copy if that fails (e.g. opened via `file://`, where fetch of a sibling
  file is blocked).
- **Map tiles are fragile — pick providers carefully.** Currently using
  Esri's keyless World Street Map tiles (`server.arcgisonline.com`). We've
  already been burned twice by "free" tile providers changing terms:
  OpenStreetMap's own tile server blocked direct hotlinking, then CARTO
  started requiring an API key shortly after. If Esri breaks too, swap the
  `L.tileLayer(...)` call inside `index_template.html` (not `index.html`),
  then rebuild.
- **"Best age?" votes are per-browser only** (stored in `localStorage`,
  no backend). This was an explicit choice to avoid standing up a server.
  A Google Sheets + Apps Script "web app" endpoint was discussed as the
  upgrade path if real cross-visitor shared voting is wanted later — not
  built yet.
- **`cost` and `age` are hand-researched fields** — the Places API returns
  neither, so `update_venues.py` is written to never overwrite them on
  existing venues, only to fill them in blank for newly-discovered ones.

## Not yet done

- No git remote configured — this repo is local-only so far.
- `GOOGLE_PLACES_API_KEY` has not been created/tested.
- Shared (cross-visitor) voting was discussed but intentionally not built.
- Not yet hosted anywhere (GitHub Pages setup is documented in README.md
  but hasn't been done).
