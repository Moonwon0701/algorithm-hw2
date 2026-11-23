import unittest

from src.hash_table import HashTable
from src.shortener import Shortener


class TestHashTableEdgeCases(unittest.TestCase):
    def test_capacity_is_fixed_and_load_factor_can_exceed_one(self):
        # 용량 13에 26개를 넣었을 때 자동 확장이 없으면 적재율은 정확히 2.0
        table = HashTable(13)
        for i in range(26):
            table.put(f"key{i}", i)
        self.assertEqual(len(table), 26)
        self.assertAlmostEqual(table.load_factor(), 2.0)
        for i in range(26):
            self.assertEqual(table.get(f"key{i}"), i)

    def test_miss_in_empty_bucket_compares_zero_nodes(self):
        table = HashTable(13)
        value, compared = table.find("https://nothing.example")
        self.assertIsNone(value)
        self.assertEqual(compared, 0)

    def test_miss_in_chain_compares_every_node(self):
        # 용량 2에서 한 글자 키의 버킷은 ord(글자) % 2.
        # a, c, e, g, i, k는 모두 홀수 코드라 같은 버킷(1)에 모인다.
        table = HashTable(2)
        for key in ["a", "c", "e", "g", "i"]:
            table.put(key, key)
        value, compared = table.find("k")
        self.assertIsNone(value)
        self.assertEqual(compared, 5)


class TestShortenerEdgeCases(unittest.TestCase):
    PREFIX = "https://a.com/"

    def setUp(self):
        self.shortener = Shortener(HashTable(13))

    def make_url(self, length):
        return self.PREFIX + "x" * (length - len(self.PREFIX))

    def test_exactly_2048_chars_is_accepted(self):
        url = self.make_url(2048)
        code = self.shortener.shorten(url)
        self.assertEqual(self.shortener.expand(code), url)

    def test_2049_chars_is_rejected(self):
        with self.assertRaises(ValueError):
            self.shortener.shorten(self.make_url(2049))

    def test_length_is_checked_after_stripping_outer_spaces(self):
        url = self.make_url(2048)
        code = self.shortener.shorten("  " + url + "  ")
        self.assertEqual(self.shortener.expand(code), url)

    def test_scheme_without_host_is_rejected(self):
        for url in ["http://", "https://", "https:///path"]:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    self.shortener.shorten(url)

    def test_works_when_urls_exceed_table_capacity(self):
        # 버킷 13개에 URL 30개(적재율 > 2)를 넣어도 모두 제대로 찾아야 함
        urls = [f"https://site{i}.example/" for i in range(30)]
        codes = [self.shortener.shorten(u) for u in urls]
        self.assertEqual(len(set(codes)), 30)
        for url, code in zip(urls, codes):
            self.assertEqual(self.shortener.expand(code), url)


if __name__ == "__main__":
    unittest.main()
