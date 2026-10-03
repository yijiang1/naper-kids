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


def place(pid, name, lat, lng, rating=None, phone=None, website=None, addr="", count=None):
    p = {"id": pid, "displayName": {"text": name},
         "location": {"latitude": lat, "longitude": lng}, "formattedAddress": addr}
    if rating is not None:
        p["rating"] = rating
    if count is not None:
        p["userRatingCount"] = count
    if phone:
        p["nationalPhoneNumber"] = phone
    if website:
        p["websiteUri"] = website
    return p


QUERY_TO_CATEGORY = {q: c for c, q in upd.CATEGORIES.items()}


def run_updater(fake_results, path, fake_care=None):
    """Run main() with search_category answering from `fake_results` (category -> places)
    and search_provider answering from `fake_care` (care entry name -> places)."""
    upd.OUTPUT_PATH = path
    upd.search_category = lambda query: fake_results.get(QUERY_TO_CATEGORY[query], [])
    fake_care = fake_care or {}
    upd.search_provider = lambda query, lat, lng: next(
        (places for name, places in fake_care.items() if query.startswith(name)), [])
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
    # Start from the real curated list, but with no candidates and no place_ids,
    # so the test exercises the slug/fuzzy matching paths deterministically
    # regardless of what the weekly bot has written since.
    with io.open(os.path.join(HERE, "venues.json"), encoding="utf-8") as f:
        before = json.load(f)
    before["candidates"] = []
    for v in before["venues"]:
        v.pop("place_id", None)
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(before, f, indent=2, ensure_ascii=False)
    before_ids = [v["id"] for v in before["venues"]]
    by_id = {v["id"]: v for v in before["venues"]}
    knoch, jaycee = by_id["knoch-park"], by_id["jaycee-playground"]
    lib95, splash95 = by_id["95th-street-library"], by_id["95th-street-plaza-splash"]
    museum = by_id["dupage-childrens-museum"]
    ramsays = by_id["ramsays-kitchen-naperville"]

    # --- Run 1: the usual mix of exact, fuzzy, and brand-new results ---------
    fake = {
        "Parks & Playgrounds": [
            # exact id match, rating changed; raw Google formatting must be tidied
            place("g1", "Knoch Park", 41.7613506, -88.15650169999999, rating=4.6,
                  phone="+1 630-848-5000",
                  website="https://napervilleparks.org/location/knochpark?utm_source=gbp&utm_medium=organic",
                  addr="724 S West St, Naperville, IL 60540, USA"),
            # different spelling -> must match by "same spot + similar name"
            place("g2", "Naperville Jaycee Playground", jaycee["lat"], jaycee["lng"], rating=4.9),
            # never seen before -> candidate
            place("g3", "Some Random New Park", 41.70, -88.10, rating=4.0),
        ],
        "Splash Pads & Pools": [
            # ~75 m from the 95th St library; must NOT be matched to the library
            place("g6", "95th Street Splash Pad", splash95["lat"], splash95["lng"], rating=4.9),
            # a second Google listing for the same splash pad -> ignored, not a candidate
            place("g8", "Splash pad", splash95["lat"], splash95["lng"], rating=4.8),
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
            # ~230 km away -> not worth a candidate slot
            place("g9", "Far Away Wildlife Park", 39.70, -88.30, rating=4.6),
        ],
        "Restaurants": [
            # the apostrophe breaks the slug match ("ramsay-s-..."), so this must go
            # through "same spot + similar name"; the hand-copied kids menu must survive
            place("g10", "Ramsay's Kitchen Naperville", ramsays["lat"], ramsays["lng"], rating=4.3,
                  phone="+1 331-244-2550"),
        ],
    }
    # The care list: Google also (wrongly) offers a phone/address/website/name, which must be ignored.
    care = {c["id"]: c for c in before["care"]}
    edward, cdh = care["edward-hospital-er"], care["nm-central-dupage-pediatric-er"]
    tic, small = care["tic-tac-tooth-pediatric-dentistry"], care["small-smiles-naperville"]
    afc, innov = care["afc-urgent-care-naperville"], care["innovative-pediatric-dentistry"]
    fake_care = {
        edward["name"]: [
            place("c0", "Edward Hospital Gift Shop Parking", edward["lat"], edward["lng"], rating=1.0, count=3),
            place("c1", "Edward Hospital", edward["lat"] + 0.0005, edward["lng"], rating=4.1, count=1234,
                  phone="+1 111-111-1111", website="https://example.com/wrong", addr="Wrong St"),
        ],
        # same name but ~5 km away -> a different building, must not match
        cdh["name"]: [place("c2", "Northwestern Medicine Central DuPage Hospital", cdh["lat"] + 0.05, cdh["lng"], rating=3.0, count=9)],
        # right spot, unrelated business -> must not match
        tic["name"]: [place("c3", "Joe's Pizza", tic["lat"], tic["lng"], rating=4.9, count=500)],
        small["name"]: [],   # Google has nothing
        innov["name"]: [place("c5", "Innovative Pediatric Dentistry", innov["lat"], innov["lng"], rating=4.9, count=88)],
    }
    data, log = run_updater(fake, path, fake_care)
    V = {v["id"]: v for v in data["venues"]}
    assert [v["id"] for v in data["venues"]] == before_ids, "venue list changed"
    C = {c["id"]: c for c in data["care"]}
    assert [c["id"] for c in data["care"]] == [c["id"] for c in before["care"]], "care list changed"
    assert C["edward-hospital-er"]["rating"] == 4.1 and C["edward-hospital-er"]["rating_count"] == 1234
    assert C["edward-hospital-er"]["place_id"] == "c1", "the near, similarly named result should win"
    assert C["innovative-pediatric-dentistry"]["rating"] == 4.9 and C["innovative-pediatric-dentistry"]["rating_count"] == 88
    for cid in ("nm-central-dupage-pediatric-er", "tic-tac-tooth-pediatric-dentistry",
                "small-smiles-naperville", "afc-urgent-care-naperville"):
        assert "rating" not in C[cid] and "place_id" not in C[cid], cid + " was matched to the wrong place"
    stripped = lambda c: {k: v for k, v in c.items() if k not in ("rating", "rating_count", "place_id")}
    for cid, c in care.items():
        assert stripped(C[cid]) == c, "care entry {} had hand-curated fields changed".format(cid)
    assert len(data["candidates"]) == 1, "care lookups must never create candidates"
    assert "2 of 10 entries had reviews refreshed" in log, log
    assert V["knoch-park"]["rating"] == 4.6 and V["knoch-park"]["place_id"] == "g1"
    assert V["knoch-park"]["address"] == "724 S West St, Naperville, IL 60540", V["knoch-park"]["address"]
    assert V["knoch-park"]["phone"] == "(630) 848-5000", V["knoch-park"]["phone"]
    assert V["knoch-park"]["website"] == "https://napervilleparks.org/location/knochpark", V["knoch-park"]["website"]
    assert V["knoch-park"]["lng"] == -88.1565017, V["knoch-park"]["lng"]
    assert V["knoch-park"]["note"] == knoch["note"] and V["knoch-park"]["category"] == knoch["category"]
    assert V["jaycee-playground"]["place_id"] == "g2", "fuzzy (distance + name) match failed"
    assert V["95th-street-library"].get("place_id") == "g4", "library matched wrongly"
    assert V["95th-street-plaza-splash"].get("place_id") == "g6", "splash pad matched wrongly"
    assert V["nichols-library"]["place_id"] == "g5" and V["nichols-library"]["rating"] == 4.5
    assert V["dupage-childrens-museum"]["phone"] == museum["phone"], "phone wiped by an empty Google field"
    assert V["dupage-childrens-museum"]["website"] == museum["website"]
    assert V["dupage-childrens-museum"].get("indoor") == museum.get("indoor"), "indoor flag touched by updater"
    assert V["dupage-childrens-museum"].get("tags") == museum.get("tags"), "tags touched by updater"
    assert V["wolfs-crossing-park"].get("season") == by_id["wolfs-crossing-park"].get("season"), \
        "season touched by updater"
    assert V["ramsays-kitchen-naperville"]["place_id"] == "g10" and V["ramsays-kitchen-naperville"]["rating"] == 4.3
    assert V["ramsays-kitchen-naperville"]["category"] == "Restaurants"
    assert V["ramsays-kitchen-naperville"]["kids_menu"] == ramsays["kids_menu"], "kids_menu touched by updater"
    assert [c["name"] for c in data["candidates"]] == ["Some Random New Park"], [c["name"] for c in data["candidates"]]
    assert "ignored 1 duplicate listing(s) and 1 too far away" in log, log
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
    kept_venues, kept_candidates, kept_care = data["venues"], data["candidates"], data["care"]
    upd.search_category = boom
    upd.search_provider = lambda query, lat, lng: boom(query)
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
    assert data["care"] == kept_care, "care list changed when its lookups failed"
    print("run 3 OK: API failures leave the data untouched")

    shutil.rmtree(tmpdir, ignore_errors=True)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
