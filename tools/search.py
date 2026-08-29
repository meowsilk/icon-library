#!/usr/bin/env python3
"""Search the icon/font catalog and rank the best matches for humans and agents."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "catalog" / "icons.json"
FONTS = ROOT / "catalog" / "fonts.json"

PREFERRED = [
    "cs2",
    "dopamina",
    "fa-7.3.0",
    "remix",
    "embedded-weapons",
    "iconsv2",
]


def tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def score_icon(query: str, q_tokens: list[str], icon: dict, collection_id: str) -> int:
    name = icon.get("name", "")
    aliases = icon.get("aliases") or []
    hay = " ".join([name, *aliases]).lower()
    q = query.lower().strip()
    score = 0
    if name.lower() == q or q in [a.lower() for a in aliases]:
        score += 200
    elif name.lower().startswith(q) or any(a.lower().startswith(q) for a in aliases):
        score += 120
    elif q in hay:
        score += 80
    hit = sum(1 for t in q_tokens if t in hay)
    score += hit * 18
    if hit == len(q_tokens) and q_tokens:
        score += 25
    if collection_id in PREFERRED:
        score += 12 - PREFERRED.index(collection_id)
    if collection_id == "cs2" and any(t in hay for t in q_tokens):
        score += 40
    if collection_id == "dopamina" and any(t in hay for t in q_tokens):
        score += 35
    return score


def load_icons() -> dict:
    if not ICONS.exists():
        raise SystemExit("catalog/icons.json missing. Run: python tools/build_catalog.py")
    return json.loads(ICONS.read_text(encoding="utf-8"))


def load_fonts() -> dict:
    if not FONTS.exists():
        raise SystemExit("catalog/fonts.json missing. Run: python tools/build_catalog.py")
    return json.loads(FONTS.read_text(encoding="utf-8"))


def search_icons(query: str, limit: int, collection: str | None) -> list[dict]:
    catalog = load_icons()
    q_tokens = tokens(query)
    hits = []
    for data in catalog["collections"]:
        if collection and data["id"] != collection:
            continue
        for icon in data.get("icons", []):
            s = score_icon(query, q_tokens, icon, data["id"])
            if s < 18:
                continue
            hits.append(
                {
                    "score": s,
                    "collection": data["id"],
                    "collectionName": data["name"],
                    "kind": data["kind"],
                    "name": icon.get("name"),
                    "aliases": icon.get("aliases") or [],
                    "unicode": icon.get("unicode"),
                    "path": icon.get("path") or data.get("fontUrl"),
                    "class": class_for(data, icon),
                    "useWhen": data.get("useWhen"),
                }
            )
    hits.sort(key=lambda h: (-h["score"], h["collection"], h["name"]))
    return hits[:limit]


def class_for(collection: dict, icon: dict) -> str | None:
    kind = collection.get("kind")
    name = icon.get("name")
    if kind == "fa":
        styles = collection.get("styles") or []
        solid = next((s for s in styles if s["id"] == "solid"), None)
        if icon.get("brand"):
            brands = next((s for s in styles if s.get("brand")), None)
            if brands:
                return f"{brands['iconClass']} fa-{name}"
        if solid:
            return f"{solid['iconClass']} fa-{name}"
        return f"fa-solid fa-{name}"
    if kind == "svg":
        return None
    if collection.get("id") == "remix" and name:
        return f"ri-{name}" if not name.startswith("ri-") else name
    return None


def search_fonts(query: str, limit: int) -> list[dict]:
    catalog = load_fonts()
    q = query.lower()
    q_tokens = tokens(query)
    hits = []
    for font in catalog["fonts"]:
        hay = " ".join(
            str(font.get(k) or "") for k in ("id", "name", "path", "family", "use", "kind")
        ).lower()
        score = 0
        if q in hay:
            score += 70
        score += sum(18 for t in q_tokens if t in hay)
        if score < 18:
            continue
        hits.append({"score": score, **font})
    hits.sort(key=lambda h: (-h["score"], h["name"]))
    return hits[:limit]


def print_icon(hit: dict) -> None:
    extras = []
    if hit.get("class"):
        extras.append(hit["class"])
    if hit.get("unicode"):
        extras.append(f"U+{hit['unicode'].upper()}")
    if hit.get("path"):
        extras.append(hit["path"])
    print(f"{hit['score']:3}  {hit['collection']:22}  {hit['name']}")
    print(f"     { '  |  '.join(extras)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search ff0l icon library",
        epilog="Examples:\n  python tools/search.py settings\n  python tools/search.py awp\n  python tools/search.py --kind font title\n  python tools/search.py gear --json\n  python tools/search.py --collection cs2 knife",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", nargs="+", help="what you need, e.g. 'settings gear' or 'awp'")
    parser.add_argument("--kind", choices=("icon", "font", "all"), default="all")
    parser.add_argument("--collection", help="limit to one collection id from catalog/icons.json")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    query = " ".join(args.query)

    result = {"query": query, "icons": [], "fonts": [], "pick": None}
    if args.kind in ("icon", "all"):
        result["icons"] = search_icons(query, args.limit, args.collection)
    if args.kind in ("font", "all") and not args.collection:
        result["fonts"] = search_fonts(query, min(args.limit, 8))

    if result["icons"]:
        result["pick"] = result["icons"][0]
    elif result["fonts"]:
        result["pick"] = result["fonts"][0]

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print(f"query: {query}")
    if result["pick"] and "name" in result["pick"] and "collection" in result["pick"]:
        pick = result["pick"]
        print(f"best:  {pick['collection']} / {pick['name']}")
        if pick.get("class"):
            print(f"class: {pick['class']}")
        if pick.get("path"):
            print(f"path:  {pick['path']}")
        print()
    if result["icons"]:
        print("icons")
        for hit in result["icons"]:
            print_icon(hit)
            print()
    if result["fonts"]:
        print("fonts")
        for font in result["fonts"]:
            print(f"{font['score']:3}  {font['name']}")
            print(f"     {font.get('path')}  |  {font.get('use') or ''}")
            print()


if __name__ == "__main__":
    main()
