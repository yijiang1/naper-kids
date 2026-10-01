#!/usr/bin/env python3
"""
Validates venues.json so a bad hand edit never gets baked into index.html.

Checks every entry in "venues" (not "candidates" — those are an updater
holding pen and are allowed to be incomplete until promoted):
  - required fields are present: name, category, lat, lng, address, cost,
    age, note
  - ids are unique and are clean slugs (lowercase, hyphen-separated)
  - coordinates are within ~90 km of "center" (the Chicago six-county metro)
  - rating (if set) is between 0 and 5
  - season / tags / indoor (if set) only use their fixed vocabularies
  - kids_menu (required for category "Restaurants", optional elsewhere) is
    well-formed: a link to the restaurant's own menu, a "checked" date, and
    at least one section with at least one named item

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
MAX_DISTANCE_KM = 90.0  # matches update_venues.py's MAX_CANDIDATE_DISTANCE_M
TAG_VOCAB = {"restrooms", "fenced", "shade", "stroller", "food", "water-play", "picnic", "parking"}
SEASON_VOCAB = {"year-round", "summer", "winter"}
RESTAURANT_CATEGORY = "Restaurants"  # these must carry a kids_menu
MENU_KEYS = {"url", "summary", "sections", "checked"}
MENU_SECTION_KEYS = {"title", "note", "items"}
MENU_ITEM_KEYS = {"name", "desc", "price"}
URL_RE = re.compile(r"^https?://\S+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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


def check_unknown_keys(where, obj, allowed, errors):
    extra = sorted(set(obj.keys()) - allowed)
    if extra:
        errors.append("{}: unknown key(s) {} (allowed: {})".format(where, extra, sorted(allowed)))


def check_kids_menu(v, errors):
    menu = v.get("kids_menu")
    who = describe(v)
    if menu is None:
        if v.get("category") == RESTAURANT_CATEGORY:
            errors.append("{}: restaurants need a 'kids_menu'".format(who))
        return
    if not isinstance(menu, dict):
        errors.append("{}: kids_menu must be an object, got {!r}".format(who, menu))
        return
    check_unknown_keys(who + ": kids_menu", menu, MENU_KEYS, errors)

    url = menu.get("url")
    if not (isinstance(url, str) and URL_RE.match(url)):
        errors.append("{}: kids_menu.url must be an http(s) link to the restaurant's own menu, got {!r}".format(who, url))
    checked = menu.get("checked")
    if not (isinstance(checked, str) and DATE_RE.match(checked)):
        errors.append("{}: kids_menu.checked must be a YYYY-MM-DD date, got {!r}".format(who, checked))
    summary = menu.get("summary")
    if summary is not None and not (isinstance(summary, str) and summary.strip()):
        errors.append("{}: kids_menu.summary, if present, must be non-empty text".format(who))

    sections = menu.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append("{}: kids_menu.sections must be a non-empty list".format(who))
        return
    for si, sec in enumerate(sections):
        where = "{}: kids_menu.sections[{}]".format(who, si)
        if not isinstance(sec, dict):
            errors.append("{} must be an object".format(where))
            continue
        check_unknown_keys(where, sec, MENU_SECTION_KEYS, errors)
        for key in ("title", "note"):
            if key in sec and not (isinstance(sec[key], str) and sec[key].strip()):
                errors.append("{}.{} must be non-empty text if present".format(where, key))
        items = sec.get("items")
        if not isinstance(items, list) or not items:
            errors.append("{}.items must be a non-empty list".format(where))
            continue
        for ii, item in enumerate(items):
            iwhere = "{}.items[{}]".format(where, ii)
            if not isinstance(item, dict):
                errors.append("{} must be an object".format(iwhere))
                continue
            check_unknown_keys(iwhere, item, MENU_ITEM_KEYS, errors)
            if not (isinstance(item.get("name"), str) and item["name"].strip()):
                errors.append("{} needs a 'name'".format(iwhere))
            for key in ("desc", "price"):
                if key in item and not (isinstance(item[key], str) and item[key].strip()):
                    errors.append("{}.{} must be non-empty text if present".format(iwhere, key))


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
        check_kids_menu(v, errors)

    if errors:
        print("venues.json failed validation ({} issue{}):".format(
            len(errors), "" if len(errors) == 1 else "s"), file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        sys.exit(1)

    print("venues.json OK ({} venues checked)".format(len(venues)))


if __name__ == "__main__":
    main()
