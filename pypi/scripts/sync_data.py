#!/usr/bin/env python3
"""Copy the dataset from the repo root into the package before building or testing.

data/ at the repo root is the single source of truth; it is never committed twice.
stats.json is copied too — a hand-copied stats file goes stale the first time the
data is rebuilt.
"""
import json
import shutil
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2] / "data"
pkg = Path(__file__).resolve().parents[1] / "src" / "copy_paste_symbols"

for f in ("symbols.json", "categories.json", "stats.json"):
    if not (root / f).exists():
        sys.exit(f"[sync-data] missing {root / f} — run this from inside the repo")

(pkg / "data").mkdir(parents=True, exist_ok=True)
for f in ("symbols.json", "categories.json"):
    obj = json.loads((root / f).read_text(encoding="utf-8"))
    # Same content, no indentation: smaller wheel.
    (pkg / "data" / f).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
shutil.copyfile(root / "stats.json", pkg / "stats.json")

n = len(json.loads((pkg / "data" / "symbols.json").read_text(encoding="utf-8")))
expected = json.loads((pkg / "stats.json").read_text(encoding="utf-8"))["symbols"]
if n != expected:
    sys.exit(f"[sync-data] copied {n} symbols but stats.json says {expected} — refusing to build")
print(f"[sync-data] ok — {n} symbols + categories.json + stats.json")
