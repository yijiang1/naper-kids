#!/usr/bin/env python3
"""
Checks that update_venues.py never loses or duplicates curated data.

Runs against a fake Places API on a temporary copy of venues.json, so it
needs no API key and no network:

    python3 test_update_venues.py
"""

import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("GOOGLE_PLACES_API_KEY", "fake-key-for-tests")
sys.path.insert(0, HERE)
import update_venues as upd  # noqa: E402


def place(pid, name, lat, lng, rating=None, phone=None, website=None, addr=""):
    p = {"id": pid, "displayName": {"text": name},
         "location": {"latitude": lat, "longitude": lng}, "formattedAddress": addr}
    if rating is not None:
        p["rating"] = rating
    if phone:
        p["nationalPhoneNumber"] = phone
    if website:
        p["websiteUri"] = website
    return p


QUERY_TO_CATEGORY = {q: c for c, q in upd.CATEGORIES.items()}


def run_updater(fake_results, path):
    """Run main() with search_category answering from `fake_results` (category -> places)."""
    upd.OUTPUT_PATH = path
    upd.search_category = lambda query: fake_results.get(QUERY_TO_CATEGORY[query], [])
    buf = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = buf
    try:
        upd.main()
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    with io.open(path, encoding="utf-8") as f:
        return json.load(f), buf.getvalue()


def main():
    tmpdir = tempfile.mkdtemp(prefix="naperkids-test-")
    path = os.path.join(tmpdir, "venues.json")
    shutil.copy(os.path.join(HERE, "venues.json"), path)
    with io.open(path, encoding="utf-8") as f:
        before = json.load(f)
    before_ids = [v["id"] for v in before["venues"]]
    by_id = {v["id"]: v for v in before["venues"]}
    knoch, jaycee = by_id["knoch-park"], by_id["jaycee-playground"]
    lib95, splash95 = by_id["95th-street-library"], by_id["95th-street-plaza-splash"]
    museum = by_id["dupage-childrens-museum"]

    # --- Run 1: the usual mix of exact, fuzzy, and brand-new results ---------
    fake = {
        "Parks & Playgrounds": [
            # exact id match, rating changed
            place("g1", "Knoch Park", knoch["lat"], knoch["lng"], rating=4.6,
                  phone=knoch["phone"], website=knoch["website"], addr=knoch["address"]),
            # different spelling -> must match by "same spot + similar name"
            place("g2", "Naperville Jaycee Playground", jaycee["lat"], jaycee["lng"], rating=4.9),
            # never seen before -> candidate
            place("g3", "Some Random New Park", 41.70, -88.10, rating=4.0),
        ],
        "Splash Pads & Pools": [
            # ~75 m from the 95th St library; must NOT be matched to the library
            place("g6", "95th Street Splash Pad", splash95["lat"], splash95["lng"], rating=4.9),
        ],
        "Museums & Indoor Play": [
            # Google returns no phone/website -> ours must be kept
            place("g7", "DuPage Children's Museum", museum["lat"], museum["lng"], rating=4.4),
        ],
        "Libraries": [
            # ~75 m from the splash pad; must match the library
            place("g4", "Naperville Public Library - 95th Street Library", lib95["lat"], lib95["lng"], rating=4.7),
            place("g5", "Nichols Library", by_id["nichols-library"]["lat"], by_id["nichols-library"]["lng"], rating=4.5),
        ],
        "Nature & Zoos": [
            # same place id again (Nature runs after Libraries) -> ignored as a duplicate
            place("g4", "duplicate that must be skipped", 0.0, 0.0),
        ],
    }
    data, log = run_updater(fake, path)
    V = {v["id"]: v for v in data["venues"]}
    assert [v["id"] for v in data["venues"]] == before_ids, "venue list changed"
    assert V["knoch-park"]["rating"] == 4.6 and V["knoch-park"]["place_id"] == "g1"
    assert V["knoch-park"]["note"] == knoch["note"] and V["knoch-park"]["category"] == knoch["category"]
    assert V["jaycee-playground"]["place_id"] == "g2", "fuzzy (distance + name) match failed"
    assert V["95th-street-library"].get("place_id") == "g4", "library matched wrongly"
    assert V["95th-street-plaza-splash"].get("place_id") == "g6", "splash pad matched wrongly"
    assert V["nichols-library"]["place_id"] == "g5" and V["nichols-library"]["rating"] == 4.5
    assert V["dupage-childrens-museum"]["phone"] == museum["phone"], "phone wiped by an empty Google field"
    assert V["dupage-childrens-museum"]["website"] == museum["website"]
    assert [c["name"] for c in data["candidates"]] == ["Some Random New Park"], data["candidates"]
    assert list(data["venues"][0].keys())[:3] == ["id", "place_id", "name"]
    assert "Not returned by Google this run" in log
    print("run 1 OK: matching, refresh, candidates")

    # --- Run 2: Google renames and re-categorises a place -> place_id wins ---
    fake = {
        "Nature & Zoos": [place("g1", "Knoch Park Naperville", knoch["lat"], knoch["lng"], rating=4.7)],
        "Parks & Playgrounds": [place("g3", "Some Random New Park", 41.70, -88.10, rating=4.1)],
    }
    data, log = run_updater(fake, path)
    V = {v["id"]: v for v in data["venues"]}
    assert [v["id"] for v in data["venues"]] == before_ids
    assert V["knoch-park"]["rating"] == 4.7
    assert V["knoch-park"]["category"] == knoch["category"], "category must stay hand-assigned"
    assert V["knoch-park"]["name"] == knoch["name"], "name must stay hand-curated"
    assert len(data["candidates"]) == 1 and data["candidates"][0]["rating"] == 4.1, "candidate duplicated"
    assert V["95th-street-library"]["place_id"] == "g4", "place_id lost when Google didn't return it"
    print("run 2 OK: place_id match survives rename, no duplicate candidates")

    # --- Run 3: every API call fails -> nothing but the date changes ---------
    def boom(query):
        raise RuntimeError("network down")
    kept_venues, kept_candidates = data["venues"], data["candidates"]
    upd.search_category = boom
    buf = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = buf
    try:
        upd.main()
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    with io.open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["venues"] == kept_venues and data["candidates"] == kept_candidates
    print("run 3 OK: API failures leave the data untouched")

    shutil.rmtree(tmpdir, ignore_errors=True)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
