# Naper Kids — dev notes

A single-file personal dashboard of kid-friendly places in Naperville, IL.
No build system beyond a tiny Python script — this stays plain HTML/CSS/JS
on purpose so it keeps working as one portable, offline-capable file.

## How the pieces fit together

- **`venues.json`** — the actual content. `venues` is the curated list (22
  entries: id, name, category, lat/lng, address, rating, phone, website,
  hours, cost, age, note, plus `place_id` once the updater has matched it
  to Google). `candidates` is a holding pen for places the updater found
  that nobody has curated yet; the page ignores it. This is what changes
  most often.
- **`index_template.html`** — the real source of the page: markup, CSS, and
  all JS logic (filtering, sorting, the map, favorites, voting). Has one
  placeholder, `__VENUES_JSON__`, where the data gets inlined at build time.
- **`build.py`** — reads `venues.json` + `index_template.html`, substitutes
  the placeholder, writes `index.html`. Run this after editing either
  source file.
- **`index.html`** — the generated, self-contained output. This is what
  actually gets opened / hosted / shared. **Don't hand-edit this file** —
  edits get overwritten on the next build. Edit `index_template.html` or
  `venues.json` instead, then rebuild.
- **`update_venues.py`** — refreshes `venues.json` from the Google Places
  API (needs a `GOOGLE_PLACES_API_KEY` env var). It never removes a venue,
  never changes a venue's category or name, and never touches the
  hand-curated `note`, `hours`, `cost`, and `age` fields; it only refreshes
  rating/address/phone/website/lat/lng, and only when Google actually
  returns a value. Google results are matched to existing venues by
  `place_id`, then by id slug, then by "within 150 m and names mostly
  overlap" (see `MATCH_RADIUS_M` / `MATCH_NAME_SCORE`). Unmatched results
  go to `candidates`.
- **`test_update_venues.py`** — runs the updater against a fake Places API
  on a temp copy of the data and asserts nothing curated is lost or
  duplicated. Stdlib only. Run it after any change to the updater.
- **`.github/workflows/update-venues.yml`** — optional GitHub Actions job
  that runs `update_venues.py` on a schedule, if this repo ever gets pushed
  to GitHub with Pages enabled.

## Workflow

```bash
# after editing venues.json or index_template.html:
python3 build.py

# then check it locally:
python3 -m http.server 8000   # visit http://localhost:8000

# after editing update_venues.py:
python3 test_update_venues.py
```

A quick way to catch a JS syntax slip in the template without opening a
browser: pull the inline `<script>` out, swap `__VENUES_JSON__` for `{}`,
and run `node --check` on it. (The first commit shipped with a missing
`function ageOverlaps(v){` line and nothing rendered — cheap to prevent.)

## Constraints worth keeping in mind

- **Zero build tooling** (no npm, no bundler) — keep it that way. It should
  always be openable by just double-clicking `index.html`.
- **Python scripts must run on 3.6.** On the dev machine, plain `python3`
  is Anaconda's 3.6 with an ASCII default locale, so: always pass
  `encoding="utf-8"` when opening files, and avoid 3.7+ syntax (walrus,
  `dict | dict`, positional-only params, etc.). The GitHub Action uses 3.12.
- **Works fully offline.** All venue data is embedded inline in
  `index.html` as a JS fallback (`VENUES_FALLBACK`). When hosted, the page
  tries `fetch('./venues.json')` first and only falls back to the embedded
  copy if that fails (e.g. opened via `file://`, where fetch of a sibling
  file is blocked). Consequence: after running the updater, `build.py` has
  to be run too or the double-click copy won't see the new data.
- **Venue text is untrusted once the updater runs.** Everything rendered
  from a venue goes through `esc()` in the template; keep it that way when
  adding fields, since names/addresses come straight from Google.
- **Map tiles are fragile — pick providers carefully.** Currently using
  Esri's keyless World Street Map tiles (`server.arcgisonline.com`). We've
  already been burned twice by "free" tile providers changing terms:
  OpenStreetMap's own tile server blocked direct hotlinking, then CARTO
  started requiring an API key shortly after. If Esri breaks too, swap the
  `L.tileLayer(...)` call inside `index_template.html` (not `index.html`),
  then rebuild.
- **Map fitting is deferred while the map is hidden.** On phones the map is
  `display:none` in list view; `fitMapTo()` parks the request in
  `pendingFitBounds` and `showView('map')` applies it. The map is also only
  re-fitted when the *set* of visible venues changes, so starring/voting
  doesn't move it.
- **Favorites and "Best age?" votes are per-browser only** (`localStorage`
  keys `naperkids_favs_v1` and `naperkids_votes_v1`, no backend). This was
  an explicit choice to avoid standing up a server. A Google Sheets + Apps
  Script "web app" endpoint was discussed as the upgrade path if real
  cross-visitor shared voting is wanted later — not built yet.
- **"Near me" needs a secure context** for `navigator.geolocation`: fine on
  GitHub Pages (https), `localhost`, and `file://` in current browsers. The
  button hides itself if the API is missing; permission errors show in the
  status line under the toolbar.
- **`cost` and `age` are hand-researched fields** — the Places API returns
  neither, so `update_venues.py` is written to never overwrite them.

## Not yet done

- No git remote configured — this repo is local-only so far. Local branch
  is `master`; README's GitHub Pages steps assume `main`.
- `GOOGLE_PLACES_API_KEY` has not been created/tested, so the updater has
  only ever run against the fake API in `test_update_venues.py`.
- Shared (cross-visitor) voting was discussed but intentionally not built.
- Not yet hosted anywhere (GitHub Pages setup is documented in README.md
  but hasn't been done).
- Cosley Zoo's `note` says "~$8 admission" while its `cost` says $12 — one
  of them is stale; check the zoo's site.
