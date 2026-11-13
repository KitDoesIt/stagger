"""Shared helpers for STAGGER-256.

The objective is simple: find a 32-byte candidate whose SHA-256 digest has the
smallest possible Hamming distance to the target in ``target.txt``.
"""

import hashlib
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
TARGET = bytes.fromhex((HERE / "target.txt").read_text().strip())

# distance -> rung name.  Every rung is 4 bits apart, so the expected number of
# random trials grows by roughly 2^5 per rung.
LADDER = [
    (104, "warm-up"),
    (96, "bronze"),
    (88, "silver"),
    (84, "silver+"),
    (80, "gold"),
    (76, "gold+"),
    (72, "platinum"),
    (68, "platinum+"),
    (64, "mythic"),
    (60, "mythic+"),
    (56, "reliquary"),
    (48, "reliquary+"),
    (40, "centurion"),
    (32, "centurion+"),
    (24, "paragon"),
    (16, "paragon+"),
    (8, "unreachable"),
    (0, "prize"),
]


def distance(candidate: bytes) -> int:
    """Hamming distance between SHA-256(candidate) and the target."""
    digest = hashlib.sha256(candidate).digest()
    return (int.from_bytes(digest, "big") ^ int.from_bytes(TARGET, "big")).bit_count()


def rung(dist: int) -> str:
    """Highest ladder rung cleared by ``dist`` (lower distance clears more)."""
    cleared = "none"
    for threshold, name in LADDER:
        if dist <= threshold:
            cleared = name
    return cleared


def next_rung(dist: int) -> tuple[int, str] | None:
    """The next rung worth chasing, or None below the ladder."""
    for threshold, name in LADDER:
        if threshold < dist:
            return (threshold, name)
    return None
