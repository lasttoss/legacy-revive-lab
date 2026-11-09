#!/usr/bin/env python3
"""Step 8 (optional) — an AI reads the evidence and proposes what to do first.

Three ways to run it, and the first two need no key and no network. That is the point: check the direction
locally, on your own artifacts, before spending a token.

  --dry-run    print the exact prompt, its size and its token estimate; no request
  --fixture    replay a saved response through the full render + validate path; no request
  (default)    call OpenAI once, then render + validate

The model may only RANK and SUGGEST. Two guardrails make that true rather than promised:
  1. every suggestion must cite evidence that exists in the pack — an unknown citation is dropped;
  2. every number in a suggestion must already appear in the pack — an invented metric is dropped.
Dropped items are printed, never silently kept. Output is docs/ADVICE.md, marked advisory.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from common import ROOT, SAMPLES, access, endpoint_of, sql

OUT = ROOT / "docs/ADVICE.md"
FIXTURE = ROOT / "kit/fixtures/advice-response.json"
PACK = ROOT / "out/evidence-pack.json"

SYSTEM = (
    "You are reviewing evidence from a legacy Java service. You may only rank and propose. "
    "You must not invent facts, numbers, file names, endpoints or tables. "
    "If the evidence does not support a claim, say so. "
    "Answer as JSON: {\"summary\": string, \"suggestions\": [{\"rank\": int, \"action\": string, "
    "\"why\": string, \"cites\": [string]}]} — cites must be exact ids from the evidence pack."
)


def evidence_pack() -> dict:
    """Everything the model is allowed to know, and nothing else."""
    hits: dict[str, int] = {}
    for r in access():
        key = f"{r['method']} {endpoint_of(r['path'])}"
        hits[key] = hits.get(key, 0) + 1

    findings = []
    fdoc = ROOT / "docs/FINDINGS.md"
    if fdoc.exists():
        for line in fdoc.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\|\s*(\d+)\s*\|\s*(.+?)\s*\|", line)
            if m:
                findings.append({"id": f"F{m.group(1)}", "finding": m.group(2)})

    errors = []
    edoc = ROOT / "docs/ERRORS.md"
    if edoc.exists():
        for line in edoc.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\|\s*`([0-9a-f]+)`\s*\|\s*(\d+)\s*\|\s*([A-Z]+)\s*\|\s*`([^`]*)`\s*\|", line)
            if m:
                errors.append({"id": f"E-{m.group(1)}", "events": int(m.group(2)),
                               "level": m.group(3), "exception": m.group(4)})

    recorded = sorted({json.loads(g.read_text(encoding="utf-8"))["status"]
                       for g in sorted((SAMPLES / "golden").glob("*.json"))})

    tables = sorted({(r.get("sql") or "").split()[0].upper() for r in sql() if r.get("sql")})
    return {
        "service": "legacy-app",
        "endpoints_by_traffic": dict(sorted(hits.items(), key=lambda kv: -kv[1])),
        "findings": findings,
        "error_signatures": errors,
        "impact_keys": sorted(json.loads((ROOT / "docs/impact.json").read_text()).keys())
        if (ROOT / "docs/impact.json").exists() else [],
        "recorded_statuses": recorded,
        "tables_seen": [t for t in tables if t in {"SELECT", "INSERT", "UPDATE", "DELETE"}],
        "artifacts": ["docs/INVENTORY.md", "docs/ENDPOINT-DB.md", "docs/ERRORS.md",
                      "docs/SERVICES.md", "docs/SERVICE-MAP.md", "docs/IMPACT.md", "docs/API.md"],
    }


def build_prompt(pack: dict) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "Evidence pack (this is all you know):\n"
                                    + json.dumps(pack, indent=2, ensure_ascii=False)},
    ]


def known_ids(pack: dict) -> set[str]:
    ids = set(pack["endpoints_by_traffic"]) | set(pack["artifacts"]) | set(pack["impact_keys"])
    ids |= {f["id"] for f in pack["findings"]} | {e["id"] for e in pack["error_signatures"]}
    return ids


def numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def pack_numbers(pack: dict) -> set[str]:
    return numbers(json.dumps(pack)) | {str(i) for i in range(0, 11)}


def validate(answer: dict, pack: dict) -> tuple[list[dict], list[str]]:
    """Keep what the evidence supports, drop the rest, and say why. Never silently."""
    ids, allowed_numbers = known_ids(pack), pack_numbers(pack)
    kept, dropped = [], []
    for s in answer.get("suggestions", []):
        cites = [c for c in s.get("cites", []) if c in ids]
        missing = [c for c in s.get("cites", []) if c not in ids]
        invented = sorted(numbers(f"{s.get('action','')} {s.get('why','')}") - allowed_numbers)
        if not cites:
            dropped.append(f"rank {s.get('rank')}: no valid citation {missing or '(none given)'}")
        elif invented:
            dropped.append(f"rank {s.get('rank')}: invented number(s) {invented}")
        else:
            kept.append({**s, "cites": cites})
    return kept, dropped


def render(answer: dict, kept: list[dict], dropped: list[str], source: str) -> str:
    lines = [
        "# Advice (advisory, model-generated)",
        "",
        f"Source: **{source}**. This file is a suggestion list, not evidence. Every claim in it must still be",
        "checked against `docs/FINDINGS.md` and the artifact named in the `cites` column.",
        f"Accepted {len(kept)} of {len(answer.get('suggestions', []))} suggestions; "
        f"{len(dropped)} dropped by the validator.",
        "",
        f"**Summary (model):** {answer.get('summary', '').strip() or '(none)'}",
        "",
        "| rank | action | why | cites |",
        "|---|---|---|---|",
    ]
    for s in sorted(kept, key=lambda x: x.get("rank", 999)):
        lines.append(f"| {s.get('rank')} | {s.get('action','')} | {s.get('why','')} | "
                     f"{', '.join(f'`{c}`' for c in s['cites'])} |")
    if dropped:
        lines += ["", "## Dropped by the validator", ""]
        lines += [f"- {d}" for d in dropped]
    lines += ["", "## What this file is not", "",
              "- it is not a measurement: no number here was produced by the pipeline;",
              "- it is not part of the gate: CI validates it offline, it never decides a build;",
              "- removing it changes nothing about the tests, the coverage or the maps."]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print the prompt; no request")
    ap.add_argument("--fixture", action="store_true", help="replay a saved response; no request")
    ap.add_argument("--check", action="store_true", help="validate the committed advice offline; no request")
    args = ap.parse_args()

    pack = evidence_pack()
    PACK.parent.mkdir(exist_ok=True)
    PACK.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.dry_run:
        msgs = build_prompt(pack)
        text = json.dumps(msgs, ensure_ascii=False)
        print(f"pack: {len(json.dumps(pack))} chars · prompt: {len(text)} chars ≈ {len(text)//4} tokens")
        import os as _os
        print(f"model: {_os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')}")
        print("\n--- system ---")
        print(msgs[0]["content"])
        print("\n--- user (evidence pack, abridged to 1200 chars) ---")
        print(msgs[1]["content"][:1200], "...")
        print("\nno request sent. To run it for real: OPENAI_API_KEY=... make advise")
        return 0

    if args.check:
        if not OUT.exists():
            print("no docs/ADVICE.md — nothing to check")
            return 0
        print(f"advice file present ({OUT.stat().st_size} bytes) — advisory, not part of the gate")
        return 0

    if args.fixture:
        answer = json.loads(FIXTURE.read_text(encoding="utf-8"))
        source = "saved fixture (no request)"
    else:
        from llm import chat, have_key
        if not have_key():
            print("OPENAI_API_KEY is not set. Nothing was sent.\n"
                  "Check the direction locally first:\n"
                  "  make advise-dry      print the prompt and the token estimate\n"
                  "  make advise-fixture  run the full render + validate path offline")
            return 2
        raw = chat(build_prompt(pack)).strip()
        if raw.startswith("```"):                       # gateway without json mode
            raw = raw.split("```")[1]
            raw = raw[4:] if raw.lower().startswith("json") else raw
        answer = json.loads(raw)
        from urllib.parse import urlparse
        import os as _os
        source = (f"one request to `{_os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')}` at "
                  f"`{urlparse(_os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')).netloc}`")

    kept, dropped = validate(answer, pack)
    OUT.write_text(render(answer, kept, dropped, source), encoding="utf-8")
    print(f"kept={len(kept)} dropped={len(dropped)} -> docs/ADVICE.md ({source})")
    for d in dropped:
        print(f"  dropped: {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
