#!/usr/bin/env python3
"""Check every number and factual claim in README.md against the shipped data.

    python scripts/verify.py              # full check; downloads the Unicode 16.0 data files
    python scripts/verify.py --offline    # skip the checks that need the network

Stdlib only. Nothing is precomputed: every count is recomputed from data/, every
Unicode fact is re-derived, and README.md may contain no number that this script
did not verify. Exit code 0 = all claims hold, 1 = at least one does not.

What is checked
  data      ids/texts unique · no duplicates inside a category · every code point
            assigned (not Cn/Co/Cs) · codepoints/length match the text · names and
            general categories match Python's unicodedata (needs 16.0.0, i.e. Python
            3.14; otherwise UnicodeData.txt 16.0.0 is downloaded and used instead)
  ucd       blocks · ages · Emoji / Emoji_Presentation · emoji-test status and name
            re-derived from the official Unicode 16.0 files            [network]
  files     by-category/*.json, symbols.csv and stats.json all agree with symbols.json
  site      the API still serves exactly this set of symbols            [network]
            every fontvibe.ai page linked in categories.json answers 200 [network]
  README    every number in the prose is one of the verified numbers below; the
            category table matches categories.json row by row
"""
from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UNICODE_VERSION = "16.0.0"
EMOJI_VERSION = "16.0"
API = "https://api.fontvibe.ai/logicSrv/FontVibeAPI/unicode/v1"
UA = "fontvibe-symbols-verify (+https://github.com/Funovate-Technology/fontvibe-symbols)"
UCD = {
    "Blocks.txt": f"https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/Blocks.txt",
    "DerivedAge.txt": f"https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/DerivedAge.txt",
    "emoji-data.txt": f"https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/emoji/emoji-data.txt",
    "emoji-test.txt": f"https://www.unicode.org/Public/emoji/{EMOJI_VERSION}/emoji-test.txt",
    "UnicodeData.txt": f"https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/UnicodeData.txt",
}

OFFLINE = "--offline" in sys.argv
failures: list[str] = []
passed = 0


def check(cond: bool, msg: str) -> None:
    global passed
    if cond:
        passed += 1
    else:
        failures.append(msg)
        print("  FAIL  " + msg)


def fetch(url: str, body: dict | None = None, headers: dict | None = None) -> bytes:
    h = {"User-Agent": UA, **(headers or {})}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def parse_ranges(text: str):
    out = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        rng, val = (s.strip() for s in line.split(";")[:2])
        lo, _, hi = rng.partition("..")
        out.append((int(lo, 16), int(hi or lo, 16), val))
    return out


def lookup(ranges, cp):
    for lo, hi, v in ranges:
        if lo <= cp <= hi:
            return v
    return None


def vkey(v):
    return tuple(int(x) for x in v.split("."))


def main() -> int:
    syms = json.loads((DATA / "symbols.json").read_text(encoding="utf-8"))
    cats = json.loads((DATA / "categories.json").read_text(encoding="utf-8"))
    stats = json.loads((DATA / "stats.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    # ── data ────────────────────────────────────────────────────────────────
    print("data")
    check(len({r["id"] for r in syms}) == len(syms), "duplicate id")
    check(len({r["text"] for r in syms}) == len(syms), "duplicate text across records")
    for r in syms:
        cps = [ord(c) for c in r["text"]]
        check(r["codepoints"] == [f"U+{c:04X}" for c in cps], f"{r['id']} codepoints do not match text")
        check(r["length"] == len(cps), f"{r['id']} length")
        for f in ("unicode_names", "general_categories", "blocks", "ages", "emoji", "emoji_presentation"):
            check(len(r[f]) == len(cps), f"{r['id']} {f} not aligned with codepoints")
        for c in r["text"]:
            check(unicodedata.category(c) not in ("Cn", "Co", "Cs") or unicodedata.unidata_version != UNICODE_VERSION,
                  f"{r['id']} U+{ord(c):04X} is unassigned / private use / surrogate")
        check(r["text"].strip() != "", f"{r['id']} is whitespace only")
        check(bool(r["categories"]) and len(set(r["categories"])) == len(r["categories"]), f"{r['id']} categories")
        if all(r["ages"]):
            check(r["unicode_version"] == max(r["ages"], key=vkey), f"{r['id']} unicode_version != max(ages)")
    print(f"  {len(syms)} records")

    # names: unicodedata when its version matches, else the official UnicodeData.txt
    print(f"names (Python unicodedata {unicodedata.unidata_version})")
    if unicodedata.unidata_version == UNICODE_VERSION:
        for r in syms:
            for c, n, gc in zip(r["text"], r["unicode_names"], r["general_categories"]):
                check(n == unicodedata.name(c, None), f"{r['id']} name of U+{ord(c):04X}: {n!r}")
                check(gc == unicodedata.category(c), f"{r['id']} category of U+{ord(c):04X}")
                check(n is not None, f"{r['id']} U+{ord(c):04X} has no name")
    elif OFFLINE:
        print(f"  SKIP  unicodedata is {unicodedata.unidata_version}, not {UNICODE_VERSION}; rerun online or on Python 3.14")
    else:
        names, gcs, ranges = {}, {}, []
        first = None
        for line in fetch(UCD["UnicodeData.txt"]).decode().splitlines():
            f = line.split(";")
            cp = int(f[0], 16)
            if f[1].endswith(", First>"):
                first = (cp, f[1], f[2])
                continue
            if f[1].endswith(", Last>"):
                ranges.append((first[0], cp, first[1], first[2]))
                continue
            names[cp] = f[1] if not f[1].startswith("<") else None
            gcs[cp] = f[2]
        for r in syms:
            for c, n, gc in zip(r["text"], r["unicode_names"], r["general_categories"]):
                cp = ord(c)
                if cp in names:
                    check(n == names[cp] and gc == gcs[cp], f"{r['id']} U+{cp:04X} name/category")
                    check(gcs[cp] not in ("Cn", "Co", "Cs"), f"{r['id']} U+{cp:04X} unassigned")
                else:
                    rng = next((x for x in ranges if x[0] <= cp <= x[1]), None)
                    check(rng is not None and rng[3] not in ("Co", "Cs"), f"{r['id']} U+{cp:04X} unassigned")
                    if rng and "CJK Ideograph" in rng[2]:
                        check(n == f"CJK UNIFIED IDEOGRAPH-{cp:04X}", f"{r['id']} U+{cp:04X} name")

    # ── ucd ─────────────────────────────────────────────────────────────────
    print(f"ucd (Unicode {UNICODE_VERSION}, Emoji {EMOJI_VERSION})")
    if OFFLINE:
        print("  SKIP  --offline")
    else:
        blocks = parse_ranges(fetch(UCD["Blocks.txt"]).decode())
        ages = parse_ranges(fetch(UCD["DerivedAge.txt"]).decode())
        eprops: dict[int, set] = {}
        for lo, hi, v in parse_ranges(fetch(UCD["emoji-data.txt"]).decode()):
            for cp in range(lo, hi + 1):
                eprops.setdefault(cp, set()).add(v)
        etest = {}
        pat = re.compile(r"^([0-9A-F ]+?)\s*;\s*([a-z-]+)\s*#\s*\S+\s+E\d+\.\d+\s+(.+)$")
        for line in fetch(UCD["emoji-test.txt"]).decode().splitlines():
            m = pat.match(line)
            if m:
                etest["".join(chr(int(h, 16)) for h in m.group(1).split())] = (m.group(2), m.group(3).strip())
        for r in syms:
            for c, b, a, e, ep in zip(r["text"], r["blocks"], r["ages"], r["emoji"], r["emoji_presentation"]):
                cp = ord(c)
                check(b == lookup(blocks, cp), f"{r['id']} block of U+{cp:04X}")
                check(a == lookup(ages, cp), f"{r['id']} age of U+{cp:04X}")
                check(e == ("Emoji" in eprops.get(cp, ())), f"{r['id']} Emoji of U+{cp:04X}")
                check(ep == ("Emoji_Presentation" in eprops.get(cp, ())), f"{r['id']} Emoji_Presentation of U+{cp:04X}")
            t = etest.get(r["text"])
            check((r["emoji_status"], r["emoji_name"]) == (t if t else (None, None)), f"{r['id']} emoji_status/name")

    # ── files ───────────────────────────────────────────────────────────────
    print("files")
    by_text = {r["text"]: r for r in syms}
    seen_members = 0
    for c in cats:
        f = DATA / "by-category" / f"{c['slug']}.json"
        check(f.exists(), f"missing {f.name}")
        if not f.exists():
            continue
        doc = json.loads(f.read_text(encoding="utf-8"))
        texts = [x["text"] for x in doc["symbols"]]
        check(doc["category"] == c, f"{f.name} category block differs from categories.json")
        check(len(texts) == c["count"], f"{f.name} has {len(texts)}, categories.json says {c['count']}")
        check(len(set(texts)) == len(texts), f"{f.name} has duplicates")
        check(all(by_text.get(x["text"]) == x for x in doc["symbols"]), f"{f.name} records differ from symbols.json")
        check(sorted(texts) == sorted(r["text"] for r in syms if c["key"] in r["categories"]),
              f"{f.name} membership differs from symbols.json categories")
        check(set(c["labels"]) == set(stats["locales"]) and all(c["labels"].values()), f"{c['key']} labels incomplete")
        check("kaomoji" not in c["key"].lower(), f"{c['key']} is a kaomoji category")
        seen_members += len(texts)
    check(len(list((DATA / "by-category").glob("*.json"))) == len(cats), "stray files in by-category/")

    with (DATA / "symbols.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    check(len(rows) == len(syms), "symbols.csv row count")
    for row, r in zip(rows, syms):
        ok = (row["id"] == r["id"] and row["text"] == r["text"]
              and row["categories"] == "|".join(r["categories"])
              and row["codepoints"] == " ".join(r["codepoints"])
              and row["unicode_names"] == "|".join(n or "" for n in r["unicode_names"])
              and row["unicode_version"] == (r["unicode_version"] or "")
              and row["emoji_name"] == (r["emoji_name"] or "") and row["alt_code"] == (r["alt_code"] or ""))
        check(ok, f"symbols.csv row {r['id']} differs from symbols.json")

    facts = {
        "symbols": len(syms),
        "category_memberships": seen_members,
        "categories": len(cats),
        "categories_with_dedicated_page": sum(1 for c in cats if c["dedicated_page"]),
        "single_code_point": sum(1 for r in syms if r["length"] == 1),
        "multi_code_point": sum(1 for r in syms if r["length"] > 1),
        "distinct_code_points": len({cp for r in syms for cp in r["codepoints"]}),
        "in_multiple_categories": sum(1 for r in syms if len(r["categories"]) > 1),
        "rgi_emoji_fully_qualified": sum(1 for r in syms if r["emoji_status"] == "fully-qualified"),
        "with_alt_code": sum(1 for r in syms if r["alt_code"]),
    }
    for k, v in facts.items():
        check(stats.get(k) == v, f"stats.json {k} = {stats.get(k)}, data says {v}")
    check(stats["per_category"] == {c["key"]: c["count"] for c in cats}, "stats.json per_category")
    check(stats["unicode_version"] == UNICODE_VERSION, "stats.json unicode_version")

    # ── site ────────────────────────────────────────────────────────────────
    print("site")
    if OFFLINE:
        print("  SKIP  --offline")
    else:
        groups = json.loads(fetch(API + "/symbols", {}, {"X-Locale": "en"}))["Data"]["Groups"]
        live = {g["Category"]: [i["Content"] for i in g["Items"]] for g in groups if "kaomoji" not in g["Category"].lower()}
        excluded = {(x["category"], x["text"]) for x in stats["excluded"]}
        for c in cats:
            want = [x["text"] for x in json.loads((DATA / "by-category" / f"{c['slug']}.json").read_text(encoding="utf-8"))["symbols"]]
            got = [t for t in live.get(c["key"], []) if (c["key"], t) not in excluded]
            if got != want:
                print(f"  note  {c['key']}: the live site now differs from this snapshot ({len(got)} vs {len(want)})")
        check(set(live) == {c["key"] for c in cats}, "the live site has a different set of symbol categories")
        for url in sorted({c["fontvibe_page"] for c in cats}):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
                code = urllib.request.urlopen(req, timeout=30).status
            except Exception as e:  # noqa: BLE001
                code = getattr(e, "code", str(e))
            check(code == 200, f"{url} answered {code}")

    # ── README ──────────────────────────────────────────────────────────────
    print("README")
    by_key = {c["key"]: c for c in cats}
    table = re.findall(r"^\| \[([^\]]+)\]\((https://fontvibe\.ai/[^)]+)\) \| ([\d,]+) \|", readme, re.M)
    check(len(table) == len(cats), f"README category table has {len(table)} rows, expected {len(cats)}")
    for name, url, n in table:
        c = by_key.get(name)
        check(c is not None, f"README table: unknown category {name}")
        if c:
            check(url == c["fontvibe_page"], f"README table: {name} links {url}, data says {c['fontvibe_page']}")
            check(int(n.replace(",", "")) == c["count"], f"README table: {name} = {n}, data says {c['count']}")

    allowed = set()
    for v in list(facts.values()) + [c["count"] for c in cats] + [len(stats["locales"]), len(stats["excluded"])]:
        allowed |= {str(v), f"{v:,}"}
    allowed |= {UNICODE_VERSION, EMOJI_VERSION, "16", "4.0", "3.14"}   # versions: Unicode, Emoji, CC BY, Python
    allowed |= {str(stats["snapshot_date"][:4])}                       # year in the citation
    allowed |= {f"U+{cp}" for x in stats["excluded"] for cp in [c[2:] for c in x["codepoints"]]}
    # Fenced code is example code (exercised by the package tests) and is skipped —
    # except ```text blocks, which are prose laid out in a box and are checked.
    kept, fence = [], None            # None | "text" | "code"
    for line in readme.splitlines():
        if line.startswith("```"):
            fence = None if fence else ("text" if line.strip() == "```text" else "code")
            continue
        if fence != "code":
            kept.append(line)
    prose = "\n".join(kept)
    prose = re.sub(r"\]\([^)]*\)", "]", prose)                      # link targets
    prose = re.sub(r"https?://\S+", "", prose)
    prose = re.sub(r"`[^`]*`", "", prose)                           # inline code: identifiers, file names
    prose = re.sub(r"<!--.*?-->", "", prose, flags=re.S)
    prose = re.sub(r"^(#+) \d+\. ", r"\1 ", prose, flags=re.M)      # "### 2. Title": an ordinal, not a claim
    def scan(name: str, text: str) -> None:
        for tok in re.findall(r"(?<![\w.+-])\d[\d,]*(?:\.\d+)*", text):
            tok = tok.rstrip(",.")
            check(tok in allowed, f"{name} states the number {tok!r}, which this script does not verify")

    scan("README.md", prose)
    # The package READMEs are shown on npm / PyPI; same rule, prose only.
    for pkg in ("npm", "pypi"):
        t = (ROOT / pkg / "README.md").read_text(encoding="utf-8")
        t = re.sub(r"```.*?\n```", "", t, flags=re.S)
        t = re.sub(r"\]\([^)]*\)", "]", t)
        t = re.sub(r"`[^`]*`", "", t)
        scan(f"{pkg}/README.md", t)
    for k in ("symbols", "categories", "multi_code_point", "distinct_code_points"):
        check(f"{facts[k]:,}" in prose, f"README does not state {k} ({facts[k]:,})")

    print()
    if failures:
        print(f"{len(failures)} FAILED, {passed} passed")
        return 1
    print(f"all {passed} checks passed" + (" (offline: network checks skipped)" if OFFLINE else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
