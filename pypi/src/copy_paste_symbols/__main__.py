"""python -m copy_paste_symbols heart -n 5"""

from __future__ import annotations

import argparse
import json
import re
import sys

from . import by_category, categories, get, random, search, stats


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="copy-paste-symbols",
        description=f"{stats['symbols']:,} copy-and-paste symbols in {stats['categories']} categories. "
        "Data CC BY 4.0 · https://fontvibe.ai/tools/heart-symbol",
    )
    p.add_argument("query", nargs="*", help="Unicode/emoji name, category, or a code point like U+2665")
    p.add_argument("-c", "--category", help="category key, slug, or label in en/es/pt/de/ja/zh")
    p.add_argument("-n", "--limit", type=int, default=10)
    p.add_argument("--categories", action="store_true", help="list categories")
    p.add_argument("--stats", action="store_true", help="dataset totals")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    a = p.parse_args(argv)

    if a.stats:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0
    if a.categories:
        for c in categories():
            print(f"{c['count']:>5}  {c['key']:<14}{c['fontvibe_page']}")
        return 0

    q = " ".join(a.query)
    if re.match(r"^U\+[0-9A-Fa-f]{4,6}$", q, re.I):
        r = get(q)
        results = [r] if r else []
    elif q:
        results = search(q, category=a.category, limit=a.limit)
    elif a.category:
        results = by_category(a.category, limit=a.limit)
    else:
        results = [random()]

    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    if not results:
        print(f'no match for "{q or a.category}"', file=sys.stderr)
        return 1
    for r in results:
        label = r["emoji_name"] or (r["unicode_names"][0] if r["length"] == 1 else " ".join(r["codepoints"]))
        print(f"{r['text']}  {label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
