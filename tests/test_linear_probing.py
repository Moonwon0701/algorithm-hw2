import unittest

from src.linear_probing import LinearProbingHashTable


class LinearProbingTests(unittest.TestCase):
    def test_probes_from_last_slot_to_zero(self):
        table = LinearProbingHashTable(capacity=5)

        table.put("1", "last")
        table.put("6", "zero")

        self.assertEqual(table.slots[4], ("1", "last"))
        self.assertEqual(table.slots[0], ("6", "zero"))
        self.assertEqual(table.get("1"), "last")
        self.assertEqual(table.get("6"), "zero")

    def test_keys_with_same_start_slot_form_a_cluster(self):
        table = LinearProbingHashTable(capacity=7)

        for key in ("a", "h", "o"):
            table.put(key, key.upper())

        self.assertEqual(
            table.slots[6:7] + table.slots[0:2],
            [("a", "A"), ("h", "H"), ("o", "O")],
        )
        for key in ("a", "h", "o"):
            self.assertEqual(table.get(key), key.upper())

    def test_find_counts_each_inspected_slot_including_empty_slots(self):
        table = LinearProbingHashTable(capacity=7)
        self.assertEqual(table.find("missing"), (None, 1))

        for key in ("a", "h", "o"):
            table.put(key, key.upper())

        value, probes = table.find("h")
        self.assertEqual(value, "H")
        self.assertEqual(probes, 2)

        self.assertEqual(table.find("v"), (None, 4))

    def test_full_table_updates_existing_key_and_rejects_new_key(self):
        table = LinearProbingHashTable(capacity=2)
        table.put("a", 1)
        table.put("b", 2)

        with self.assertRaises(OverflowError):
            table.put("c", 3)

        table.put("a", 10)
        self.assertEqual(table.get("a"), 10)
        self.assertEqual(table.find("d"), (None, 2))
        self.assertEqual(len(table), 2)
        self.assertEqual(table.load_factor(), 1)


if __name__ == "__main__":
    unittest.main()
