# STAGGER-256

A search challenge. 32 bytes in, one number out.

## The problem

`target.txt` holds a 32-byte value. A **candidate** is any 32 bytes you like.
Its score is

```
d(c) = popcount( sha256(c) XOR target )
```

That is: the Hamming distance between the digest of your candidate and the
target, out of 256 bits. **Minimise it.** `d = 0` means you produced a SHA-256
preimage of the target, which is the whole point of the exercise.

There is no structure to satisfy and no trick input to find. Every 32-byte
string is legal.

## Score a candidate

```console
$ python3 verify.py --target
a3f1...0b9c

$ python3 verify.py 0000000000000000000000000000000000000000000000000000000000000000
candidate  0000...0000
sha256    6e34...c02f
distance   119 / 256
rung       warm-up
next       104 (warm-up)
```

The verifier is the whole specification: `sha256`, `xor`, `popcount`. Anyone can
check anyone else's claim in one command, which is what makes the board worth
having.

## The ladder

| rung | needs d ≤ | |
|---|---|---|
| warm-up | 104 | instant |
| bronze | 96 | instant |
| silver | 88 | seconds |
| silver+ | 84 | seconds |
| gold | 80 | a minute |
| gold+ | 76 | minutes |
| platinum | 72 | hours |
| platinum+ | 68 | days |
| mythic | 64 | months |
| mythic+ | 60 | years |
| reliquary | 56 | ... |
| centurion | 40 | |
| paragon | 16 | |
| **prize** | **0** | |

Every rung is four bits apart, so the honest way to think about the ladder is
"each step is one more zero", not "each step is a bit more effort".

## Leaderboard

| distance | rung | candidate | run |
|---|---|---|---|
| 78 | gold | `dee81641d720bbfe7a4a06c58ac04e8901976991ac59ec5c926f030000000000` | reference solver, 45.0M tries, 12.0s |

Submit by improving `records.json` — `search.py` does it for you — and open a
PR with the candidate. Claims are merged once `verify.py` agrees.

## Start here

```console
$ python3 search.py --budget 120
[    5s] tries=    19.0M  rate=  3.8M/s  best= 86 (silver)   next: 2 to silver+
[   10s] tries=    38.0M  rate=  3.8M/s  best= 82 (silver+)  next: 2 to gold
...
done: 120.0s  455.0M tries  best distance 78 (gold)
```

`search.py` is a sharded random search: 24 random bytes per worker, an 8-byte
counter, `sha256`, popcount. It runs at roughly 3–4 M candidates/s on eight
cores of CPython and updates `records.json` when it beats the stored best.

It is also deliberately the *slowest reasonable way* to play the game. That is
the interesting part of the challenge: d ≤ 80 falls out of a two-minute run,
and everything past that is a question of how many candidates per second you
can actually produce.

## Things that actually help

- **Drop to C.** A tight loop with SHA-256-NI (or even portable C) is 20–50×
  the Python rate on the same machine.
- **GPU.** Raw SHA-256 throughput on a consumer card is in the 10⁸–10⁹
  candidates/s range. That reframes the whole ladder.
- **Midstate.** If you keep the first 32-byte block of the candidate fixed, the
  compression function's chaining value after block one can be precomputed, so
  each candidate costs one block instead of two. This is a real 2× and it
  composes with everything else.
- **Batching.** Amortise the counter update; avoid per-candidate allocation.
  The reference solver allocates a 32-byte string per hash, which is most of
  its overhead.

## Rules

- Candidates are exactly 32 bytes, hex-encoded.
- Ties on distance are broken by fewer tries.
- The ladder is unbounded; new rungs get added when someone clears the top one.
- No claiming a distance you did not verify. `verify.py` is the referee.

## Notes

- The target was generated with `secrets.token_hex(32)` and the author does not
  know a preimage.
- `records.json` only keeps improvements; the history array is append-only.
- If you get to 0, open an issue. You will be on the board forever, and the
  board is the only prize.
