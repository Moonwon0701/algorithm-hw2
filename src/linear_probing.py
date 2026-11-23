"""A fixed-capacity hash table using linear probing."""

from __future__ import annotations


class LinearProbingHashTable:
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
        self.slots: list[tuple[str, object] | None] = [None] * capacity
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
        start = self.bucket_index(key)
        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            slot = self.slots[index]
            if slot is None:
                self.slots[index] = (key, value)
                self._size += 1
                return
            if slot[0] == key:
                self.slots[index] = (key, value)
                return
        raise OverflowError("hash table is full")

    def find(self, key: str) -> tuple[object | None, int]:
        self._validate_key(key)
        start = self.bucket_index(key)
        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            slot = self.slots[index]
            probes = offset + 1
            if slot is None:
                return None, probes
            if slot[0] == key:
                return slot[1], probes
        return None, self.capacity

    def get(self, key: str) -> object | None:
        value, _ = self.find(key)
        return value

    def load_factor(self) -> float:
        return self._size / self.capacity

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        start = self.bucket_index(key)
        for offset in range(self.capacity):
            slot = self.slots[(start + offset) % self.capacity]
            if slot is None:
                return False
            if slot[0] == key:
                return True
        return False
