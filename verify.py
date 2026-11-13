#!/usr/bin/env python3
"""Score a candidate for STAGGER-256.

    python3 verify.py <hex>
    python3 verify.py --stdin
    python3 verify.py --json <hex>

A candidate is 32 bytes of lowercase hex (64 characters).  Any 32 bytes are
legal; there is no structure to satisfy.
"""

import argparse
import json
import sys

from common import TARGET, distance, next_rung, rung


def score(hex_string: str) -> dict:
    cand = bytes.fromhex(hex_string.strip())
    if len(cand) != 32:
        raise SystemExit(f"candidate must be 32 bytes, got {len(cand)}")
    d = distance(cand)
    nxt = next_rung(d)
    return {
        "candidate": cand.hex(),
        "sha256": __import__("hashlib").sha256(cand).hexdigest(),
        "distance": d,
        "rung": rung(d),
        "next_rung": None if nxt is None else {"distance": nxt[0], "name": nxt[1]},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="score a STAGGER-256 candidate")
    ap.add_argument("candidate", nargs="?")
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--target", action="store_true", help="print the target")
    args = ap.parse_args()

    if args.target:
        print(TARGET.hex())
        return

    if args.stdin:
        hex_string = sys.stdin.read()
    elif args.candidate:
        hex_string = args.candidate
    else:
        ap.error("give a 64-char hex candidate, or --stdin")

    result = score(hex_string)
    if args.json:
        print(json.dumps(result))
        return

    print(f"candidate  {result['candidate']}")
    print(f"sha256     {result['sha256']}")
    print(f"distance   {result['distance']} / 256")
    print(f"rung       {result['rung']}")
    if result["next_rung"]:
        n = result["next_rung"]
        print(f"next       {n['distance']} ({n['name']})")
    else:
        print("next       —")


if __name__ == "__main__":
    main()
