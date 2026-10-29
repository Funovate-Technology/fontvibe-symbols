"""FontVibe's copy-and-paste symbol library, with Unicode facts for every code point.

    >>> import copy_paste_symbols as cps
    >>> cps.get("U+2665")["unicode_names"]
    ['BLACK HEART SUIT']
    >>> len(cps.by_category("Corazones")) == len(cps.by_category("Hearts"))
    True

Category names work in English, Spanish, Portuguese, German, Japanese and Chinese.

Data licensed CC BY 4.0 (attribution required); code MIT.
Browse and copy: https://fontvibe.ai/tools/heart-symbol
"""

from __future__ import annotations

import json
import random as _random
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

__version__ = "1.0.0"

LANGS = ("en", "es", "pt", "de", "ja", "zh")

_HERE = Path(__file__).parent
_DATA = _HERE / "data"

Symbol = Dict[str, Any]

_all: Optional[List[Symbol]] = None
_cats: Optional[List[Dict[str, Any]]] = None


def _load(name: str) -> Any:
    p = _DATA / name
    if not p.exists():
        raise FileNotFoundError(
            f"copy-paste-symbols: data file is missing ({p}). The package was probably "
            "built without running scripts/sync_data.py; please open an issue at "
            "https://github.com/Funovate-Technology/fontvibe-symbols/issues"
        )
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


def all() -> List[Symbol]:  # noqa: A001 - mirrors the JavaScript package
    """Every symbol record, parsed once and cached."""
    global _all
    if _all is None:
        _all = _load("symbols.json")
    return _all


load = all  # for anyone who would rather not shadow the builtin


def categories() -> List[Dict[str, Any]]:
    """Every category: key, slug, labels in six languages, count and fontvibe.ai page."""
    global _cats
    if _cats is None:
        _cats = _load("categories.json")
    return _cats


def _norm(value: Any) -> str:
    return ("" if value is None else str(value)).strip().lower()


def _take(items: List[Symbol], limit: Optional[int]) -> List[Symbol]:
    """A negative limit means "no limit"; it must never fall through to ``items[:-n]``."""
    if limit is None or limit < 0:
        return items
    return items[:limit]


def find_category(name: str) -> Optional[Dict[str, Any]]:
    """Resolve a category by key ("Hearts"), slug ("heart-combos") or a label in any language."""
    q = _norm(name)
    if not q:
        return None
    for c in categories():
        if _norm(c["key"]) == q or c["slug"] == q or any(_norm(c["labels"][l]) == q for l in LANGS):
            return c
    return None


def by_category(name: str, limit: Optional[int] = None) -> List[Symbol]:
    """Symbols in one category, in the order fontvibe.ai shows them."""
    c = find_category(name)
    if not c:
        return []
    return _take([r for r in all() if c["key"] in r["categories"]], limit)


_CP = re.compile(r"^U\+([0-9A-Fa-f]{4,6})$", re.I)


def get(text_or_codepoint: str) -> Optional[Symbol]:
    """Look up one symbol by exact text, or by a code point like ``"U+2665"``."""
    s = "" if text_or_codepoint is None else str(text_or_codepoint)
    m = _CP.match(s.strip())
    if m:
        cp = "U+" + m.group(1).upper().rjust(4, "0")
        return next((r for r in all() if r["length"] == 1 and r["codepoints"][0] == cp), None)
    return next((r for r in all() if r["text"] == s), None)


def search(query: str, category: Optional[str] = None, limit: Optional[int] = 50) -> List[Symbol]:
    """Search by Unicode name, CLDR emoji name, or category (key or label in six languages).

    Exact category or name matches rank above word matches, which rank above
    substring matches; within a rank, single characters come before combos.
    """
    q = _norm(query)
    if not q:
        return []
    cat = find_category(category) if category else None
    if category and not cat:
        return []
    cat_hits, cat_prefix = set(), set()
    for c in categories():
        labels = [_norm(c["key"]), c["slug"]] + [_norm(c["labels"][l]) for l in LANGS]
        if q in labels:
            cat_hits.add(c["key"])
        elif len(q) >= 3 and any(x.startswith(q) for x in labels):
            cat_prefix.add(c["key"])
    by_key = {c["key"]: c for c in categories()}
    hits = []
    for r in all():
        if cat and cat["key"] not in r["categories"]:
            continue
        score = 4 if r["text"] == query else 0
        if any(k in cat_hits for k in r["categories"]):
            score = max(score, 3)
        if any(k in cat_prefix for k in r["categories"]):
            score = max(score, 2)
        names = [_norm(n) for n in r["unicode_names"] if n]
        if r.get("emoji_name"):
            names.append(_norm(r["emoji_name"]))
        for n in names:
            if n == q:
                score = max(score, 3)
            elif q in re.split(r"[\s-]+", n):
                score = max(score, 2)
            elif q in n:
                score = max(score, 1)
        if not score and any(
            q in _norm(by_key[k]["labels"][l]) for k in r["categories"] for l in LANGS
        ):
            score = 1
        if score:
            hits.append((score, r))
    hits.sort(key=lambda p: (-p[0], p[1]["length"]))  # stable: site order within ties
    return _take([r for _, r in hits], limit)


def random(category: Optional[str] = None) -> Optional[Symbol]:
    """One random symbol, optionally from one category; ``None`` when nothing matches."""
    pool = by_category(category) if category else all()
    return _random.choice(pool) if pool else None


with (_HERE / "stats.json").open(encoding="utf-8") as _fh:
    stats: Dict[str, Any] = json.load(_fh)

__all__ = [
    "all",
    "load",
    "categories",
    "find_category",
    "by_category",
    "get",
    "search",
    "random",
    "stats",
    "LANGS",
    "Symbol",
    "__version__",
]
