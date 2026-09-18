#!/usr/bin/env python3
"""
Rebuilds index.html from index_template.html + venues.json.

Run this after editing either source file:
    python3 build.py

index.html is generated output — don't hand-edit it, your changes will be
overwritten the next time this runs. Edit index_template.html (markup/CSS/JS)
or venues.json (the data) instead.
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent
TEMPLATE = ROOT / "index_template.html"
DATA = ROOT / "venues.json"
OUTPUT = ROOT / "index.html"

def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    # The page only reads "venues". Leave the review queue ("candidates") out
    # of the offline copy so index.html doesn't carry data it never shows.
    data.pop("candidates", None)
    venues_json_text = json.dumps(data, indent=2, ensure_ascii=False)
    template = TEMPLATE.read_text(encoding="utf-8")

    if "__VENUES_JSON__" not in template:
        raise SystemExit("index_template.html is missing the __VENUES_JSON__ placeholder")

    output = template.replace("__VENUES_JSON__", venues_json_text)
    OUTPUT.write_text(output, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(output):,} bytes)")

if __name__ == "__main__":
    main()
