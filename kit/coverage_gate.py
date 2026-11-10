#!/usr/bin/env python3
"""Step 6 — coverage gate: a floor AND a ratchet.

A legacy service cannot jump to 80% in a week, but it can stop going down. So there are two rules:
  1. hard floor  — line coverage must be >= 80% (the goal)
  2. ratchet     — coverage may never fall below the recorded baseline

The baseline lives in `.coverage-baseline` and is raised by `--update`. The ratchet is what makes the
number meaningful: without it a single refactor silently drops 10 points and nobody notices.
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / "legacy-app/target/site/jacoco/jacoco.xml"
BASELINE = ROOT / ".coverage-baseline"
FLOOR = 0.80
# The baseline is stored with four decimals, so the ratchet must be compared at that
# precision. Comparing raw floats made a no-change run fail: 107/120 = 0.891666...
# against a stored 0.8917 is not a drop, but it is smaller as a float.
DEFAULT_DECIMALS = 4


def baseline_decimals(text: str) -> int:
    """How many decimals the baseline was written with ('0.892' -> 3, '0.8917' -> 4)."""
    text = text.strip()
    return len(text.split(".")[1]) if "." in text else 0


def ratchet_dropped(ratio: float, base: float, decimals: int = DEFAULT_DECIMALS) -> bool:
    """True only when coverage fell by at least one unit of the recorded precision.

    Rounding both sides to the precision the baseline was written with is what makes
    "no change" pass: 107/120 = 0.891666... against a recorded 0.8917 is not a drop,
    and neither is it against a recorded 0.892.
    """
    return round(ratio, decimals) < round(base, decimals)


def counters() -> dict[str, tuple[int, int]]:
    root = ET.parse(XML).getroot()
    out = {}
    for c in root.findall("counter"):
        cov, mis = int(c.get("covered")), int(c.get("missed"))
        out[c.get("type")] = (cov, cov + mis)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="raise the baseline to the current value")
    args = ap.parse_args()

    if not XML.exists():
        print(f"no jacoco report at {XML} — run `make verify` first")
        return 2

    c = counters()
    line_cov, line_tot = c["LINE"]
    ratio = line_cov / line_tot
    print(f"{'counter':8} {'covered':>8} {'total':>7}  ratio")
    for k in ("LINE", "BRANCH", "METHOD", "CLASS"):
        cov, tot = c.get(k, (0, 0))
        print(f"{k:8} {cov:8} {tot:7}  {100.0 * cov / tot:5.1f}%")

    base_text = BASELINE.read_text().strip() if BASELINE.exists() else "0"
    base = float(base_text)
    decimals = baseline_decimals(base_text)
    print(f"\nfloor={FLOOR:.0%}  baseline={base:.1%}  now={ratio:.1%}")

    failed = False
    if ratio < FLOOR:
        print(f"FAIL below the {FLOOR:.0%} floor")
        failed = True
    if ratchet_dropped(ratio, base, decimals):
        print(f"FAIL ratchet: coverage dropped from {base:.1%} to {ratio:.1%}")
        failed = True

    if args.update and not failed:
        BASELINE.write_text(f"{ratio:.4f}\n")
        print(f"baseline updated -> {ratio:.1%}")

    print("RESULT coverage=ok" if not failed else "RESULT coverage=FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
