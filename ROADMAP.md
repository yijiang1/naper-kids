# Naper Kids — roadmap

Ideas for making the dashboard better, roughly in order of payoff per hour.
The yardstick for everything here is one moment: *it's 2 pm on a Saturday,
where do we take the kids?* Anything that makes that answer faster or more
trustworthy ranks high.

Tick boxes as things land, and move finished items to **Done** at the
bottom. Each item notes the data it needs, because new fields are the part
that's hardest to change later — the page and the updater are cheap to
adjust, `venues.json` is hand-curated.

## At a glance

| # | Idea | Why it matters | Effort | Status |
|---|------|----------------|--------|--------|
| 1.1 | Season awareness | Stops suggesting splash pads in January | Small | ☑ |
| 1.2 | "Open now" from structured hours | Hours are the field that goes stale first | Medium | ☐ |
| 1.3 | Amenity tags + filters | "Fenced + toddler + free" is a real query | Medium | ☑ |
| 1.4 | Indoor flag + rainy-day chip | Instant answer on a wet day | Small | ☑ |
| 2.1 | Promote the good candidates | More places, same quality bar | Content | ☑ |
| 2.2 | Add well-known places Google missed | Arboretum, Naper Settlement, etc. | Content | ☑ |
| 2.3 | Show rating counts | 4.9 (12) ≠ 4.5 (2,000) | Small | ☐ |
| 2.4 | Seasonal farms / pumpkin patches | Fall-specific content, `season` field already exists | Content | ☐ |
| 2.5 | Restaurants with kids menus | "Where can we eat?" is half of every outing | Medium | ☑ |
| 2.6 | More restaurants (and re-check the 4 existing menus) | Seeded with 4 verified places; sit-down chains still missing | Content | ☐ |
| 3.1 | Filters + selected place in the URL | Text a link to your spouse | Small | ☐ |
| 3.2 | Saved home location | Distance sort without a GPS prompt | Small | ☐ |
| 3.3 | "Been there" log + surprise me | Remember, and break ties | Small | ☐ |
| 4.1 | Data validation in tests/workflow | Catches hand-edit slips for free | Small | ☑ |
| 4.2 | Dark mode | Bedtime planning | Small | ☐ |
| 4.3 | Weekly link check | Dead websites get noticed | Small | ☐ |

**Landed:** 2.5 (restaurants + kids menus, Sep 30 2026), after 1.1 + 1.3 + 1.4 + 4.1, then 2.1 + 2.2 (see Done — that pass also
widened the whole project's scope from Naperville-only to the greater
Chicago metro area, ahead of schedule relative to this list's original
ordering). **Next up:** 1.2, then 2.3, then the sharing conveniences (3.x).

---

## 1. Trustworthy on the day

### 1.2 "Open now" from structured hours

**Problem.** `hours` is free text. It reads well but can't be checked, and
it's the most likely field to drift. Half the value of the page is knowing
a place is open *right now*.

**Data.** Have `update_venues.py` request `places.regularOpeningHours` in
the same Text Search call it already makes. That field is in the same
pricing tier the script already uses (phone/website), so it costs nothing
extra. Store Google's periods in a new refreshable field and leave the
hand-written `hours` alone as the human-readable fallback:

```json
"hours_periods": [
  {"day": 0, "open": "0900", "close": "1700"},   // day: 0=Sun … 6=Sat
  {"day": 1, "open": "0700", "close": "2200"}
]
```

A place open 24 hours comes back as an `open` with no `close`; a place with
no data has no field at all.

**Page.** Compute status in the browser's local time:

- *Open now · closes 5 PM*
- *Opens 9 AM* (later today)
- *Closed today*
- Nothing, if there are no periods — the `hours` text still shows.

Add an **Open now** chip to the toolbar. Handle closes after midnight
(bowling alleys) by treating a `close` earlier than its `open` as next-day.

**Caveats.** Don't use Google's `currentOpeningHours`; it's only accurate at
fetch time. Parks often come back "open 24 hours" or with nothing — that's
fine, the hand text covers them. Holiday hours will be wrong; the footer
already says to double-check before going.

---

## 2. More places, better places

### 2.3 Show rating counts

Add `places.userRatingCount` to the field mask (same tier as `rating`),
store as `rating_count`, and render the card rating as `★ 4.5 (1.2k)`.
Optional: make the "Top rated" sort weight by count so a 4.9 with 12
reviews doesn't beat a 4.7 with 1,500.

### 2.4 Seasonal farms / pumpkin patches

Split off from the old 2.2 when that item landed — not researched yet.
Verify hours/prices before adding, same as any other content item; set
`season` (harvest season is roughly Sep–Oct for most) once real ones are
picked.

### 2.6 More restaurants, and keeping the menus fresh

2.5 shipped with four places whose kids menus were verified on the
restaurant's own site on 2026-09-30: Ramsay's Kitchen, Egg Harbor Cafe,
Culver's and Portillo's (Ogden Ave; the Jefferson St one is mentioned in its
note rather than listed twice). Texas Roadhouse, Giordano's, Red Robin and
Cooper's Hawk were tried and dropped — their sites block scripted fetches or
don't expose a Naperville page, so nothing could be verified; a browser
session with a location search would get through. Add more the same way (see
CLAUDE.md), and fill in the kids' prices for Culver's and Portillo's if they
ever post them. Each menu shows its `checked` date; a menu older than ~6
months is due a re-check. A soft warning in `check_data.py` for stale
`checked` dates would make that automatic.

---

## 3. Sharing and convenience

### 3.1 Filters and selected place in the URL

Mirror state into the hash, e.g.
`#cat=Splash+Pads+%26+Pools&age=toddler&free=1&place=knoch-park`.
Parse on load, update with `history.replaceState` on every change (no
history spam). A selected `place` opens with the card highlighted and the
popup open. Add a small **Copy link** action on the selected card.

Works from `file://` too, so a link can be pasted into a text message even
before the site is hosted.

### 3.2 Saved home location

"Near me" needs a location prompt every time and only works where the
browser allows geolocation. Add **Set home** (use the current location once,
or click a spot on the map) stored in `localStorage` as
`naperkids_home_v1`. Distance sort then works instantly from the couch;
"Near me" still overrides it when out and about.

### 3.3 "Been there" log and surprise me

- A **Been here** button per card, storing dates in
  `naperkids_visits_v1` (`{id: ["2026-08-03", …]}`). Card shows *Last
  visit: Aug 3*.
- Sort option **Longest since visit**.
- A **Surprise me** button that picks a random place matching the current
  filters and selects it. Cheap, and genuinely useful on indecisive days.

Same per-browser caveat as favorites and votes; the footer already says so.

---

## 4. Guard rails

### 4.2 Dark mode

Colours are already CSS variables, so this is a `prefers-color-scheme:
dark` block with darker values, plus swapping the Esri tile layer for its
keyless dark variant (`World_Dark_Gray_Base`) when dark. Keep the chip and
badge colours legible; check the map popup.

### 4.3 Weekly link check

In the workflow, after the updater: a HEAD request to each `website`,
printing any that return 4xx/5xx. Report only — don't change data. Cheap
way to notice a venue that quietly closed.

---

## Decided against (for now)

- **Photos from Google.** Photo URLs embed the API key, and committing
  images bloats the repo. Not worth it for a personal page.
- **Shared, cross-visitor voting.** Still the known upgrade path (Google
  Sheets + Apps Script, or a tiny Cloudflare Worker), but only matters if
  people outside the household use the page.
- **Any build tooling.** Stays a single HTML file plus two Python scripts.
- **Auto-refreshing the `hours` text from Google.** The hand-written text is
  more readable than Google's seven-line weekday list; 1.2 gives the
  structured version alongside it instead.

## Done

- Page fixed, favorites, near-me, sorting, address search, stable map
  (Sep 2026)
- Updater made safe for curated data; formatting normalised; candidates
  filtered; weekly workflow rebuilds `index.html` (Sep 2026)
- Season awareness (out-of-season toggle + badge), amenity tags + "Must
  have" filters, indoor flag + rainy-day hint, and `check_data.py`
  validation wired into the weekly workflow (Sep 2026)
- Restaurants with kids menus (Sep 30 2026): new `Restaurants` category and
  an optional `kids_menu` field (sections of items with optional prices and
  a link + checked date for the restaurant's own menu); a "Kids menu"
  fold-out on each card, search that matches menu items, `check_data.py`
  validation (required for restaurants), a Restaurants search in the
  updater, and an updater test proving `kids_menu` is never overwritten.
  Four verified restaurants to start (see 2.6)
- Content pass: reviewed all 44 candidates (26 promoted, 18 deleted), added
  13 new Chicago-proper landmarks, and widened the whole project's scope
  from Naperville-only to the greater Chicago six-county metro area —
  `update_venues.py`'s search radius/candidate cutoff and `check_data.py`'s
  distance check both widened accordingly, at no extra weekly API-call cost
  (Sep 2026)
