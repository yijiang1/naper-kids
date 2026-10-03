# Kids' care research log

What's here: everything learned while building the **Kids' care** list
(`care` in `venues.json`: hospitals/ER, urgent care, pediatric dentists) that
did *not* end up on the page — source conflicts, dead ends, leads, and the
backlog — so nobody re-does the same digging. Not read by any script.

All entries were researched on 2026-10-02. **First-party** means the
provider's own website. Aggregators (Healthline, WebMD, newpatientsinc,
Solv, etc.) were only used to *find* providers: they were wrong or stale on
the first thing we cross-checked (see "Source conflicts"). Nothing goes on
the page until it has been read on the provider's own site, and `checked`
records the date it was read.

Keep this file current: when a lead below gets added to `venues.json`, delete
it here; when one is ruled out, add it with the evidence.

## On the page now (10)

| Entry | Category | Read from |
|---|---|---|
| Edward Hospital Emergency Department | Hospitals & ER | endeavorhealth.org ED page |
| NM Central DuPage Hospital – Pediatric ER | Hospitals & ER | nm.org pediatric ED + hospital pages |
| Advocate Good Samaritan Hospital ED | Hospitals & ER | advocatehealth.com ED page |
| Lurie Children's Hospital ED | Hospitals & ER | luriechildrens.org ER page |
| PM Pediatric Urgent Care (Naperville) | Urgent Care | pmpediatriccare.com + luriechildrens.org (hours) |
| AFC Urgent Care Naperville | Urgent Care | afcurgentcare.com children's page |
| Tic Tac Tooth Pediatric Dentistry | Pediatric Dentists | tictactooth.com |
| Innovative Pediatric Dentistry | Pediatric Dentists | innovativepediatricdentistry.com |
| Small Smiles Pediatric Dentistry | Pediatric Dentists | smallsmiles.org |
| G+G Pediatric Dentistry & Orthodontics | Pediatric Dentists | Endeavor Health provider listing (no practice site found) |

## Source conflicts (and which one the page uses)

| Entry | Conflict | Used |
|---|---|---|
| Small Smiles | Directories say 1816 Bay Scott Cir, Ste 104; the practice's own site says **1980 Three Farms Ave, Ste 108**. (The Census geocoder spells it "Three Farms Rd"; coordinates are for that spot.) | Own site |
| Tic Tac Tooth | Directories list (312) 480-8720 and Friday-closed / Saturday 9–2; own site says **(630) 995-3393** and Fri–Sat by appointment only. | Own site |
| NM Central DuPage pediatric ER | The pediatric-ED page says "9 am – 1 am every day"; the location page says Mon–Fri 9 am–1 am, **weekends/holidays noon–midnight**. Hospital page lists ED phone (630) 933-2600; the location page lists 630.933.6631. | Page says "about 9 AM–1 AM, shorter on weekends/holidays — call"; ED phone |
| Advocate Good Samaritan | A directory gave (630) 275-5900 for the ED; the hospital's own ED page lists only 800-3-ADVOCATE. | Own page |
| NM Central DuPage coordinates | The Census geocoder couldn't match "25 N Winfield Rd". | OpenStreetMap's hospital building (Nominatim) |

## Gaps on first-party pages (left blank on the card)

- AFC Urgent Care Naperville: no hours on the page we could read (probably
  script-rendered), and it doesn't say whether staff are pediatric
  specialists. Card says so.
- Small Smiles: no hours, no insurance list.
- G+G: no hours/insurance/new-patient status; Endeavor's profile says the
  dentist is an independent practitioner, not an Endeavor employee.
- Edward Hospital's pediatric ER hours: pages only say the ER is open 24/7;
  no separate pediatric-ER hours were published.
- No page lists specific insurance plans for the hospitals or PM Pediatric
  (PM Pediatric: "most major insurance plans"). `insurance` is therefore only
  set where a page said something concrete.

## Reviews

Star ratings and review counts come from Google Places, filled in by
`update_venues.py` on its weekly run (one small lookup per entry). They were
not available when the list was first built (no API key on the dev machine),
so cards show no rating until the first run after this change — or run
`GOOGLE_PLACES_API_KEY=... python3 update_venues.py && python3 build.py`
locally. Entries Google can't match (name must overlap, within 800 m) simply
keep no rating; check the run log's "no Google match for ..." line. Review
*text* is not pulled: it needs a pricier Places field and Google's display
rules, and a rating plus a link to the Google page covers the need. Treat ER
ratings with care — hospital reviews are dominated by wait times, not by
clinical care.

## Leads not yet added

| Lead | Status |
|---|---|
| Just For Kids Pediatric Dentistry, 1220 Hobson Rd Ste 224 | Directories say it is *not accepting new patients*, and no website was found. Re-check before adding. |
| Edward-Elmhurst / Endeavor Immediate Care (e.g. Naperville on Naper Blvd) | Adult+child immediate care, not pediatric-specific; only worth adding if you want a hospital-system urgent care option. Page: endeavorhealth.org/locations/immediate-care-naperville-naper-blvd |
| Advocate Immediate Care (Downers Grove) | Same — general immediate care. |
| Advocate Children's Hospital (Oak Lawn / Park Ridge) | Dedicated children's hospitals, farther out than the three ERs listed. |
| Lurie Children's at NM Delnor (Geneva) | Another Lurie-staffed pediatric ER, west of Naperville. Not read yet. |
| Lurie's planned Downers Grove children's hospital | News article was a 404 when read; check Lurie's own site for status and opening date. |
| Silver Cross (New Lenox), Edward-Elmhurst Plainfield/Bolingbrook ERs | Southwest-side options. Not read yet. |
| Other pediatric dentists (e.g. other Naperville/Aurora/Plainfield offices), pediatricians | Not researched — pick providers from a source you trust (your insurer's directory), then verify on the provider's own site. |
| Insurance | Plans you actually use aren't known to the page. If you care about one (say Delta Dental or BCBS), search for it on the page, and consider checking each dentist's plan list by phone. |

## How the research was done

`WebSearch` to find providers, then `WebFetch` on each provider's own pages to
copy hours, phone, ages, insurance statements and services. Page-summaries
can drop or misstate details, so anything that mattered (addresses, phones,
hours) was cross-checked against a second page when one existed. Coordinates:
US Census geocoder (keyless) from the address on the provider's own page;
the city/ZIP the geocoder returns is not trusted over the provider's page.
