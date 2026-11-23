"""A fixed-capacity hash table using separate chaining."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass(slots=True)
class HashNode:
    key: str
    value: object
    next: HashNode | None = None


class HashTable:
    def __init__(self, capacity: int = 13):
        if not isinstance(capacity, int) or isinstance(capacity, bool):
            raise TypeError("capacity must be an integer")
        if capacity < 2:
            raise ValueError("capacity must be a prime number")
        divisor = 2
        while divisor * divisor <= capacity:
            if capacity % divisor == 0:
                raise ValueError("capacity must be a prime number")
            divisor += 1

        self.capacity = capacity
        self.buckets: list[HashNode | None] = [None] * capacity
        self._size = 0

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

    def hash_trace(self, key: str) -> list[tuple[str, int, int]]:
        self._validate_key(key)
        value = 0
        trace = []
        for character in key:
            previous = value
            value = (31 * value + ord(character)) % self.capacity
            trace.append((character, previous, value))
        return trace

    def bucket_index(self, key: str) -> int:
        self._validate_key(key)
        value = 0
        for character in key:
            value = (31 * value + ord(character)) % self.capacity
        return value

    def put(self, key: str, value: object) -> None:
        self._validate_key(key)
        index = self.bucket_index(key)
        node = self.buckets[index]
        if node is None:
            self.buckets[index] = HashNode(key, value)
            self._size += 1
            return

        while True:
            if node.key == key:
                node.value = value
                return
            if node.next is None:
                node.next = HashNode(key, value)
                self._size += 1
                return
            node = node.next

    def find(self, key: str) -> tuple[object | None, int]:
        self._validate_key(key)
        node = self.buckets[self.bucket_index(key)]
        comparisons = 0
        while node is not None:
            comparisons += 1
            if node.key == key:
                return node.value, comparisons
            node = node.next
        return None, comparisons

    def get(self, key: str) -> object | None:
        value, _ = self.find(key)
        return value

    def load_factor(self) -> float:
        return self._size / self.capacity

    def iter_buckets(self) -> Iterator[tuple[int, HashNode | None]]:
        return iter(enumerate(self.buckets))

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        node = self.buckets[self.bucket_index(key)]
        while node is not None:
            if node.key == key:
                return True
            node = node.next
        return False
