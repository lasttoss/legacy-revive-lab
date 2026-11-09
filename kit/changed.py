#!/usr/bin/env python3
"""Step 9 — the question that actually gets asked: "I changed this file, what else is affected?"

    python3 kit/changed.py legacy-app/src/main/java/com/example/legacy/service/LegacyService.java
    python3 kit/changed.py --git            # uses `git diff --name-only HEAD`
    make changed FILES="src/main/java/.../OrderEntity.java"

It answers with four lists, and it refuses to guess: a file it cannot map is reported as unmapped, never
silently treated as "no impact".

  endpoints   declared in the changed file, or reading a table the changed file owns
  callers     services that call those endpoints (from the trace ids in samples/rpc.log)
  tables      tables reached by those endpoints
  tests+docs  which recordings must be re-run and which documents must be regenerated
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from common import APP, ROOT, SAMPLES, access, endpoint_of, java_files, sql

TABLE = re.compile(r"(?:from|into|update|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.I)
TABLE_ANN = re.compile(r'@Table\(\s*name\s*=\s*"([^"]+)"')
OUT = ROOT / "out/CHANGED-IMPACT.md"


def endpoint_tables() -> dict[str, set[str]]:
    trace_endpoint = {}
    for r in access():
        trace_endpoint.setdefault(r.get("trace"), f"{r['method']} {endpoint_of(r['path'])}")
    out: dict[str, set[str]] = defaultdict(set)
    for row in sql():
        ep = trace_endpoint.get(row.get("trace"), "(no trace in access log)")
        for t in TABLE.findall(row.get("sql", "") or ""):
            if t.lower() not in ("select", "values", "set"):
                out[ep].add(t.lower())
    return out


def declared() -> dict[str, str]:
    """endpoint -> declaring file (relative path)."""
    from inventory import declared_endpoints
    return declared_endpoints()


def callers(endpoints: set[str]) -> dict[str, list[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    rpc = SAMPLES / "rpc.log"
    if not rpc.exists():
        return {}
    for line in rpc.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        ep = f"{r.get('method', 'GET')} {endpoint_of(r.get('path', ''))}"
        if ep in endpoints:
            out[ep].add(r.get("caller") or r.get("source_service") or "?")
    return {k: sorted(v) for k, v in out.items()}


def table_of(java: Path) -> str:
    """The table a changed class owns: @Table(name=...) if present, else the class name in snake_case."""
    text = java.read_text(encoding="utf-8")
    m = TABLE_ANN.search(text)
    if m:
        return m.group(1).lower()
    return re.sub(r"(?<!^)(?=[A-Z])", "_", java.stem).lower()


def recordings() -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for g in sorted((SAMPLES / "golden").glob("*.json")):
        d = json.loads(g.read_text(encoding="utf-8"))
        out[f"{d['method']} {endpoint_of(d['path'])}"].append(g.stem)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--git", action="store_true", help="take the file list from git diff HEAD")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any impact is found")
    args = ap.parse_args()

    files = list(args.files)
    if args.git:
        try:
            files += subprocess.run(["git", "diff", "--name-only", "HEAD"], cwd=ROOT,
                                    capture_output=True, text=True, check=True).stdout.split()
        except subprocess.CalledProcessError as e:
            print(f"git diff failed: {e}", file=sys.stderr)
            return 2
    skip = ("docs/", "kit/", "samples/", ".github/", "out/")
    files = [f for f in dict.fromkeys(files)
             if f and not f.startswith(skip) and f != "Makefile"
             and not f.endswith((".md", ".py", ".log", ".json"))]
    if not files:
        print("no files given. Try: make changed FILES=\"legacy-app/src/main/java/.../OrderEntity.java\"")
        return 2

    ep_file = declared()
    ep_tables = endpoint_tables()
    recs = recordings()
    by_table: dict[str, set[str]] = defaultdict(set)
    for ep, tables in ep_tables.items():
        for t in tables:
            by_table[t].add(ep)

    blocks, unmapped, hit_endpoints = [], [], set()
    for rel in files:
        path = (ROOT / rel) if not Path(rel).is_absolute() else Path(rel)
        if not path.exists():
            unmapped.append((rel, "file not found"))
            continue
        endpoints, why = set(), []
        if path.suffix == ".java":
            for ep, f in ep_file.items():
                if f.endswith(rel) or Path(f).name == path.name:
                    endpoints.add(ep)
            if endpoints:
                why.append("declares these endpoints")
            t = table_of(path)
            readers = by_table.get(t, set())
            if readers:
                endpoints |= readers
                why.append(f"owns table `{t}` read by these endpoints")
            if not endpoints:
                name = path.stem
                users = [ep for ep, f in ep_file.items()
                         if name in (ROOT / f).read_text(encoding="utf-8")]
                endpoints |= set(users)
                if users:
                    why.append(f"`{name}` is referenced by the code behind these endpoints")
        elif path.suffix in (".sql", ".yml", ".yaml", ".properties"):
            t = path.stem.lower()
            endpoints |= by_table.get(t, set())
            why.append(f"configuration/schema for table `{t}`" if endpoints else "unmapped configuration")

        if not endpoints:
            unmapped.append((rel, "no endpoint or table could be linked to this file"))
            continue

        hit_endpoints |= endpoints
        cs = callers(endpoints)
        tables = sorted({t for ep in endpoints for t in ep_tables.get(ep, set())})
        tests = sorted({r for ep in endpoints for r in recs.get(ep, [])})
        blocks.append((rel, why, sorted(endpoints), cs, tables, tests))

    lines = ["# Change impact", "", f"Input: {len(files)} changed file(s).", ""]
    for rel, why, eps, cs, tables, tests in blocks:
        lines += [f"## `{rel}`", "", "; ".join(why) or "linked by reference", "", "**Endpoints**", ""]
        lines += [f"- `{e}`" for e in eps]
        if tables:
            lines += ["", "**Tables reached**", ""] + [f"- `{t}`" for t in tables]
        if cs:
            lines += ["", "**Callers to notify (from trace ids)**", ""]
            lines += [f"- `{e}` ← {', '.join(v)}" for e, v in cs.items()]
        if tests:
            lines += ["", "**Recordings to re-run**", ""] + [f"- `{t}`" for t in tests]
        lines += ["", "**Documents to regenerate**", "",
                  "- `docs/API.md`, `docs/IMPACT.md` (`make docs`), and `docs/ERRORS.md` if behavior changed",
                  "", "## "]
    if unmapped:
        lines += ["", "## Not mapped (needs a human)", ""]
        lines += [f"- `{rel}` — {why}" for rel, why in unmapped]

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(l for l in lines if l != "## ") + "\n", encoding="utf-8")

    print(f"changed={len(files)} mapped={len(blocks)} unmapped={len(unmapped)} "
          f"endpoints={len(hit_endpoints)} -> {OUT.relative_to(ROOT)}")
    for rel, why, eps, cs, tables, tests in blocks:
        print(f"  {rel}\n    endpoints: {', '.join(eps)}\n    tests: {', '.join(tests) or '(none)'}")
    for rel, why in unmapped:
        print(f"  UNMAPPED {rel}: {why}")
    return 1 if (args.strict and hit_endpoints) else 0


if __name__ == "__main__":
    sys.exit(main())
