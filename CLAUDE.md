# Naper Kids — dev notes

A single-file personal dashboard of kid-friendly places. Started as a
Naperville, IL-only list; as of Sep 2026 the scope is the whole Chicago
metro area (`update_venues.py`'s `CENTER` is still Naperville — it's just
the personal reference point for distance-sort/"near me", not a scope
limit — with a ~55 mi `MAX_CANDIDATE_DISTANCE_M` covering the six-county
metro). The name stayed "Naper Kids" since renaming touches a lot of
surface area for a personal project; revisit if that starts being
confusing. No build system beyond a tiny Python script — this stays plain
HTML/CSS/JS on purpose so it keeps working as one portable, offline-capable
file.

## How the pieces fit together

- **`venues.json`** — the actual content. `venues` is the curated list (65
  entries as of Sep 2026: id, name, category, lat/lng, address, rating, phone, website,
  hours, cost, age, note, plus `place_id` once the updater has matched it
  to Google). Also hand-curated, and always optional (missing = the
  default): `season` (`"year-round"` (default) / `"summer"` / `"winter"` /
  `{"from": M, "to": M}`, generous month ranges — see 1.1 in ROADMAP.md),
  `tags` (fixed vocabulary — `restrooms`, `fenced`, `shade`, `stroller`,
  `food`, `water-play`, `picnic`, `parking`), `indoor` (`true` /
  `"partly"` / omitted for outdoor), and `kids_menu` (see below; *required*
  for the `Restaurants` category, optional for anything else). `candidates` is a holding pen for
  places the updater found that nobody has curated yet; the page ignores
  it. This is what changes most often.
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
  hand-curated `note`, `hours`, `cost`, `age`, `season`, `tags`, `indoor`,
  or `kids_menu` fields; it only refreshes rating/address/phone/website/lat/lng, and only
  when Google actually returns a value. Google results are matched to
  existing venues by `place_id`, then by id slug, then by "within 150 m and
  names mostly overlap" (see `MATCH_RADIUS_M` / `MATCH_NAME_SCORE`).
  Unmatched results go to `candidates`, except second Google listings of an
  already-matched venue and anything beyond `MAX_CANDIDATE_DISTANCE_M`
  (~55 mi, covering the Chicago six-county metro) from `CENTER`, which are
  dropped. Google's raw formatting is
  tidied on the way in (`clean_*` helpers): no trailing ", USA", phones as
  `(630) 555-1234`, `utm_*` stripped from websites, coordinates rounded to
  7 decimals. Keep hand-entered data in those same shapes so diffs stay
  quiet.
- **`test_update_venues.py`** — runs the updater against a fake Places API
  on a temp copy of the data and asserts nothing curated is lost or
  duplicated. Stdlib only. Run it after any change to the updater.
- **`check_data.py`** — validates `venues.json`: required fields present,
  ids unique clean slugs, coordinates within ~90 km of `center`, rating in
  0–5, `season`/`tags`/`indoor` restricted to their vocabularies, and
  `kids_menu` well-formed (http(s) `url`, `checked` date, non-empty sections
  and items, no unknown keys — so a typo like `prise` fails loudly instead of
  silently not rendering; every `Restaurants` venue must have one). Only
  checks `venues`, not `candidates` (those are allowed to be incomplete).
  Runs in the weekly workflow right before `build.py` so a bad hand edit
  never gets baked into `index.html`; also worth running by hand after
  editing `venues.json`.
- **`ROADMAP.md`** — prioritised ideas with the data fields each one needs.
  Check it before adding fields to `venues.json` so new work lines up with
  what's planned; tick items off there as they land.
- **`.github/workflows/update-venues.yml`** — GitHub Actions job that runs
  `update_venues.py`, then `check_data.py`, then `build.py` every Monday
  and commits both `venues.json` and the rebuilt `index.html`. Skips itself
  if the `GOOGLE_PLACES_API_KEY` secret is missing. Because the bot commits
  `index.html`, always `git pull` before local work; if `index.html` ever
  conflicts, don't merge it by hand — run `build.py` and take that.

## Workflow

```bash
# after hand-editing venues.json:
python3 check_data.py

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
- **The phone layout (≤ 860px) is a different UI, not just a squeezed
  desktop.** A sticky `.appbar` holds the search box and a **Filters**
  button (with an active-count badge); the three `.toolbar`s live in
  `#filterPanel`, which is inline on desktop and a full-screen sheet on
  phones; a floating pill (`#btnViewSwitch`) flips List/Map; in map view the
  header/footer hide and the map fills the screen under the bar. Gotchas:
  - There is one `.search-wrap`; `placeSearch()` moves it between the header
    (desktop) and `#appbar` (phone), also on breakpoint change. `isMobile()`
    mirrors the CSS 860px breakpoint — change them together.
  - Call `applyFilters()` (not `refresh()`) from anything that changes the
    set of places (filters, sort, search): it also scrolls the page back to
    the top on phones. Star/vote handlers keep using `refresh()` so the page
    doesn't jump. `showView()` remembers `listScrollY` so leaving the list for
    the map and coming back lands in the same spot.
  - Links inside a card must stop click propagation (the card's own click
    handler used to flip the phone to the map). On phones a tap on the card
    body only highlights it; the "On map" button is the way to the map.
  - Tap targets are 44px and inputs 16px (stops iOS zooming on focus) in the
    `(max-width: 860px), (pointer: coarse)` block, so they also apply to an
    iPad in landscape.
  - The sheet and sticky bar use z-indexes (500/600/2000) that Leaflet's own
    (up to 1000) would otherwise beat — `#map{position:relative;z-index:0}`
    keeps the map in its own stacking context. Keep that line.
  - The List/Map pill is lifted in map view so it doesn't cover Esri's
    attribution line, which their terms require us to show.
- **Map pins are clustered via `leaflet.markercluster`** (cdnjs, next to
  Leaflet). If it fails to load the page falls back to plain pins
  (`L.layerGroup`), so it degrades the same way the tiles do. Selecting a
  venue goes through `focusVenue()`, which zooms to `FOCUS_ZOOM` and lets
  the cluster layer unfold the pin before opening its popup — don't call
  `marker.openPopup()` directly, a clustered pin has no map to open on.
- **Favorites and "Best age?" votes are per-browser only** (`localStorage`
  keys `naperkids_favs_v1` and `naperkids_votes_v1`, no backend). This was
  an explicit choice to avoid standing up a server. A Google Sheets + Apps
  Script "web app" endpoint was discussed as the upgrade path if real
  cross-visitor shared voting is wanted later — not built yet.
- **"Near me" needs a secure context** for `navigator.geolocation`: fine on
  GitHub Pages (https), `localhost`, and `file://` in current browsers. The
  button hides itself if the API is missing; permission errors show in the
  status line under the toolbar.
- **Kids menus are copied by hand from the restaurant's own site, never
  guessed.** Shape: `kids_menu: {url, checked, summary?, sections: [{title?,
  note?, items: [{name, price?, desc?}]}]}` — `url` is the restaurant's own
  menu page (shown as "Full menu →"), `checked` is the YYYY-MM-DD you copied
  it (shown on the card — menus rot, so keep it honest), and `price`/`desc`
  are optional because some chains (Culver's, Portillo's) don't post kids'
  prices. Don't trust listicles or search-result summaries for *which*
  restaurants have kids menus: while seeding the first four, aggregator
  results put 2Toots in Naperville (it's Bartlett/Glen Ellyn), listed
  Everdine's (closed 2020), and Lou Malnati's has no dedicated kids menu.
  What worked: Next.js sites embed the menu as JSON in `__NEXT_DATA__`
  (Ramsay's, Culver's locations); Egg Harbor's site 403s curl but renders in a
  real browser. Coordinates come from the restaurant's own page when it
  publishes them, otherwise the US Census geocoder (keyless). In the page,
  `menuHtml()` renders it as a "Kids menu" `<details>` on the card (open
  state kept in `openMenus` like `openVotes`; the click must not bubble to the
  card), search also matches menu item names/descriptions
  (`menuSearchText()`), and a place that matched *only* through its menu opens
  that menu automatically (`matchedOnlyByMenu()`) so it's clear why it showed.
  The `Restaurants` category has its own search in `update_venues.py`, but
  Google can't say what's on a kids menu, so results only ever land in
  `candidates` until someone adds a `kids_menu`.
- **`cost` and `age` are hand-researched fields** — the Places API returns
  neither, so `update_venues.py` is written to never overwrite them. Same
  goes for `season`, `tags`, and `indoor`.
- **A CSS class that sets `display` beats the browser's own `[hidden]`
  rule.** `.chip{display:inline-flex}` silently overrode `hidden` on any
  chip (this bit the out-of-season toggle, and had been quietly true of
  the "Near me" button's no-geolocation case too). Fixed with a blanket
  `[hidden]{display:none !important;}`, kept near the top of the
  stylesheet — keep it there if you add more elements that toggle
  `hidden` from JS.
- **The rainy-day hint calls Open-Meteo** (`api.open-meteo.com`, keyless,
  no key/quota to manage) for today's precipitation chance at `center`.
  It's wrapped in try/catch with a 5s abort timeout, so it fails silent on
  `file://`, offline, or if that host ever changes terms — same posture as
  the map tiles, just lower stakes since the page works fine without it.

## Not yet done

- Pushed to a private GitHub repo (`origin` = github.com/yijiang1/naper-kids,
  branch `main`). The `GOOGLE_PLACES_API_KEY` secret is set and the weekly
  workflow has run successfully against the real API (first run
  2026-09-18: 19 of 22 venues refreshed; Winding Creek Park, DuPage
  Children's Museum and Urban Air weren't in Google's top results, which is
  fine — they just keep their existing data).
- The `candidates` list was fully reviewed and cleared in the Sep 2026
  content pass (ROADMAP.md 2.1/2.2): 26 promoted into `venues`, 18 low-value
  ones deleted (duplicate library branches, a little free library, generic
  distant pools, redundant bowling alleys), plus 13 brand-new Chicago-area
  landmarks hand-added (Shedd Aquarium, Field Museum, Griffin Museum of
  Science and Industry, Lincoln Park Zoo, Chicago Children's Museum,
  Chicago Botanic Garden, Adler Planetarium, Peggy Notebaert Nature Museum,
  LEGOLAND Discovery Center, Naper Settlement, Cantigny Park, Fermilab's
  Lederman Science Center, Phillips Park Zoo). `candidates` is empty until
  the next automated run finds more. Hours/prices for all of these were
  researched, not guessed, but weren't independently re-verified by a human
  after the fact — worth a spot-check before relying on the pricier/less
  obvious ones (Morton Arboretum and Ball Factory in particular have no
  fixed per-visit price, so `cost` says "Check website" for those).
- Shared (cross-visitor) voting was discussed but intentionally not built.
- Not yet hosted anywhere. GitHub Pages setup is documented in README.md
  but hasn't been done; note that Pages on a *private* repo needs a paid
  GitHub plan, so it may need to be made public first.
- Cosley Zoo's `note` says "~$8 admission" while its `cost` says $12 — one
  of them is stale; check the zoo's site.
