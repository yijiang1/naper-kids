# Restaurant research log

What's here: everything learned about which Naperville-area restaurants have a
kids' menu **that did not end up on the page** — the dead ends, the
"has one but I couldn't read it yet" leads, and the not-yet-checked backlog —
so nobody re-does the same digging. Restaurants that did make it live in
`venues.json` (`"category": "Restaurants"`, 28 as of 2026-09-30: 17 in the
first pass, 11 in a second pass the same day).

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

## Looked at, found no kids' menu (weak evidence — only the landing page was checked)

For these I only counted the word "kid" in the raw HTML of the home or location
page. A menu that lives on another page, or inside an ordering app, would be
missed, so treat each as "probably none published", not proof.

| Restaurant | What was checked |
|---|---|
| Rosati's (406 W 5th Ave) | Location page: no mention. Look at its menu page before ruling out. |
| Jet's Pizza (720 E Ogden Ave) | Location page: no mention. |
| Freddy's (1967 Glacier Park Ave) | `freddys.com/menu/`: no mention (the ordering app wasn't opened). |
| Freedom Brothers, Fiammé, Kreger's, Sullivan's, Rocco's, Little Pops, Paisan's | Home pages: no mention. |
| Papa Ray's | Only a customer review ("bigger than our kids' faces"), no kids' menu. |
| Twin Peaks (Warrenville) | Menu page text had no "kid"; also a bar-style place, so skipped on purpose. |
| Hooters (Aurora) | `/menu/kids` came back empty; skipped on purpose (bar-style place). |
| Five Guys | Not opened. Known to size down ("Little" burgers) rather than have a kids' menu. |

## Not (or no longer) a Naperville restaurant, or not reachable

| Restaurant | Evidence |
|---|---|
| 2Toots Train Whistle Grill | Its own locations page lists only Bartlett and Glen Ellyn. An OpenTable listicle and OpenStreetMap still put it at 1567 N Aurora Rd, Naperville — probably closed; confirm by phone before ever re-listing. |
| Everdine's Grilled Cheese Co. | The downtown Naperville store (24 W Jefferson Ave) closed in July 2020 per local-news search results (not first-party). OpenStreetMap still lists it; a Batavia store remains. |
| Walker's Charhouse (8 W Gartner Rd) | `walkerscharhouse.com` now redirects to an unrelated gambling-spam site. Probably closed and the domain lapsed. **Don't visit it again.** |
| Pancake Cafe (1292 Rickert Dr) | `pancakecafenaperville.com` doesn't resolve (no DNS answer). Probably closed; confirm elsewhere. |
| Honey Berry — Warrenville store (28361 W Diehl Rd) | The listed `/warrenville/` page is a 404 and Honey Berry's own locations list has no Warrenville. OpenStreetMap is stale. The **Aurora** store (451 N Commons Dr) is the one on the page. |
| Houlihan's (2860 Showplace Dr) | One search result says the Naperville restaurant is permanently closed (not first-party, unverified). Its own store locator is a script-only page. Confirm before trying again. |
| Maggiano's Naperville (1847 Freedom Dr) | Its own `/locations/Illinois/Naperville/1847-freedom-drive` now answers 404 ("That page isn't on the menu"). Moved, renamed or closed — unverified. |

## Has a kids' menu (or probably does), but I couldn't read it yet (best leads)

| Restaurant (Naperville store) | What's known | Why it's blocked | Try next |
|---|---|---|---|
| Olive Garden (620 S State Route 59) | `olivegarden.com/kids` exists | `/menu/kids` shows nothing until a restaurant is chosen; the store page came up blank in the browser | Pick the Naperville restaurant via "Find a Restaurant", then read `/menu/kids` |
| Giordano's (119 S Main St, downtown) | A search summary says it has a kids' menu (unverified) | `orders.giordanos.com` is a script-only app that stays blank; the location page doesn't mention a kids' menu | Look for a PDF menu, or expand the kids' section of the ordering app |
| Panda Express (1123 E Ogden Ave) | Has the "Panda Cub Meal", three set meals | `pandaexpress.com/cub-meal` describes them but never names them | The nutrition-info page or the ordering menu may |
| Jason's Deli (1739 Freedom Dr) | Kids page lists Kids Pasta (chicken alfredo, or marinara & meatballs) and Kids Pizza (cheese or pepperoni) "and more" | The full menu sits on "Please wait. Loading content." and never finishes in the browser | Read the full menu at `jasonsdeli.com/menu` later, or find its PDF |
| Denny's (Route 59, Naperville) | Kids' menu exists (`dennys.com/kids-live-well`) | Blank page in the browser, 403 to scripts; the OpenStreetMap entry has no address | Find the real address first |
| Chipotle (22 E Chicago Ave, downtown) | Kids' meal exists (kid's quesadilla etc.) | Not completed; the only kids' menu found was a 2021 paper-menu PDF | Read the live order page |
| Dairy Queen (1002 N Washington St) | Kids' meals exist (item pages such as "2 Piece Chicken Strips – Kids") | 403 to scripts; no category page found | Assemble from the item pages |
| Shake Shack (404 S State Route 59) | **Unclear whether it has a dedicated kids' menu** — search found none | — | Check its menu; may belong in "Confirmed: no kids' menu" |
| Red Lobster (1036 N Route 59, Aurora) | Presumably has a kids' menu (not confirmed on its site) | Its site put up a ShieldSquare **CAPTCHA** ("you are a bot") on the first visit. Not attempted further — never push through a bot wall | Try again another day, or a printable PDF if one exists |
| Biaggi's (2752 Showplace Dr) | `biaggis.com/menus/` has a "Kids" tab | The Kids page loads but its body is empty (the menu isn't in the page text), and the site's API is behind a bot gate | Try a PDF, or phone the restaurant |
| TGI Fridays (888 N Route 59, Aurora) | — | `/menu` 404s; the only menu found is a May 2025 large-print PDF (too old to trust) | Wait for a current menu |
| Burger King (several stores) | Presumably has kids' meals (not confirmed on its site) | `bk.com/menu/kids` shows only a cookie banner | Browser with a longer wait, or its nutrition PDF |
| Arby's (296 S State Route 59) | Presumably has a kids' meal (not confirmed on its site) | The store page links to `/menu`, which is empty until a store is chosen | Pick the store, then open the kids' category |
| Nando's (6 W Jefferson Ave, downtown) | — | `nandosperiperi.com` answered 429 (rate limited) | Try later |

## Added without everything verified

- **Uncle Julio's (1831 Abriter Ct).** The kids' menu is read from its own
  dine-in menu page (which says options may vary by location), and the Naperville
  restaurant is confirmed by that page ("Not available in Naperville" under happy
  hour). But its location pages (`locations.unclejulios.com`) throw a Cloudflare
  "DNS points to prohibited IP" error on their end, so **phone, hours and the
  ZIP (60563, from the Census geocoder) are not from a first-party page.** Phone
  and hours were left off. A search summary quoted a phone and hours; they were
  not copied because they weren't read on a page. Retry the location page later.
- **Red Robin (Cantera, Warrenville)** — the store is confirmed on Red Robin's
  own site, but its street address (28260 W Diehl Rd) comes from OpenStreetMap +
  the Census geocoder, not from a Red Robin page.
- **Honey Berry Cafe (Aurora).** Its location page gives address and phone but
  no hours, and its menu page isn't store-specific.
- **Home Run Inn (Bolingbrook).** The kids' items are on that restaurant's
  location page; the Bolingbrook store is ~4.9 miles from downtown Naperville, so
  it's the one outside the city proper.

## Not researched yet

Names from the OpenStreetMap pool that are worth checking, roughly by how
likely a family is to want them: Fogo de Chão (Abriter Ct; it prices children
by age, so it may not have a "kids' menu"), First Watch, Golden Corral (kids are
priced by age on the buffet), Pitaville (403 to scripts), Sarpino's (500 error),
Blueberry Hill (Eola Rd), Chuck E. Cheese (its own page mentions kids 35 times,
but it's closer to an indoor play/arcade place — if it's ever added, it belongs
in "Bowling & Arcades" with its menu, not "Restaurants"). Also named by
listicles but not found in OpenStreetMap (so possibly closed or elsewhere): The
Egg & I, The Melting Pot, JoJo's ShakeBAR.

## How this research was done (so it can be repeated)

1. **Pool of restaurants.** OpenStreetMap's Overpass API (keyless; it answers
   406 unless you send a `User-Agent`):
   `[out:json];nwr["amenity"~"^(restaurant|fast_food)$"]["name"](41.70,-88.25,41.84,-88.07);out center tags;`
   gave 431 named places. **OpenStreetMap has stale entries** (2Toots,
   Everdine's, Walker's, Pancake Cafe, Honey Berry Warrenville above), so confirm
   each store on the chain's own site first.
2. **One location per chain**, the one nearest downtown Naperville
   (41.7723, -88.1480), unless there's a reason to pick another.
3. **Verify the address** against the chain's own location page. The Census
   geocoder (`geocoding.geo.census.gov`) is handy for ZIPs but can be wrong:
   it said McDonald's 516 N River Rd was 60563; McDonald's own page says 60540.
   It's also usually a few hundred metres off the pin, so prefer a restaurant's
   own latitude/longitude (JSON-LD on location pages) when it publishes one.
4. **Read the kids' menu on the chain's own page.** What worked:
   - Next.js `__NEXT_DATA__` JSON, and JSON-LD on location pages.
   - The built-in browser for script-built menus. Chili's needs a "View more"
     click; Texas Roadhouse's kids' menu is behind a tab on the per-location
     `digital-menu` page; **Outback** only shows a store-specific menu at
     `/menu/naperville` → `category/<id>` (wait a few seconds for it to load);
     **Rock Bottom** (a Popmenu site) needs its "Kid's Menu" tab, then "Show all
     items".
   - PDF menus: `osascript -l JavaScript` with macOS PDFKit gives the text
     (`pdftotext`/`pdftoppm` aren't installed), **but the text interleaves
     columns** (McAlister's, Steak 'n Shake). Render the page to PNG with PDFKit
     (`PDFPage.thumbnailOfSizeForBox`) and look at the picture to attach items to
     the right headings.
   - Image menus (Colonial Cafe's kids' menu is a JPG): download it and read it
     visually; `sips -g pixelWidth` shows the size.
   - Many sites 403/429 plain `curl`; the browser gets through. A quick `curl`
     that counts "kid" in the raw HTML is a cheap first filter.
5. **Don't copy prices that the page doesn't show.** Most chains' menu pages
   list no kids' prices; the card says so instead of guessing. When a price is
   shown on an online-ordering menu, say so in the entry's `summary` — it can
   differ in the dining room.
6. **Respect bot walls.** A CAPTCHA or "you are a bot" page (Red Lobster's
   ShieldSquare, Biaggi's anti-crawler API) is a stop sign, not a puzzle: log it
   here and move on.
7. **Search-result summaries are leads, not sources.** One quoted Uncle Julio's
   phone and hours that couldn't be confirmed on a page; others claimed
   Houlihan's Naperville is closed. Neither went on the page.
