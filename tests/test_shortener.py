import unittest

from src.hash_table import HashTable
from src.shortener import Shortener


class ShortenerTests(unittest.TestCase):
    def setUp(self):
        self.shortener = Shortener(HashTable(capacity=13))

    def test_shortens_and_expands_urls_with_sequential_codes(self):
        first_url = "https://example.com"
        second_url = "https://example.org/path"

        first_code = self.shortener.shorten(first_url)
        second_code = self.shortener.shorten(second_url)

        self.assertEqual((first_code, second_code), ("0", "1"))
        self.assertEqual(self.shortener.expand(first_code), first_url)
        self.assertEqual(self.shortener.expand(second_code), second_url)

    def test_strips_outer_whitespace_and_reuses_duplicate_code(self):
        url = "https://example.com/path"

        code = self.shortener.shorten(f"  {url}\n")

        self.assertEqual(self.shortener.shorten(url), code)
        self.assertEqual(self.shortener.expand(code), url)

    def test_distinct_unormalized_urls_get_distinct_codes(self):
        without_slash = self.shortener.shorten("https://example.com")
        with_slash = self.shortener.shorten("https://example.com/")
        self.assertNotEqual(without_slash, with_slash)

    def test_rejects_invalid_urls(self):
        invalid_urls = (
            "",
            "ftp://example.com",
            "http://",
            "https://example.com/a b",
            "https://" + "a" * 2041,
        )
        for url in invalid_urls:
            with self.subTest(url=url[:30]):
                with self.assertRaises(ValueError):
                    self.shortener.shorten(url)

    def test_unknown_or_invalid_codes_return_none(self):
        for code in ("", "!", "z"):
            with self.subTest(code=code):
                self.assertIsNone(self.shortener.expand(code))


if __name__ == "__main__":
    unittest.main()
