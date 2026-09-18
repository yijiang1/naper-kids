# Naper Kids

A personal dashboard of kid-friendly places in Naperville, IL — parks, splash
pads, museums, libraries, nature centers, bowling/arcades, and forest preserve
trails. List view + map view, filterable by category, searchable.

## Use it right now

Just open `index.html` in a browser (double-click it). It works completely
offline, using the data already saved in the file — no setup needed. This is
a snapshot from **September 12, 2026**; places don't move often, but hours
and new spots will drift out of date over time.

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
   ```
3. Re-open `index.html`. It will pick up the refreshed `venues.json`
   automatically (it tries to load that file first, and only falls back to
   the snapshot baked into the page if it can't find it).

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
   runs every Monday, re-fetches the data, and commits `venues.json` if
   anything changed. Your hosted page always reads the live file, so it
   stays current without you doing anything. You can also trigger it
   manually any time from the repo's **Actions** tab.

## Customizing

- **Add a place by hand:** open `venues.json` and add an entry — copy the
  shape of an existing one. No API key needed for this.
- **Change what gets searched:** edit the `CATEGORIES` dict near the top of
  `update_venues.py` (each entry is a category name → a search phrase).
- **Change the search area:** edit `CENTER` and `RADIUS_METERS` in the same
  file.
- **Your notes are safe:** re-running the updater keeps whatever you've
  written in a venue's `note` and `hours` fields — it only refreshes rating,
  address, phone, and website.
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
| `CLAUDE.md` | Dev notes — architecture, constraints, what's not done yet |
| `.github/workflows/update-venues.yml` | Runs the script on a schedule if hosted on GitHub |

## Developing further

The page itself lives in `index_template.html`, not `index.html` — the
latter is generated. After changing `index_template.html` or `venues.json`,
run:

```bash
python3 build.py
```

See `CLAUDE.md` for the fuller architecture notes and known rough edges.
