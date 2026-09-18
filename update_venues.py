#!/usr/bin/env python3
"""
Refreshes venues.json with current data from the Google Places API (New).

SETUP (one time):
  1. Get an API key:
     https://developers.google.com/maps/documentation/places/web-service/get-api-key
     Enable "Places API (New)" on that Google Cloud project.
  2. Set the key as an environment variable before running:
       export GOOGLE_PLACES_API_KEY="your-key-here"
  3. Run it:
       python3 update_venues.py

WHAT IT DOES:
  Runs one search per category (see CATEGORIES below) and uses the results
  to refresh the *factual* fields of the venues already in venues.json:
  rating, address, phone, website, and coordinates. It never removes a
  venue, never changes a venue's category, and never touches the
  hand-written "note", "hours", "cost", and "age" fields.

  Results are matched to existing venues by Google place id (saved into
  each venue as "place_id" the first time it's seen), then by the venue's
  "id" slug, then by "same spot + similar name" as a last resort. Venues
  Google doesn't return on a given run are left exactly as they were.

  Places Google returns that aren't in venues.json yet go into a separate
  "candidates" list at the bottom of the file. The page ignores that list.
  To add one, move it up into "venues" and fill in note/hours/cost/age; to
  drop one, just delete it (it may reappear on a later run if Google still
  returns it, but it will never show on the page).

COST:
  Text Search on the new Places API is a paid call, but Google's free
  monthly credit comfortably covers running this occasionally (e.g. weekly
  or monthly) for one city. Check current pricing before heavy use:
  https://mapsplatform.google.com/pricing/
"""

import datetime
import json
import math
import os
import re
import sys
import urllib.request
import urllib.error

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")
CENTER = {"lat": 41.7508, "lng": -88.1535}  # Naperville, IL
RADIUS_METERS = 16000.0
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venues.json")

# A Google result counts as "the same place" as an existing venue when it's
# within MATCH_RADIUS_M of it AND their names overlap at least this much
# (0–1, fraction of the shorter name's words that appear in the other).
# This is only the fallback; place_id and id-slug matches come first.
MATCH_RADIUS_M = 150.0
MATCH_NAME_SCORE = 0.75

# Edit this dict to add/remove categories or tweak what gets searched for.
CATEGORIES = {
    "Parks & Playgrounds": "parks and playgrounds in Naperville IL",
    "Splash Pads & Pools": "splash pads and pools in Naperville IL",
    "Museums & Indoor Play": "children's museums and indoor play spaces in Naperville IL",
    "Libraries": "public libraries in Naperville IL",
    "Nature & Zoos": "nature centers and zoos near Naperville IL",
    "Bowling & Arcades": "kids bowling and family entertainment near Naperville IL",
    "Forest Preserves & Trails": "forest preserves near Naperville IL",
}

# The only fields this script is allowed to change on an existing venue.
REFRESHABLE = ("lat", "lng", "address", "rating", "phone", "website")

# Preferred key order when writing a venue back out (purely cosmetic).
KEY_ORDER = ("id", "place_id", "name", "category", "lat", "lng", "address",
             "rating", "phone", "website", "hours", "note", "cost", "age")

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.rating",
    "places.nationalPhoneNumber",
    "places.websiteUri",
])

STOPWORDS = {"the", "of", "and", "at", "in", "a", "an"}


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def search_category(query):
    url = "https://places.googleapis.com/v1/places:searchText"
    body = json.dumps({
        "textQuery": query,
        "locationBias": {
            "circle": {
                "center": {"latitude": CENTER["lat"], "longitude": CENTER["lng"]},
                "radius": RADIUS_METERS,
            }
        },
        "maxResultCount": 10,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Goog-Api-Key", API_KEY)
    req.add_header("X-Goog-FieldMask", FIELD_MASK)

    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8")).get("places", [])


def to_venue(place, category):
    name = place.get("displayName", {}).get("text", "Unknown")
    loc = place.get("location", {})
    return {
        "id": slugify(name),
        "place_id": place.get("id"),
        "name": name,
        "category": category,
        "lat": loc.get("latitude"),
        "lng": loc.get("longitude"),
        "address": place.get("formattedAddress", ""),
        "rating": place.get("rating"),
        "phone": place.get("nationalPhoneNumber"),
        "website": place.get("websiteUri"),
        "hours": None,
        "note": "",
        "cost": "",
        "age": "",
    }


def load_existing():
    if not os.path.exists(OUTPUT_PATH):
        return {"venues": [], "candidates": []}
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("venues", [])
    data.setdefault("candidates", [])
    return data


def distance_m(lat1, lng1, lat2, lng2):
    """Great-circle distance in metres."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def name_tokens(name):
    return {t for t in re.findall(r"[a-z0-9]+", name.lower()) if t not in STOPWORDS}


def name_score(a, b):
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / float(min(len(ta), len(tb)))


def find_match(fresh, venues, taken):
    """Return the existing venue that `fresh` (a Google result) refers to, or None."""
    pid = fresh.get("place_id")
    if pid:
        for v in venues:
            if v["id"] not in taken and v.get("place_id") == pid:
                return v
    for v in venues:
        if v["id"] not in taken and v["id"] == fresh["id"]:
            return v
    if fresh.get("lat") is None or fresh.get("lng") is None:
        return None
    best, best_score = None, 0.0
    for v in venues:
        if v["id"] in taken or v.get("lat") is None or v.get("lng") is None:
            continue
        if distance_m(fresh["lat"], fresh["lng"], v["lat"], v["lng"]) > MATCH_RADIUS_M:
            continue
        score = name_score(fresh["name"], v["name"])
        if score > best_score:
            best, best_score = v, score
    return best if best_score >= MATCH_NAME_SCORE else None


def refresh_fields(target, fresh):
    """Copy the refreshable fields from `fresh` onto `target`. Returns the names of fields that changed."""
    changed = []
    for key in REFRESHABLE:
        new = fresh.get(key)
        if new is None:
            continue  # Google gave us nothing for this field; keep what we had
        if target.get(key) != new:
            target[key] = new
            changed.append(key)
    if fresh.get("place_id") and target.get("place_id") != fresh["place_id"]:
        target["place_id"] = fresh["place_id"]
        changed.append("place_id")
    return changed


def ordered(venue):
    out = {}
    for key in KEY_ORDER:
        if key in venue:
            out[key] = venue[key]
    for key in venue:
        if key not in out:
            out[key] = venue[key]
    return out


def main():
    if not API_KEY:
        print("Set GOOGLE_PLACES_API_KEY first — see the top of this file.", file=sys.stderr)
        sys.exit(1)

    data = load_existing()
    venues = data["venues"]

    # 1. Collect everything Google returns, de-duplicated by place id.
    fresh_results = []
    seen_pids = set()
    for category, query in CATEGORIES.items():
        print("Searching: {} ...".format(category))
        try:
            places = search_category(query)
        except urllib.error.HTTPError as e:
            print("  failed ({}): {}".format(e.code, e.read().decode("utf-8", "ignore")), file=sys.stderr)
            continue
        except Exception as e:
            print("  failed: {}".format(e), file=sys.stderr)
            continue
        for place in places:
            pid = place.get("id")
            if pid and pid in seen_pids:
                continue
            if pid:
                seen_pids.add(pid)
            fresh_results.append(to_venue(place, category))

    # 2. Match results to the venues we already have; refresh their factual fields.
    taken = set()
    refreshed = 0
    candidates = {}
    for c in data["candidates"]:
        candidates[c.get("place_id") or c["id"]] = c
    new_candidates = 0

    for fresh in fresh_results:
        match = find_match(fresh, venues, taken)
        if match is not None:
            taken.add(match["id"])
            changed = refresh_fields(match, fresh)
            if changed:
                refreshed += 1
                print("  updated {}: {}".format(match["name"], ", ".join(changed)))
            continue
        key = fresh.get("place_id") or fresh["id"]
        if key in candidates:
            refresh_fields(candidates[key], fresh)  # keep any notes you've started writing on it
        else:
            candidates[key] = fresh
            new_candidates += 1

    not_seen = [v["name"] for v in venues if v["id"] not in taken]

    # 3. Write it back. Venues keep their order; nothing is ever dropped.
    out = {
        "generated_at": datetime.date.today().isoformat(),
        "center": data.get("center", CENTER),
        "venues": [ordered(v) for v in venues],
        "candidates": [ordered(c) for c in candidates.values()],
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print()
    print("Kept all {} venues; {} had fields refreshed.".format(len(venues), refreshed))
    if not_seen:
        print("Not returned by Google this run (left unchanged): " + "; ".join(not_seen))
    print("{} candidate(s) waiting in the 'candidates' list ({} new this run).".format(
        len(candidates), new_candidates))
    print("Wrote " + OUTPUT_PATH)


if __name__ == "__main__":
    main()
