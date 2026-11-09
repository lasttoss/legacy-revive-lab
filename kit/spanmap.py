#!/usr/bin/env python3
"""Step 10 — the map, rebuilt from traces produced by the tests themselves.

The span file is written by the test run (SpanRecorder), so this step cannot invent anything: if an
endpoint did not execute, it does not appear. That is the whole point of tracing over a whiteboard.

    python3 kit/spanmap.py            # write docs/SPANS.md
    python3 kit/spanmap.py --check     # fail if the committed maps and the traces disagree

What --check proves: every endpoint listed in docs/API.md was actually exercised, and every endpoint that
ran is documented. A map that drifts from the trace is a stale map, and a stale map is a wrong answer.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import defaultdict

from common import ROOT

SPANS = ROOT / "samples/spans.log"
OUT = ROOT / "docs/SPANS.md"


def load() -> list[dict]:
    if not SPANS.exists():
        return []
    rows = []
    for line in SPANS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def collapse(path: str) -> str:
    return re.sub(r"/\d+", "/{id}", path.split("?")[0])


def by_trace(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r.get("path"):
            out[r["trace"]].append(r)
    return out


def documented() -> set[str]:
    doc = ROOT / "docs/API.md"
    if not doc.exists():
        return set()
    out = set()
    for verb, path in re.findall(r"^## `([A-Z]+) ([^`]+)`", doc.read_text(encoding="utf-8"), re.M):
        out.add(f"{verb} {collapse(path)}")
    return out


def exercised(rows: list[dict]) -> dict[str, list[int]]:
    """One entry per (trace, call): a client span and its server span describe the same request, so
    counting both would double the traffic. The longer of the two is kept as that request's duration."""
    per_trace: dict[tuple[str, str], int] = {}
    for r in rows:
        if not r.get("path"):
            continue
        key = (r["trace"], f"{r['method']} {collapse(r['path'])}")
        per_trace[key] = max(per_trace.get(key, 0), int(r.get("duration_us", 0)))
    out: dict[str, list[int]] = defaultdict(list)
    for (_, call), us in per_trace.items():
        out[call].append(us)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare traces with the committed maps")
    args = ap.parse_args()

    rows = load()
    if not rows:
        print("no spans — run `mvn verify` (the test writes samples/spans.log) first")
        return 2

    ran = exercised(rows)
    doc = documented()
    traces = by_trace(rows)

    only_ran = sorted(set(ran) - doc)
    only_doc = sorted(doc - set(ran))

    if args.check:
        print(f"traces={len(traces)} spans={len(rows)} endpoints_ran={len(ran)} endpoints_documented={len(doc)}")
        if only_ran:
            print(f"  ran but not documented: {only_ran}")
        if only_doc:
            print(f"  documented but never ran: {only_doc}")
        ok = not only_ran and not only_doc
        print("RESULT spans=ok" if ok else "RESULT spans=STALE")
        return 0 if ok else 1

    lines = ["# Spans from the test run", "",
             f"Source: `samples/spans.log`, written by `SpanRecorder` during `mvn verify`. "
             f"**{len(rows)} spans**, **{len(traces)} traces**, **{len(ran)} distinct calls**.", "",
             "These numbers come from a developer machine running the suite, so they describe *this* run, not",
             "production. They are useful for shape and for verifying the maps — not for a latency SLO.", "",
             "| Call | Runs | p50 | max |", "|---|---|---|---|"]
    for call in sorted(ran):
        d = sorted(ran[call])
        lines.append(f"| `{call}` | {len(d)} | {statistics.median(d) / 1000:.1f} ms | {d[-1] / 1000:.1f} ms |")

    lines += ["", "## Trace by trace", "", "| trace | calls | total |", "|---|---|---|"]
    for t, spans in sorted(traces.items()):
        calls = sorted({f"{s['method']} {collapse(s['path'])}" for s in spans})
        total = sum(int(s.get("duration_us", 0)) for s in spans) / 1000
        lines.append(f"| `{t}` | {', '.join(calls)} | {total:.0f} ms |")

    lines += ["", "## Agreement with the maps", ""]
    if only_ran:
        lines.append(f"- ran but not in `docs/API.md`: {', '.join(f'`{c}`' for c in only_ran)}")
    if only_doc:
        lines.append(f"- in `docs/API.md` but never ran: {', '.join(f'`{c}`' for c in only_doc)}")
    if not only_ran and not only_doc:
        lines.append("- every documented endpoint executed, and nothing undocumented executed.")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"traces={len(traces)} spans={len(rows)} endpoints={len(ran)} -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
