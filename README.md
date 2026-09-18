# Naper Kids

A personal dashboard of kid-friendly places in Naperville, IL — parks, splash
pads, museums, libraries, nature centers, bowling/arcades, and forest preserve
trails. List view + map view, filterable by category, age, and cost,
searchable by name, note, or address.

## Use it right now

Just open `index.html` in a browser (double-click it). It works completely
offline, using the data already saved in the file — no setup needed. The
footer shows when the data was last refreshed; places don't move often, but
hours and new spots will drift out of date over time.

Things you can do on the page:

- **Filter** by category, by the age of your kids, or free-only; **search**
  by name, note, or address (e.g. "aurora" or a zip code).
- **★ Favorites** — tap the star on a card to save it, then use the
  Favorites chip to see just those.
- **📍 Near me** — sorts everything by distance from where you are and shows
  the miles on each card. The browser will ask for location permission the
  first time.
- **Sort** by rating or name.
- **Best age?** — vote on which age a place suits best.

Favorites and votes are stored in the browser you're using, not shared —
open the page on another phone and they won't be there.

## Keep it updated automatically (optional)

The static file above won't update itself. If you want it to, here's the
lightweight path:

### Option A — run the updater by hand, whenever

No hosting required.

1. Get a free Google Places API key:
   https://developers.google.com/maps/documentation/places/web-service/get-api-key
   — enable **"Places API (New)"** on the project.
2. In a terminal, in this folder:
   ```
   export GOOGLE_PLACES_API_KEY="your-key-here"
   python3 update_venues.py
   python3 build.py
   ```
   The first command refreshes `venues.json`; the second bakes the new data
   into `index.html` so the double-click copy sees it too (a page opened
   straight from disk can't read `venues.json` next to it, so it relies on
   what's baked in).
3. Re-open `index.html`.

Run this every so often — monthly is plenty for how often parks and museums
change.

### Option B — host it so it updates itself on a schedule

1. Create a free GitHub account if you don't have one, and a new repository.
2. Upload everything in this folder to that repository (including the
   hidden `.github` folder — that's the automation).
3. In the repo: **Settings → Pages → Deploy from a branch → main → /(root)**.
   GitHub gives you a URL like `https://yourname.github.io/naper-kids/`.
4. In the repo: **Settings → Secrets and variables → Actions → New repository
   secret**, name it `GOOGLE_PLACES_API_KEY`, and paste in your key from
   Option A step 1.
5. That's it. The included workflow (`.github/workflows/update-venues.yml`)
   runs every Monday, re-fetches the data, rebuilds `index.html`, and
   commits both if anything changed. Your hosted page always reads the
   live file, so it stays current without you doing anything. You can also
   trigger it manually any time from the repo's **Actions** tab.

## Customizing

- **Add a place by hand:** open `venues.json` and add an entry to `venues` —
  copy the shape of an existing one. No API key needed for this. Then run
  `python3 build.py`.
- **Your notes are safe:** the updater only ever changes a venue's rating,
  address, phone, website, and coordinates. It never removes a venue, never
  changes its category or name, and never touches `note`, `hours`, `cost`,
  or `age`. Places Google finds that aren't in your list yet are parked in a
  separate `candidates` list at the bottom of `venues.json` — the page
  ignores them. To add one, move it up into `venues` and fill in the
  hand-written fields; to drop one, delete it. Places more than ~25 miles
  from Naperville and duplicate Google listings of a venue you already
  have are filtered out automatically.
- **Change what gets searched:** edit the `CATEGORIES` dict near the top of
  `update_venues.py` (each entry is a category name → a search phrase).
- **Change the search area:** edit `CENTER` and `RADIUS_METERS` in the same
  file.
- **Change how often it updates:** edit the `cron` line in
  `.github/workflows/update-venues.yml` ([crontab.guru](https://crontab.guru)
  is handy for this).

## Files in here

| File | What it's for |
|---|---|
| `index.html` | The dashboard itself — open this |
| `index_template.html` | The actual source (markup/CSS/JS) — edit this, not `index.html` |
| `venues.json` | The data the dashboard reads |
| `build.py` | Regenerates `index.html` from the two files above |
| `update_venues.py` | Refreshes `venues.json` from Google Places |
| `test_update_venues.py` | Checks the updater can't lose your hand-written data (no key needed) |
| `CLAUDE.md` | Dev notes — architecture, constraints, what's not done yet |
| `ROADMAP.md` | Ideas and planned features, in priority order |
| `.github/workflows/update-venues.yml` | Runs the script on a schedule if hosted on GitHub |

## Developing further

The page itself lives in `index_template.html`, not `index.html` — the
latter is generated. After changing `index_template.html` or `venues.json`,
run:

```bash
python3 build.py
```

To check it in a browser the way it'll behave when hosted:

```bash
python3 -m http.server 8000   # then visit http://localhost:8000
```

After touching `update_venues.py`, run `python3 test_update_venues.py`.

See `CLAUDE.md` for the fuller architecture notes and known rough edges.
