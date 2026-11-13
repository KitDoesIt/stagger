#!/usr/bin/env python3
"""STAGGER-256 reference solver.

Pure random search over 32-byte candidates, sharded across cores.  The
reference implementation is deliberately simple: it is fast enough to walk the
low rungs in seconds and slow enough that anything above the record needs
thought.

    python3 search.py --budget 120
    python3 search.py --budget 600 --workers 16

Progress is written to stdout every few seconds; ``records.json`` is updated
only when a run beats the stored best.
"""

import argparse
import json
import multiprocessing as mp
import os
import pathlib
import struct
import sys
import time

from common import TARGET, distance, next_rung, rung

HERE = pathlib.Path(__file__).resolve().parent
RECORDS = HERE / "records.json"
CHUNK = 250_000

_TARGET = int.from_bytes(TARGET, "big")


def _search(args) -> tuple[int, bytes, int]:
    """Hash CHUNK candidates derived from a per-worker random base."""
    seed, budget = args
    best_d = 257
    best_b = b""
    h = __import__("hashlib")
    pack = struct.pack
    bit_count = int.bit_count
    for i in range(budget):
        cand = seed + pack("<Q", i)
        d = bit_count(int.from_bytes(h.sha256(cand).digest(), "big") ^ _TARGET)
        if d < best_d:
            best_d, best_b = d, cand
    return best_d, best_b, budget


def main() -> None:
    ap = argparse.ArgumentParser(description="STAGGER-256 reference solver")
    ap.add_argument("--budget", type=float, default=120.0, help="seconds to run")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--chunk", type=int, default=CHUNK)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    stored = json.loads(RECORDS.read_text()) if RECORDS.exists() else {"best_distance": 256, "history": []}
    record = stored.get("best_distance", 256)

    start = time.time()
    tries = 0
    best_d, best_b = 257, b""
    last_report = start
    ctr = 0

    with mp.Pool(args.workers) as pool:
        pending = set()
        def submit():
            nonlocal ctr
            base = os.urandom(24)
            pending.add(pool.apply_async(_search, ((base, args.chunk),)))
            ctr += 1

        for _ in range(args.workers * 2):
            submit()

        while time.time() - start < args.budget:
            done = [p for p in pending if p.ready()]
            for p in done:
                pending.discard(p)
                d, b, n = p.get()
                tries += n
                if d < best_d:
                    best_d, best_b = d, b
                submit()

            now = time.time()
            if not args.quiet and now - last_report >= 5:
                elapsed = now - start
                rate = tries / elapsed if elapsed else 0
                nxt = next_rung(best_d)
                gap = f"{best_d - nxt[0]} to {nxt[1]}" if nxt else "—"
                print(
                    f"[{elapsed:5.0f}s] tries={tries/1e6:8.1f}M  rate={rate/1e6:5.1f}M/s  "
                    f"best={best_d:3d} ({rung(best_d)})  next: {gap}",
                    flush=True,
                )
                last_report = now
            time.sleep(0.05)

        pool.terminate()

    elapsed = time.time() - start
    print()
    print(f"done: {elapsed:.1f}s  {tries/1e6:.1f}M tries  best distance {best_d} ({rung(best_d)})")

    if best_d < record and best_b:
        stored["best_distance"] = best_d
        stored["best_candidate"] = best_b.hex()
        stored.setdefault("history", []).append(
            {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "distance": best_d,
             "tries": tries, "seconds": round(elapsed, 1)}
        )
        RECORDS.write_text(json.dumps(stored, indent=2) + "\n")
        print(f"record updated: {record} -> {best_d}")
        print(f"candidate  {best_b.hex()}")
        nxt = next_rung(best_d)
        if nxt:
            print(f"next rung  {nxt[0]} ({nxt[1]})")
    else:
        print(f"no new record (stored best {record}); best this run {best_d}")


if __name__ == "__main__":
    main()
