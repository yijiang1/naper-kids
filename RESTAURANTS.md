# Restaurant research log

What's here: everything learned about which Naperville-area restaurants have a
kids' menu **that did not end up on the page** — the dead ends, the
"has one but I couldn't read it yet" leads, and the not-yet-checked backlog —
so nobody re-does the same digging. Restaurants that did make it live in
`venues.json` (`"category": "Restaurants"`, 17 as of 2026-09-30).

Dates are 2026-09-30 unless noted. **First-party** means the restaurant's own
website, never a listicle. Listicles and search-result summaries were wrong
often enough (see the second table) that they're only used to find *leads*;
nothing goes on the page until it's been read on the restaurant's own site.

Please keep this file current: when you add a restaurant to `venues.json`,
delete it from the tables below; when you rule one out, add it here with the
evidence.

## Confirmed: no kids' menu

| Restaurant | Evidence |
|---|---|
| Lou Malnati's (131 W Jefferson Ave downtown; 2879 95th St) | Zero mentions of "kid" or "child" in the raw HTML of its menu, home, FAQ and downtown-location pages. That only means no kids' menu is *published* — it says nothing about whether kids are welcome. Re-check if they ever add one. |

## Not (or no longer) a Naperville restaurant

| Restaurant | Evidence |
|---|---|
| 2Toots Train Whistle Grill | Its own locations page lists only Bartlett and Glen Ellyn. An OpenTable listicle and OpenStreetMap still put it at 1567 N Aurora Rd, Naperville — probably closed; confirm by phone before ever re-listing. |
| Everdine's Grilled Cheese Co. | The downtown Naperville store (24 W Jefferson Ave) closed in July 2020 per local-news search results (not first-party). OpenStreetMap still lists it; a Batavia store remains. |

## Has a kids' menu, but I couldn't read it yet (best leads)

| Restaurant (Naperville store) | What's known | Why it's blocked | Try next |
|---|---|---|---|
| Olive Garden (620 S State Route 59) | `olivegarden.com/kids` exists | `/menu/kids` shows nothing until a restaurant is chosen | In the built-in browser, pick the Naperville restaurant via "Find a Restaurant", then read `/menu/kids` |
| Maggiano's Little Italy (1847 Freedom Dr) | A search summary of maggianos.com says the kids' menu is for children 12 and under | The `/menus/<address>/kids menu/` URL 404s for this store | Start from the Naperville location page and click through to the menu |
| Giordano's (119 S Main St, downtown) | A search summary says it has a kids' menu (unverified) | `orders.giordanos.com` is a script-only app with no readable text | Look for a PDF menu, or expand the kids' section of the ordering app in the browser |
| Panda Express (1123 E Ogden Ave) | Has the "Panda Cub Meal", three set meals | `pandaexpress.com/cub-meal` doesn't name them | The nutrition-info page or the ordering menu may |
| Jason's Deli (1739 Freedom Dr) | Kids page lists Kids Pasta (chicken alfredo, or marinara & meatballs) and Kids Pizza (cheese or pepperoni) "and more" | Too thin to list faithfully | Read the full menu at `jasonsdeli.com/menu` |
| Denny's (Route 59, Naperville) | Kids' menu exists (`dennys.com/kids-live-well`) | Site returns 403 to scripts; the OpenStreetMap entry has no address | Browser, and find the real address first |
| Chipotle (22 E Chicago Ave, downtown) | Kids' meal exists (kid's quesadilla etc.) | Not completed; the only kids' menu found was a 2021 paper-menu PDF | Read the live order page in the browser |
| Dairy Queen (1002 N Washington St) | Kids' meals exist (item pages such as "2 Piece Chicken Strips – Kids") | 403 to scripts; no category page found | Browser, or assemble from the item pages |
| Shake Shack (404 S State Route 59) | **Unclear whether it has a dedicated kids' menu** — search found none | — | Check its menu in the browser; may belong in "Confirmed: no kids' menu" |

## Not researched yet

Names from the OpenStreetMap pool that are worth checking, roughly by how
likely a family is to want them: Rosati's (406 W 5th Ave; 1935 95th St), Nando's
(downtown), Home Run Inn (Bolingbrook), Fogo de Chão, Uncle Julio's, Biaggi's,
Houlihan's, Outback, Red Lobster, TGI Fridays, IHOP, First Watch, Hooters,
Twin Peaks, Mission BBQ, Freddy's, Steak 'n Shake, Five Guys, Smashburger,
Burger King, Golden Corral, McAlister's, Jet's Pizza, Pancake Cafe, Honey Berry
Pancakes, Blueberry Hill, Walker's Charhouse, Rock Bottom, Chuck E. Cheese,
Fiammé, Freedom Brothers, Kreger's. Also named by listicles but not found in
OpenStreetMap (so possibly closed or elsewhere): The Egg & I, The Melting Pot,
JoJo's ShakeBAR.

**Listed with a loose end:** Red Robin (Cantera, Warrenville) — the store is
confirmed on Red Robin's own site, but its street address (28260 W Diehl Rd)
comes from OpenStreetMap + the Census geocoder, not from a Red Robin page.

## How this research was done (so it can be repeated)

1. **Pool of restaurants.** OpenStreetMap's Overpass API (keyless; it answers
   406 unless you send a `User-Agent`):
   `[out:json];nwr["amenity"~"^(restaurant|fast_food)$"]["name"](41.70,-88.25,41.84,-88.07);out center tags;`
   gave 431 named places. **OpenStreetMap has stale entries** (2Toots,
   Everdine's above), so confirm each store on the chain's own site first.
2. **One location per chain**, the one nearest downtown Naperville
   (41.7723, -88.1480), unless there's a reason to pick another.
3. **Verify the address** against the chain's own location page. The Census
   geocoder (`geocoding.geo.census.gov`) is handy for ZIPs but can be wrong:
   it said McDonald's 516 N River Rd was 60563; McDonald's own page says 60540.
4. **Read the kids' menu on the chain's own page.** What worked: Next.js
   `__NEXT_DATA__` JSON, JSON-LD on location pages, the built-in browser for
   script-built menus (Chili's needs a "View more" click; Texas Roadhouse's kids'
   menu is behind a tab on the per-location `digital-menu` page), and for PDF
   menus `osascript -l JavaScript` with macOS PDFKit (`pdftotext`/`pdftoppm`
   aren't installed). Many sites 403/429 plain `curl`; the browser gets through.
5. **Don't copy prices that the page doesn't show.** Most chains' menu pages
   list no kids' prices; the card says so instead of guessing.
