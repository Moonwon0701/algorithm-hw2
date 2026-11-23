import unittest

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


class TableContractTests(unittest.TestCase):
    def test_tables_share_the_hash_table_contract(self):
        for table_type in (HashTable, LinearProbingHashTable):
            with self.subTest(table_type=table_type.__name__):
                table = table_type(capacity=3)
                for key in ("a", "d", "g"):
                    table.put(key, key.upper())

                self.assertEqual(len(table), 3)
                for key in ("a", "d", "g"):
                    self.assertIn(key, table)
                    self.assertEqual(table.get(key), key.upper())
                self.assertNotIn("missing", table)
                self.assertIsNone(table.get("missing"))

                table.put("d", "updated")
                self.assertEqual(table.get("d"), "updated")
                self.assertEqual(len(table), 3)

    def test_tables_reject_non_prime_capacity(self):
        for table_type in (HashTable, LinearProbingHashTable):
            with self.subTest(table_type=table_type.__name__):
                with self.assertRaises(ValueError):
                    table_type(capacity=4)


if __name__ == "__main__":
    unittest.main()
