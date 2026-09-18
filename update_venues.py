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
  Runs one search per category (see CATEGORIES below), merges the results
  into venues.json, and keeps any "note", "hours", "cost", or "age" text
  you've already written for a venue rather than overwriting it. New venues
  Google returns get added with those fields empty for you to fill in by
  hand — the Places API doesn't return admission prices or age fit, so both
  always have to be researched and entered manually.

COST:
  Text Search on the new Places API is a paid call, but Google's free
  monthly credit comfortably covers running this occasionally (e.g. weekly
  or monthly) for one city. Check current pricing before heavy use:
  https://mapsplatform.google.com/pricing/
"""

import datetime
import json
import os
import re
import sys
import urllib.request
import urllib.error

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")
CENTER = {"lat": 41.7508, "lng": -88.1535}  # Naperville, IL
RADIUS_METERS = 16000.0
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venues.json")

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

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.rating",
    "places.nationalPhoneNumber",
    "places.websiteUri",
])


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def search_category(query: str):
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


def to_venue(place: dict, category: str) -> dict:
    name = place.get("displayName", {}).get("text", "Unknown")
    loc = place.get("location", {})
    return {
        "id": slugify(name),
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


def load_existing() -> dict:
    if not os.path.exists(OUTPUT_PATH):
        return {}
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {v["id"]: v for v in data.get("venues", [])}


def main():
    if not API_KEY:
        print("Set GOOGLE_PLACES_API_KEY first — see the top of this file.", file=sys.stderr)
        sys.exit(1)

    existing = load_existing()
    merged = []
    seen_ids = set()

    for category, query in CATEGORIES.items():
        print(f"Searching: {category} ...")
        try:
            places = search_category(query)
        except urllib.error.HTTPError as e:
            print(f"  failed ({e.code}): {e.read().decode('utf-8', 'ignore')}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"  failed: {e}", file=sys.stderr)
            continue

        for place in places:
            venue = to_venue(place, category)
            vid = venue["id"]
            if vid in seen_ids:
                continue
            seen_ids.add(vid)
            if vid in existing:
                # Keep whatever you've hand-written; refresh the factual fields only.
                venue["note"] = existing[vid].get("note", "")
                venue["hours"] = existing[vid].get("hours")
                venue["cost"] = existing[vid].get("cost", "")
                venue["age"] = existing[vid].get("age", "")
            merged.append(venue)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.date.today().isoformat(),
            "center": CENTER,
            "venues": merged,
        }, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(merged)} venues to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
