#!/usr/bin/env python3
"""Rebuild data/ from FontVibe's public API plus the official Unicode data files.

    python scripts/build_dataset.py

Stdlib only. Two kinds of input, and nothing else:

1. The symbol library behind fontvibe.ai, read through the same public
   endpoint the website uses (POST /unicode/v1/symbols), once per locale.
   Kaomoji categories are excluded — they have their own dataset
   (github.com/Funovate-Technology/fontvibe-kaomoji).

2. Unicode facts. Code point names and general categories come from Python's
   ``unicodedata`` and the build refuses to run unless its version equals
   UNICODE_VERSION below, so the shipped names are reproducible. Block, age
   and emoji properties are not in ``unicodedata``; they are read from the
   official UCD / emoji files for the same version, downloaded at build time.

Nothing is typed in by hand: if a fact can't be looked up, the field is null.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE = ROOT / ".cache"

API = "https://api.fontvibe.ai/logicSrv/FontVibeAPI/unicode/v1"
SITE = "https://fontvibe.ai"
LOCALES = ["en", "es", "pt", "de", "ja", "zh"]

UNICODE_VERSION = "16.0.0"
EMOJI_VERSION = "16.0"
UCD_FILES = {
    "Blocks.txt": f"https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/Blocks.txt",
    "DerivedAge.txt": f"https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/DerivedAge.txt",
    "emoji-data.txt": f"https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/emoji/emoji-data.txt",
    "emoji-test.txt": f"https://www.unicode.org/Public/emoji/{EMOJI_VERSION}/emoji-test.txt",
}

# Categories with their own page on fontvibe.ai are discovered from the page
# list (PageType "symbol", tool_config.categories). Everything else lives in
# the Symbols tab of the fancy-text tool; this is the hub page for that.
GENERAL_PAGE = "fancy-font-generator"

UA = "fontvibe-symbols-dataset-builder (+https://github.com/Funovate-Technology/fontvibe-symbols)"


# ── fetching ────────────────────────────────────────────────────────────────

def post(path: str, body: dict, locale: str | None = None) -> dict:
    headers = {"Content-Type": "application/json", "User-Agent": UA}
    if locale:
        headers["X-Locale"] = locale
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        env = json.load(r)
    if str(env.get("Code")) != "200":
        sys.exit(f"[build] {path} ({locale}) returned Code={env.get('Code')} Msg={env.get('Msg')}")
    return env["Data"]


def ucd(name: str) -> str:
    CACHE.mkdir(exist_ok=True)
    p = CACHE / f"{UNICODE_VERSION}-{name}"
    if not p.exists():
        req = urllib.request.Request(UCD_FILES[name], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            p.write_bytes(r.read())
    return p.read_text(encoding="utf-8")


def is_kaomoji_category(key: str) -> bool:
    return "kaomoji" in key.lower()


def slugify(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")


# ── UCD parsing (shared shape with scripts/verify.py) ───────────────────────

def parse_ranges(text: str) -> list[tuple[int, int, str]]:
    out = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        rng, val = (s.strip() for s in line.split(";")[:2])
        lo, _, hi = rng.partition("..")
        out.append((int(lo, 16), int(hi or lo, 16), val))
    return out


def lookup(ranges, cp: int):
    for lo, hi, v in ranges:
        if lo <= cp <= hi:
            return v
    return None


def emoji_props(text: str) -> dict[int, set[str]]:
    props: dict[int, set[str]] = {}
    for lo, hi, v in parse_ranges(text):
        for cp in range(lo, hi + 1):
            props.setdefault(cp, set()).add(v)
    return props


def emoji_test(text: str) -> dict[str, dict]:
    """sequence text -> {status, name, emoji_version} from emoji-test.txt."""
    out = {}
    pat = re.compile(r"^([0-9A-F ]+?)\s*;\s*([a-z-]+)\s*#\s*\S+\s+E(\d+\.\d+)\s+(.+)$")
    for line in text.splitlines():
        m = pat.match(line)
        if not m:
            continue
        seq = "".join(chr(int(h, 16)) for h in m.group(1).split())
        out[seq] = {"status": m.group(2), "emoji_version": m.group(3), "name": m.group(4).strip()}
    return out


def version_key(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


# ── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    if unicodedata.unidata_version != UNICODE_VERSION:
        sys.exit(
            f"[build] this Python's unicodedata is {unicodedata.unidata_version}, need {UNICODE_VERSION} "
            "(Python 3.14). Names must come from one pinned version."
        )

    # 1. pages: which categories have their own page
    pages = post("/pages", {})["List"]
    cat_page: dict[str, str] = {}
    alt_codes: dict[str, str] = {}
    for p in pages:
        if p["PageType"] != "symbol":
            continue
        detail = post("/page", {"Slug": p["Slug"]})
        try:
            cfg = json.loads(detail.get("ToolConfig") or "{}")
        except json.JSONDecodeError:
            cfg = {}
        cats = [c for c in cfg.get("categories") or [] if not is_kaomoji_category(c)]
        for c in cats:
            cat_page.setdefault(c, p["Slug"])
        if cats:
            for a in cfg.get("annotated") or []:
                if a.get("alt") and a.get("c"):
                    alt_codes[a["c"]] = a["alt"]

    # 2. symbols in every locale
    groups_by_locale = {}
    for loc in LOCALES:
        groups = post("/symbols", {}, loc)["Groups"]
        groups_by_locale[loc] = [g for g in groups if not is_kaomoji_category(g["Category"])]

    base = groups_by_locale["en"]
    for loc, gs in groups_by_locale.items():
        for g in gs:
            if g.get("Total") is not None and g["Total"] != len(g["Items"]):
                sys.exit(f"[build] {loc}/{g['Category']} was capped: {len(g['Items'])} of {g['Total']}")
        a = [(g["Category"], [i["Content"] for i in g["Items"]]) for g in gs]
        b = [(g["Category"], [i["Content"] for i in g["Items"]]) for g in base]
        if a != b:
            sys.exit(f"[build] locale {loc} serves a different symbol set from en — handle per-locale visibility first")

    # 3. UCD
    blocks = parse_ranges(ucd("Blocks.txt"))
    ages = parse_ranges(ucd("DerivedAge.txt"))
    eprops = emoji_props(ucd("emoji-data.txt"))
    etest = emoji_test(ucd("emoji-test.txt"))

    # 4. records
    # Entries containing an unassigned (Cn) or private-use (Co) code point are
    # not standard characters: they render as tofu or as whatever a font happens
    # to put there. They are dropped and listed in stats.json, never patched.
    excluded = []
    for g in base:
        keep = []
        for it in g["Items"]:
            bad = [f"U+{ord(c):04X}" for c in it["Content"] if unicodedata.category(c) in ("Cn", "Co")]
            if bad:
                excluded.append({"text": it["Content"], "category": g["Category"], "codepoints": bad,
                                 "reason": "unassigned or private-use code point in Unicode " + UNICODE_VERSION})
            else:
                keep.append(it)
        g["Items"] = keep

    categories = []
    records: dict[str, dict] = {}
    order: list[str] = []
    for gi, g in enumerate(base):
        key = g["Category"]
        labels = {loc: next(x["CategoryLabel"] for x in groups_by_locale[loc] if x["Category"] == key) for loc in LOCALES}
        slug = slugify(key)
        page = cat_page.get(key, GENERAL_PAGE)
        categories.append({
            "key": key,
            "slug": slug,
            "labels": labels,
            "count": len(g["Items"]),
            "fontvibe_page": f"{SITE}/tools/{page}",
            "dedicated_page": key in cat_page,
        })
        for it in g["Items"]:
            text = it["Content"]
            if text not in records:
                cps = [ord(c) for c in text]
                cp_ages = [lookup(ages, cp) for cp in cps]
                et = etest.get(text)
                records[text] = {
                    "text": text,
                    "categories": [],
                    "length": len(cps),
                    "codepoints": [f"U+{cp:04X}" for cp in cps],
                    "unicode_names": [unicodedata.name(chr(cp), None) for cp in cps],
                    "general_categories": [unicodedata.category(chr(cp)) for cp in cps],
                    "blocks": [lookup(blocks, cp) for cp in cps],
                    "ages": cp_ages,
                    "unicode_version": max(cp_ages, key=version_key) if all(cp_ages) else None,
                    "emoji": [("Emoji" in eprops.get(cp, ())) for cp in cps],
                    "emoji_presentation": [("Emoji_Presentation" in eprops.get(cp, ())) for cp in cps],
                    "emoji_status": et["status"] if et else None,
                    "emoji_name": et["name"] if et else None,
                    "alt_code": alt_codes.get(text),
                }
                order.append(text)
            if key not in records[text]["categories"]:
                records[text]["categories"].append(key)

    ordered = []
    for i, text in enumerate(order, 1):
        r = records[text]
        ordered.append({"id": f"sym_{i:05d}", **r})
    id_of = {r["text"]: r["id"] for r in ordered}

    # 5. write
    DATA.mkdir(exist_ok=True)
    bycat = DATA / "by-category"
    bycat.mkdir(exist_ok=True)
    for old in bycat.glob("*.json"):
        old.unlink()

    def dump(path: Path, obj) -> None:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    dump(DATA / "symbols.json", ordered)
    dump(DATA / "categories.json", categories)
    by_text = {r["text"]: r for r in ordered}
    for c, g in zip(categories, base):
        dump(bycat / f"{c['slug']}.json", {
            "category": c,
            "symbols": [by_text[i["Content"]] for i in g["Items"]],
        })

    with (DATA / "symbols.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "text", "categories", "codepoints", "unicode_names", "blocks",
                    "unicode_version", "emoji_status", "emoji_name", "alt_code"])
        for r in ordered:
            w.writerow([
                r["id"], r["text"], "|".join(r["categories"]), " ".join(r["codepoints"]),
                "|".join(n or "" for n in r["unicode_names"]), "|".join(b or "" for b in r["blocks"]),
                r["unicode_version"] or "", r["emoji_status"] or "", r["emoji_name"] or "", r["alt_code"] or "",
            ])

    cps = {cp for r in ordered for cp in r["codepoints"]}
    stats = {
        "symbols": len(ordered),
        "category_memberships": sum(c["count"] for c in categories),
        "categories": len(categories),
        "categories_with_dedicated_page": sum(1 for c in categories if c["dedicated_page"]),
        "single_code_point": sum(1 for r in ordered if r["length"] == 1),
        "multi_code_point": sum(1 for r in ordered if r["length"] > 1),
        "distinct_code_points": len(cps),
        "in_multiple_categories": sum(1 for r in ordered if len(r["categories"]) > 1),
        "rgi_emoji_fully_qualified": sum(1 for r in ordered if r["emoji_status"] == "fully-qualified"),
        "with_alt_code": sum(1 for r in ordered if r["alt_code"]),
        "locales": LOCALES,
        "unicode_version": UNICODE_VERSION,
        "emoji_version": EMOJI_VERSION,
        "per_category": {c["key"]: c["count"] for c in categories},
        "excluded": excluded,
        "snapshot_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    dump(DATA / "stats.json", stats)
    print(json.dumps({k: v for k, v in stats.items() if k not in ("per_category", "locales")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
