"""Plain unittest, no third-party test runner."""

import unittest

import copy_paste_symbols as cps


class TestDataset(unittest.TestCase):
    def test_all_matches_stats(self):
        self.assertEqual(len(cps.all()), cps.stats["symbols"])

    def test_ids_and_texts_unique(self):
        self.assertEqual(len({r["id"] for r in cps.all()}), cps.stats["symbols"])
        self.assertEqual(len({r["text"] for r in cps.all()}), cps.stats["symbols"])

    def test_record_shape(self):
        for r in cps.all():
            self.assertTrue(r["text"] and r["categories"])
            self.assertEqual(len(r["text"]), r["length"])
            for f in ("codepoints", "unicode_names", "blocks", "ages", "emoji"):
                self.assertEqual(len(r[f]), r["length"], f)

    def test_category_counts(self):
        cats = cps.categories()
        self.assertEqual(len(cats), cps.stats["categories"])
        for c in cats:
            self.assertEqual(len(cps.by_category(c["key"])), c["count"], c["key"])

    def test_category_resolves_in_every_language(self):
        hearts = next(c for c in cps.categories() if c["key"] == "Hearts")
        n = len(cps.by_category("Hearts"))
        self.assertGreater(n, 0)
        for lang in cps.LANGS:
            self.assertEqual(len(cps.by_category(hearts["labels"][lang])), n, lang)
        self.assertEqual(len(cps.by_category("heart-combos")), cps.stats["per_category"]["Heart Combos"])

    def test_no_kaomoji_category(self):
        for c in cps.categories():
            self.assertNotIn("kaomoji", c["key"].lower())

    def test_get(self):
        self.assertEqual(cps.get("♥")["codepoints"], ["U+2665"])
        self.assertEqual(cps.get("U+2665")["text"], "♥")
        self.assertEqual(cps.get("u+2665")["text"], "♥")
        self.assertIsNone(cps.get("not a symbol"))

    def test_search_by_name(self):
        self.assertEqual(len(cps.search("heart", limit=5)), 5)
        self.assertEqual(cps.search("black heart suit")[0]["text"], "♥")

    def test_search_cross_lingual_category(self):
        self.assertGreaterEqual(len(cps.search("Corazones", limit=-1)), cps.stats["per_category"]["Hearts"])

    def test_search_limit_and_category(self):
        self.assertEqual(len(cps.search("arrow", limit=3)), 3)
        self.assertLessEqual(len(cps.search("arrow")), 50)
        self.assertEqual(cps.search("arrow", limit=0), [])
        for r in cps.search("arrow", category="Arrows", limit=-1):
            self.assertIn("Arrows", r["categories"])
        self.assertEqual(cps.search("arrow", category="no-such-category"), [])

    def test_search_of_nonsense(self):
        self.assertEqual(cps.search("zzzzqqqqxxxx"), [])

    def test_random(self):
        for _ in range(50):
            self.assertIn("Stars", cps.random(category="Stars")["categories"])
        self.assertIsNone(cps.random(category="no-such-category"))

    def test_same_results_as_npm_ordering_rule(self):
        # singles before combos within a score tier
        res = cps.search("star", limit=6)
        self.assertTrue(all(r["length"] == 1 for r in res))


if __name__ == "__main__":
    unittest.main()
