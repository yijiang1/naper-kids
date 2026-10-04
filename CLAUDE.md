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

- **`venues.json`** — the actual content. `venues` is the curated list (89
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
  it. This is what changes most often. A third list, `care`, holds the
  **Kids' care** providers (see below): hand-researched, never searched
  for by category; the updater looks each entry up by name + address
  (`refresh_care()`, accepted only within `CARE_MATCH_RADIUS_M` with a
  `CARE_MATCH_NAME_SCORE` name overlap) and fills in only `place_id`,
  `rating` and `rating_count`. Google's phone/address/website are never
  copied onto care entries (they disagreed with the providers' own sites);
  care results never become candidates.
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
  `kids_menu` well-formed (and, separately, the `care` list — see the Kids'
  care bullet below) (http(s) `url`, `checked` date, non-empty sections
  and items, no unknown keys — so a typo like `prise` fails loudly instead of
  silently not rendering; every `Restaurants` venue must have one). Only
  checks `venues`, not `candidates` (those are allowed to be incomplete).
  Runs in the weekly workflow right before `build.py` so a bad hand edit
  never gets baked into `index.html`; also worth running by hand after
  editing `venues.json`.
- **`CARE.md`** — the Kids' care research log (source conflicts, gaps on
  first-party pages, leads, backlog). Same idea as `RESTAURANTS.md`: update it
  when you add or rule out a provider.
- **`RESTAURANTS.md`** — the restaurant research log: confirmed "no kids menu"
  verdicts, closed/not-in-Naperville dead ends, leads that need another
  attempt, and a backlog. Not read by any script; it exists so research isn't
  repeated. Update it whenever a restaurant is added, ruled out, or retried.
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
- **Page width is one CSS variable, `--page-w` (1680px, in `:root`).** The
  header, toolbars, banners and footer all use it, so they stay aligned;
  change it there rather than per container. (On desktop the map itself is
  *not* bound by it — see the next bullet.) The footer's paragraphs are capped
  at 900px so the fine print stays readable.
- **Desktop (> 860px) is map-first: no list, the card opens in the map.**
  `#list` is `display:none` there and the map runs edge to edge
  (`@media (min-width: 861px)` block, before the phone block). The same
  `buildCard(v, inPopup)` that makes the phone's list cards is the content of
  the Leaflet popup (`renderMarkers()` binds `() => buildCard(v, true)`; phones
  open it as a bottom sheet instead, see the phone-layout bullet). Things that
  bit while building it:
  - **Don't rebuild the pins unless the set of places changed.** Starring or
    voting calls `refresh()`; `renderMarkers()` now returns early when the
    visible ids are unchanged (and the layout hasn't flipped between phone and
    desktop), so the open popup survives. `refreshOpenPopup()` then calls
    `popup.update()` to redraw the card in place, keeping its scroll position.
    A filter/search that changes the set still closes the popup — expected.
  - Leaflet gives popup `<p>`s a 1.3em margin that beats the card's single-class
    rules; the `.card-popup .card .card-name/.card-note/.menu-sum/.menu-foot`
    overrides undo that. New `<p>` classes inside a card need the same.
  - A tall card scrolls inside the popup (`max-height:var(--popup-max)`, set from
    the map's height in `updatePopupMax()`); opening the kids menu or "Best age?"
    calls `keepPopupInView()` (`map.panInside`) so the title isn't pushed off the
    top. Leaflet's own `maxHeight` option isn't used because it only measures
    when the popup opens, not when a `<details>` grows.
  - Selection follows the popup (`popupopen`/`popupclose` → `selectVenue`), not
    the other way round. Tooltips (pin name on hover) are unbound while a popup
    is open because Leaflet re-opens them on click. The "nothing matches"
    message floats over the map (`#mapEmpty`) since there's no list to hold it.
  - `popupAnchor` (-20) is sized for the 1.5x selected pin; change them together.
  - "Sort" is hidden on desktop (nothing to sort); "Near me" instead centers the
    map on you (if you're within 60 mi of `center`).
  - **The filters are a dropdown over the map, not rows above it.** A floating
    `#mapBar` (top-left, clear of Leaflet's zoom buttons) holds a **Filters**
    button with the active-count badge, the three "Where" chips and the result
    count; the button toggles `#filterPanel`, which is the *same element* as the
    phone's full-screen sheet (it lives inside `<main>` so it can be positioned
    over the map). It stays open while you pick filters and closes on Esc, ×, the
    button, a click on empty map, or a place card opening (`closeFilters(false)`
    skips the focus-return). `openFilters()` only locks page scroll and sets
    `aria-modal` on phones. The area chips are rendered twice (`#areaChips` in the
    panel, `#areaBar` in the bar) and `#areaToolbar` is hidden on desktop, so
    only one set shows per layout; `refresh()` updates both badges
    (`#filterBadge` phone, `#filterBadgeDesk`). The map is `--map-h` tall
    (`max(560px, 100vh - 150px)`) so it fits under the ~170px header.
  - Popups leave room for the bar: `autoPanPaddingTopLeft` top is 76 and
    `keepPopupInView()` / `updatePopupMax()` allow for it. If the bar gets
    taller, change those numbers too.
- **The phone layout (≤ 860px) is a different UI, not just a squeezed
  desktop.** A sticky `.appbar` holds the search box and a **Filters**
  button (with an active-count badge); the `.toolbar`s live in
  `#filterPanel`, which is a dropdown over the map on desktop and a
  full-screen sheet on phones; a floating pill (`#btnViewSwitch`) flips List/Map; in map view the
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
  - **The phone's map view is the desktop idea scaled down.** Tapping a pin
    doesn't open a Leaflet popup (a 380px bubble doesn't fit a 390px screen);
    `renderMarkers()` wires `marker.on('click')` to `openMapCard()`, which fills
    `#mapCard` with the same `buildCard(v, true)` and slides it up over the bottom
    of the map. `keepPinAboveCard()` pans so the pin sits in what's left (above
    the sheet; beside it when the card is docked left on a small tablet >= 600px
    or right on a phone in landscape, per the CSS) and is also what
    `keepPopupInView()` does when a menu opens. The card closes with the x,
    Esc, a tap on empty map, a downward drag on its handle, leaving for the list,
    or any change to the set of places (the map re-fits then). While it's open
    the List/Map pill is hidden (`body.card-open`). Don't call `marker.openPopup()`
    on a phone; there's no popup bound.
  - The three "Where" chips float over the top of the phone's map in the same
    `#mapBar` the desktop uses (Filters button and count hidden, since the sticky bar
    has them), with the Leaflet zoom buttons pushed to `top:56px` beneath. They
    carry two labels (`.long`/`.short`; "Naperville", "+ Neighbors", "Chicago area"
    under 520px) because the full wording is wider than a 360px phone. The row
    is `pointer-events:none` except for the chips so it doesn't eat map drags.
  - In Kids' care the 911 note is squeezed to one line in map view
    (`--care-h`) and the map is shortened by it. Before that the map overflowed
    the screen by the banner's height, which hid the attribution and the card.
    `#mapEmpty` (nothing matches) is shown over the phone map too.
- **Map pins are clustered via `leaflet.markercluster`** (cdnjs, next to
  Leaflet). If it fails to load the page falls back to plain pins
  (`L.layerGroup`), so it degrades the same way the tiles do. Selecting a
  venue goes through `focusVenue()`, which zooms to `FOCUS_ZOOM` and lets
  the cluster layer unfold the pin before opening its popup — don't call
  `marker.openPopup()` directly, a clustered pin has no map to open on.
  Each pin is a category-colored circle with a white inline-SVG glyph
  (`CATEGORY_ICONS`, next to `CATEGORY_COLORS` in the template; 24x24 box,
  stroke-based, styled by `.pin svg`). A new category needs an entry in both
  maps — without an icon it falls back to a plain dot. Glyphs were checked at
  the real 14px size, where fine outlines turn to mush (a stroked pine tree
  read as a triangle, so it's filled).
- **Kids' care is a second mode of the same page, not a second page.**
  `venues.json` has a `care` array (10 entries as of Oct 2026: 4 hospital
  ERs, 2 urgent care, 4 pediatric dentists); the "Places to go" / "Kids' care"
  tabs under the title call `setMode()`, which swaps `allVenues` between
  `placesData` and `careData`, clears the filters and search, re-renders the
  chips, list and map, and writes `#care` into the URL (`hashchange` is
  honored too). The tabs hide themselves if there's no `care` list (e.g. an
  older hosted `venues.json`). The list/map/filter code is shared; what
  differs: `.places-only` controls (free toggle, indoor, out-of-season, age
  chips, rain hint, the places footer) are hidden in care mode via
  `body.mode-care`, `.care-only` ones (911 banner, care footer) show only
  there; tags use `CARE_TAG_LABELS` instead of `TAG_LABELS` (`tagLabels()`);
  cards get a Call button (`telHref()`), insurance and "Checked <date>"
  lines, a star rating with the review count that links to the place's Google
  page when it has a `place_id` (`ratingHtml()`; the count is shown for care
  only for now — ROADMAP 2.3 would extend it to places), and no "Best age?" votes; search also matches `insurance` and the tag
  labels in care mode only. Care entries have different required fields than
  venues (`phone`, `website`, `checked` required; no `cost`/`age` needed) —
  `check_data.py`'s `check_care()` enforces them, a fixed category list
  (`Hospitals & ER`, `Urgent Care`, `Pediatric Dentists`), the tag vocabulary
  (`CARE_TAG_VOCAB`, keep in step with `CARE_TAG_LABELS`) and that ids don't
  collide with `venues`. Ids are shared across both lists, since favorites are
  keyed by id. A new care category needs entries in `CATEGORY_COLORS` and
  `CATEGORY_ICONS`.
  **Medical data rules:** every fact comes from the provider's own site and
  `checked` is the day it was read; leave a field out rather than guess
  (insurance in particular — only set where a page said something concrete).
  Directories were wrong on first contact (Small Smiles' address, Tic Tac
  Tooth's phone), so use them only to find leads. The page carries a "call
  911" banner and a not-medical-advice footer in care mode; keep both.
  See `CARE.md` for conflicts, gaps and leads.
- **The "Where" filter is three nested rings, not a stored field.** `AREAS` /
  `inArea()` in the template: *Naperville only* = the address says
  `, Naperville, IL`; *Naperville + neighbors* = that, or within
  `AREA_NEAR_MILES` (15) of `center`; *Greater Chicago area* = everything, and
  it's the unfiltered default (so it doesn't count toward the filter badge).
  It's by address city rather than radius on purpose — Naperville's limits are
  ragged (Tic Tac Tooth is Naperville at 5.4 mi, IHOP is Aurora at 2.7 mi),
  and a hand-entered `address` is already required. Consequence: a venue's
  address must keep the `City, IL` shape (see the `clean_*` notes above) or
  it falls through to the radius test. 15 mi sits in the empty stretch between
  Blackberry Farm (12.3) and St. Charles (15.7); recheck it if venues land in
  that gap. It applies in both modes (care providers have addresses too) and
  resets with the other filters on a mode switch.
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

  The 13 chains (Texas Roadhouse, Cheesecake Factory, Chili's, Chick-fil-A,
  McDonald's, Red Robin, Buffalo Wild Wings, Noodles & Co, Cooper's Hawk,
  Lazy Dog, Panera, Wendy's, Cracker Barrel) were added as **one location per
  chain, the one nearest downtown Naperville** — a dozen identical McDonald's
  cards would just be noise. Their kids menus are the chains' national lists,
  mostly without prices (each entry says so); Lazy Dog, Cooper's Hawk and
  Egg Harbor/Ramsay's post prices. Phone and hours are included only when the
  chain's own location page published them.

  A second batch (same day) added 11 more — Outback, IHOP, MISSION BBQ,
  Steak 'n Shake, McAlister's, Smashburger, Rock Bottom, Uncle Julio's, Honey
  Berry, Home Run Inn and Colonial Cafe — for 28 restaurants in all. Same
  rules, plus what that batch taught: many chains build their menu only after
  you pick a store, so open the *store-specific* menu URL in the browser (Outback:
  `/menu/naperville/category/<id>`; Rock Bottom's Popmenu site: the "Kid's
  Menu" tab, then "Show all items"); some publish a printable PDF or an image
  (McAlister's, Steak 'n Shake, Colonial Cafe) — render PDF pages to PNG with
  PDFKit and *look* at them, because extracted PDF text interleaves columns.
  Never push through a CAPTCHA or bot wall (Red Lobster's ShieldSquare): log
  it in RESTAURANTS.md and move on.

  **`RESTAURANTS.md` is the research log: read it before researching a
  restaurant, and keep it current.** It records what's *not* on the page —
  the one confirmed "no kids menu" (Lou Malnati's), places that aren't (or
  are no longer) in Naperville (2Toots, Everdine's), the leads that do have a
  kids menu but couldn't be read yet (Olive Garden, Maggiano's, Giordano's,
  Panda Express, Jason's Deli, Denny's, Chipotle, Dairy Queen, Red Lobster,
  Biaggi's, ...) with what to try next, a not-yet-researched backlog, and how the research was done
  (OpenStreetMap pool, per-chain verification, PDF text via macOS PDFKit).
  Two lessons from it worth repeating here: OpenStreetMap has stale entries,
  so confirm every store on the chain's own page, and the Census geocoder can
  return the wrong ZIP (McDonald's 516 N River Rd: geocoder 60563, the
  chain's own page 60540), so take address details from the chain.
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

- Pushed to a **public** GitHub repo (`origin` = github.com/yijiang1/naper-kids,
  branch `main`; these notes used to say "private", but `gh repo view` reports
  public as of 2026-10-03, so assume everything committed and every Actions
  log is world-readable). The key is never in the repo: `GOOGLE_PLACES_API_KEY` is only
  an Actions secret (and the script sends it in a header, so it can't leak via
  a URL); keep it that way, and restrict the key to "Places API (New)" in
  Google Cloud (not verified that it is). The secret is set and the weekly
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
  Lederman Science Center, Phillips Park Zoo). The weekly runs have since
  refilled `candidates` (178 unreviewed entries as of 2026-10-03), so another
  review-and-clear pass is due; the page ignores them meanwhile. Hours/prices for all of these were
  researched, not guessed, but weren't independently re-verified by a human
  after the fact — worth a spot-check before relying on the pricier/less
  obvious ones (Morton Arboretum and Ball Factory in particular have no
  fixed per-visit price, so `cost` says "Check website" for those).
- Shared (cross-visitor) voting was discussed but intentionally not built.
- **Hosted on GitHub Pages** at https://yijiang1.github.io/naper-kids/ (legacy
  "deploy from a branch": `main`, `/`, HTTPS enforced; checked 2026-10-04, the
  latest build matched the latest commit). Every push to `main`, including the
  Monday bot commit, rebuilds it in under a minute. Because it's served over
  https the page fetches `./venues.json` live rather than using the baked-in copy.
- Cosley Zoo's `note` says "~$8 admission" while its `cost` says $12 — one
  of them is stale; check the zoo's site.
