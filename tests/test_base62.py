import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_zero_round_trips_as_zero_digit(self):
        self.assertEqual(encode(0), "0")
        self.assertEqual(decode("0"), 0)

    def test_digit_boundaries_follow_alphabet_order(self):
        self.assertEqual(encode(9), "9")
        self.assertEqual(encode(10), "a")
        self.assertEqual(encode(35), "z")
        self.assertEqual(encode(36), "A")
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")

    def test_round_trips_large_values(self):
        for number in (1, 61, 62, 3844, 2**128):
            with self.subTest(number=number):
                self.assertEqual(decode(encode(number)), number)

    def test_encode_rejects_negative_and_non_integer_values(self):
        with self.assertRaises(ValueError):
            encode(-1)
        with self.assertRaises(TypeError):
            encode(1.5)

    def test_decode_rejects_empty_and_invalid_values(self):
        with self.assertRaises(ValueError):
            decode("")
        with self.assertRaises(ValueError):
            decode("!")
        with self.assertRaises(TypeError):
            decode(12)


if __name__ == "__main__":
    unittest.main()
