import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_put_get_update_and_size(self):
        table = HashTable(capacity=3)
        table.put("one", 1)
        table.put("two", 2)

        self.assertEqual(table.get("one"), 1)
        self.assertEqual(table.get("two"), 2)
        self.assertIsNone(table.get("missing"))
        self.assertEqual(len(table), 2)
        self.assertIn("one", table)
        self.assertNotIn("missing", table)

        table.put("one", 10)
        self.assertEqual(table.get("one"), 10)
        self.assertEqual(len(table), 2)

    def test_chains_collisions_and_reports_compared_nodes(self):
        table = HashTable(capacity=3)
        for key in ("a", "d", "g", "j"):
            table.put(key, key.upper())

        self.assertEqual(len(table), 4)
        self.assertAlmostEqual(table.load_factor(), 4 / 3)
        for key in ("a", "d", "g", "j"):
            value, comparisons = table.find(key)
            self.assertEqual(value, key.upper())
            self.assertGreaterEqual(comparisons, 1)
            self.assertLessEqual(comparisons, 4)

        self.assertEqual(table.find("b"), (None, 0))

    def test_find_counts_each_key_comparison(self):
        table = HashTable(capacity=3)
        table.put("a", 1)
        value, comparisons = table.find("a")
        self.assertEqual(value, 1)
        self.assertEqual(comparisons, 1)


if __name__ == "__main__":
    unittest.main()
