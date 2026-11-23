"""In-memory URL shortening backed by a custom hash table."""

from urllib.parse import urlsplit

from src.base62 import decode, encode
from src.hash_table import HashTable


class Shortener:
    MAX_URL_LENGTH = 2048

    def __init__(self, table: HashTable):
        self.table = table
        self._urls: list[str] = []

    def shorten(self, url: str) -> str:
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        url = url.strip()
        self._validate_url(url)

        existing_code, _ = self.table.find(url)
        if existing_code is not None:
            return existing_code

        code = encode(len(self._urls))
        self.table.put(url, code)
        self._urls.append(url)
        return code

    def expand(self, code: str) -> str | None:
        if not isinstance(code, str):
            return None
        try:
            index = decode(code)
        except ValueError:
            return None
        if index >= len(self._urls):
            return None
        return self._urls[index]

    @classmethod
    def _validate_url(cls, url: str) -> None:
        if not url:
            raise ValueError("url must not be empty")
        if len(url) > cls.MAX_URL_LENGTH:
            raise ValueError("url is too long")
        if any(character.isspace() for character in url):
            raise ValueError("url must not contain whitespace")

        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            parsed.port
        except ValueError as error:
            raise ValueError("url is invalid") from error
        if parsed.scheme.lower() not in ("http", "https") or not hostname:
            raise ValueError("url must be an HTTP(S) URL with a host")
