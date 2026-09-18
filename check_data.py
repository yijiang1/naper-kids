#!/usr/bin/env python3
"""
Validates venues.json so a bad hand edit never gets baked into index.html.

Checks every entry in "venues" (not "candidates" — those are an updater
holding pen and are allowed to be incomplete until promoted):
  - required fields are present: name, category, lat, lng, address, cost,
    age, note
  - ids are unique and are clean slugs (lowercase, hyphen-separated)
  - coordinates are within ~60 km of "center"
  - rating (if set) is between 0 and 5
  - season / tags / indoor (if set) only use their fixed vocabularies

Runs by hand, or in the weekly workflow right before build.py:
    python3 check_data.py
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import update_venues as upd  # noqa: E402 (reuses distance_m/CENTER)

DATA_PATH = os.path.join(HERE, "venues.json")

REQUIRED_FIELDS = ("name", "category", "lat", "lng", "address", "cost", "age", "note")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_DISTANCE_KM = 60.0
TAG_VOCAB = {"restrooms", "fenced", "shade", "stroller", "food", "water-play", "picnic", "parking"}
SEASON_VOCAB = {"year-round", "summer", "winter"}


def describe(v):
    return v.get("id") or v.get("name") or "<unknown venue>"


def check_season(v, errors):
    season = v.get("season")
    if season is None:
        return
    if isinstance(season, str):
        if season not in SEASON_VOCAB:
            errors.append("{}: season {!r} is not one of {}".format(
                describe(v), season, sorted(SEASON_VOCAB)))
        return
    if isinstance(season, dict):
        keys = set(season.keys())
        if keys != {"from", "to"}:
            errors.append("{}: season object must have exactly 'from' and 'to', got {}".format(
                describe(v), sorted(keys)))
            return
        for k in ("from", "to"):
            m = season.get(k)
            if not isinstance(m, int) or isinstance(m, bool) or not (1 <= m <= 12):
                errors.append("{}: season.{} must be a month 1-12, got {!r}".format(
                    describe(v), k, m))
        return
    errors.append("{}: season must be a string or a {{from,to}} object, got {!r}".format(
        describe(v), season))


def check_tags(v, errors):
    tags = v.get("tags")
    if tags is None:
        return
    if not isinstance(tags, list):
        errors.append("{}: tags must be a list, got {!r}".format(describe(v), tags))
        return
    for t in tags:
        if t not in TAG_VOCAB:
            errors.append("{}: tag {!r} is not in the fixed vocabulary {}".format(
                describe(v), t, sorted(TAG_VOCAB)))


def check_indoor(v, errors):
    indoor = v.get("indoor")
    if indoor is None:
        return
    if indoor not in (True, False, "partly"):
        errors.append("{}: indoor must be true, false, or 'partly', got {!r}".format(
            describe(v), indoor))


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    venues = data.get("venues", [])
    center = data.get("center", upd.CENTER)
    errors = []
    seen_ids = set()

    for v in venues:
        vid = v.get("id")

        for field in REQUIRED_FIELDS:
            if v.get(field) in (None, ""):
                errors.append("{}: missing '{}'".format(describe(v), field))

        if not vid:
            errors.append("<unknown venue>: missing 'id'")
        else:
            if vid in seen_ids:
                errors.append("id '{}' is used more than once".format(vid))
            seen_ids.add(vid)
            if not SLUG_RE.match(vid):
                errors.append("id '{}' is not a clean slug (lowercase, hyphen-separated)".format(vid))

        lat, lng = v.get("lat"), v.get("lng")
        if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
            dist_km = upd.distance_m(center["lat"], center["lng"], lat, lng) / 1000.0
            if dist_km > MAX_DISTANCE_KM:
                errors.append("{}: {:.1f} km from center, over the {:.0f} km limit".format(
                    describe(v), dist_km, MAX_DISTANCE_KM))

        rating = v.get("rating")
        if rating is not None and not (isinstance(rating, (int, float)) and 0 <= rating <= 5):
            errors.append("{}: rating {!r} is outside 0-5".format(describe(v), rating))

        check_season(v, errors)
        check_tags(v, errors)
        check_indoor(v, errors)

    if errors:
        print("venues.json failed validation ({} issue{}):".format(
            len(errors), "" if len(errors) == 1 else "s"), file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        sys.exit(1)

    print("venues.json OK ({} venues checked)".format(len(venues)))


if __name__ == "__main__":
    main()
