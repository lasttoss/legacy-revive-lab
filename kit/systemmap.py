#!/usr/bin/env python3
"""Step 11 — one diagram for the whole repository, generated from traces and sources.

Three related services are easy to draw by hand once and impossible to keep true. This builds the picture
from two things that cannot be guessed: the modules found in the tree, and the trace ids in the call log.

    python3 kit/systemmap.py --root examples/multi-service
    make system ROOT=examples/multi-service

Output: docs/SYSTEM.html (self-contained SVG, paper background) plus docs/SYSTEM.md for grepping, and
out/system.json for tools.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def discover(root: Path) -> list[dict]:
    out = subprocess.run([sys.executable, str(ROOT / "kit/discover.py"), "--root", str(root), "--json"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def edges(root: Path, services: set[str]) -> tuple[Counter, dict[str, int], dict[str, set[str]]]:
    """caller -> callee counts, plus per-trace fan-out and the endpoints each pair exchanges."""
    log = root / "samples/rpc.log"
    if not log.exists():
        log = ROOT / "samples/rpc.log"
    pair: Counter = Counter()
    exchange: dict[str, set[str]] = defaultdict(set)
    traces: dict[str, set[str]] = defaultdict(set)
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        svc = r.get("service") or ""
        caller = r.get("caller") or ""
        if svc:
            traces[r["trace"]].add(svc)
        if caller and caller != svc and caller in services and svc in services:
            pair[(caller, svc)] += 1
            exchange[f"{caller}->{svc}"].add(re.sub(r"/\d+", "/{id}", r.get("path", "")))
    return pair, {k: len(v) for k, v in traces.items()}, exchange


# "select * from t" and "select a, b from t" are both reads of t, so the columns cannot be part of the match
SQL_OPS = [
    ("SELECT", re.compile(r"^\s*select\b.*?\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.I | re.S)),
    ("INSERT", re.compile(r"^\s*insert\s+into\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.I)),
    ("UPDATE", re.compile(r"^\s*update\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.I)),
    ("DELETE", re.compile(r"^\s*delete\s+from\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.I)),
]


def table_access(root: Path) -> dict[tuple[str, str], Counter]:
    """(service, table) -> {SELECT: n, INSERT: n, ...} from the statement log.

    The log is the only honest source: a repository can declare ten tables and read three, and the diagram
    must show three.
    """
    log = root / "samples/sql.log"
    out: dict[tuple[str, str], Counter] = defaultdict(Counter)
    if not log.exists():
        return out
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        sql = r.get("sql", "") or ""
        for op, pattern in SQL_OPS:
            m = pattern.match(sql)
            if m:
                out[(r.get("service", ""), m.group(1).lower())][op] += 1
                break
    return out


def box(x: int, y: int, w: int, h: int, title: str, sub: str, facts: list[str], accent: bool) -> str:
    fill = "var(--accent-tint)" if accent else "var(--paper-2)"
    stroke = "var(--accent)" if accent else "var(--rule-solid)"
    width = 1.5 if accent else 1
    out = [f'  <g>',
           f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>',
           f'    <text x="{x+16}" y="{y+26}" font-size="14.5" font-weight="600">{title}</text>',
           f'    <text x="{x+16}" y="{y+46}" font-size="11" fill="var(--muted)">{sub}</text>']
    for i, line in enumerate(facts):
        out.append(f'    <text x="{x+16}" y="{y+68+i*17}" font-size="11.5" fill="var(--muted)">{line}</text>')
    out.append('  </g>')
    return "\n".join(out)


def arrow(x1: int, y1: int, x2: int, y2: int, label: str, dashed: bool = False) -> str:
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    mx, my = (x1 + x2) // 2, (y1 + y2) // 2
    return (f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--muted)" stroke-width="1.4"{dash}/>\n'
            f'  <polygon points="{x2},{y2} {x2-10},{y2-5} {x2-10},{y2+5}" fill="var(--muted)"/>\n'
            f'  <text x="{mx}" y="{my-7}" font-size="11" fill="var(--soft)" text-anchor="middle" class="mono">{label}</text>')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT / "examples/multi-service"))
    args = ap.parse_args()
    root = Path(args.root).resolve()

    svc = discover(root)
    names = [s["module"] for s in svc]
    pair, per_trace, exchange = edges(root, set(names))

    access = table_access(root)
    access_tables = sorted({t for (_, t) in access})
    declared_tables = sorted({t for s in svc for t in s["tables"]} | set(access_tables))

    shared = Counter(t for s in svc for t in s["tables"])
    shared_tables = {t: n for t, n in shared.items() if n > 1}

    # layout: left to right, gateway first when it exists
    order = sorted(names, key=lambda n: (0 if "gateway" in n else 1, n))
    W, GAP, H = 232, 84, 156
    x0, y0 = 24, 132
    pos = {n: (x0 + i * (W + GAP), y0) for i, n in enumerate(order)}

    parts = []
    for n in order:
        s = next(x for x in svc if x["module"] == n)
        def n_(k: int, one: str, many: str) -> str:
            return f"{k} {one if k == 1 else many}"

        facts = [f"{n_(len(s['endpoints']), 'endpoint', 'endpoints')}, "
                 f"{n_(s['controllers'], 'controller', 'controllers')}",
                 f"{n_(s['entities'], 'entity', 'entities')} · tables: {', '.join(s['tables']) or 'none'}",
                 f"{n_(s['test_files'], 'test file', 'test files')}"]
        x, y = pos[n]
        parts.append(box(x, y, W, H, n, "module " + s["path"], facts, accent=(len(pair) and n in {p[0] for p in pair}) and False))

    def plural(n: int) -> str:
        return f"{n} call" if n == 1 else f"{n} calls"

    for (a, b), count in sorted(pair.items()):
        if a not in pos or b not in pos:
            continue
        ax, ay = pos[a]
        bx, by = pos[b]
        i, j = order.index(a), order.index(b)
        two_way = (b, a) in pair
        if abs(i - j) == 1:
            # neighbours: one lane per direction, so a two-way pair never looks like a single arrow
            if j > i:
                y1 = y2 = ay + H // 2 - (10 if two_way else 0)
                parts.append(arrow(ax + W, y1, bx, y2, plural(count)))
            else:
                y1 = y2 = ay + H // 2 + (12 if two_way else 0)
                parts.append(arrow(ax, y1, bx + W, y2, plural(count)))
        else:
            # skips a service: route below the row, where no label lives
            # above the row: the space below belongs to the service-to-table edges
            lane = ay - 34
            parts.append(f'  <path d="M {ax + W // 2} {ay} L {ax + W // 2} {lane} L {bx + W // 2} {lane} '
                         f'L {bx + W // 2} {by}" fill="none" stroke="var(--muted)" stroke-width="1.4"/>\n'
                         f'  <polygon points="{bx + W // 2},{by} {bx + W // 2 - 5},{by - 10} '
                         f'{bx + W // 2 + 5},{by - 10}" fill="var(--muted)"/>\n'
                         f'  <text x="{(ax + bx) // 2 + W // 2}" y="{lane - 8}" font-size="11" '
                         f'fill="var(--soft)" text-anchor="middle" class="mono">{plural(count)}</text>')

    # ---- table row: who reads and writes what
    TW, TH, TGAP = 210, 74, 40
    row_y = y0 + H + 92
    tx0 = 24
    tpos = {t: (tx0 + i * (TW + TGAP), row_y) for i, t in enumerate(declared_tables)}
    owners: dict[str, set[str]] = defaultdict(set)
    for (svc_name, table) in access:
        owners[table].add(svc_name)

    for t in declared_tables:
        x, y = tpos[t]
        ops = Counter()
        for (svc_name, table), c in access.items():
            if table == t:
                ops.update(c)
        ops_txt = " · ".join(f"{k} {v}" for k, v in sorted(ops.items())) or "declared, never accessed in the sample"
        owner_txt = ", ".join(sorted(owners.get(t) or {s["module"] for s in svc if t in s["tables"]})) or "unknown"
        shared_flag = "  ← shared by 2 services" if len(owners.get(t, set())) > 1 else ""
        parts.append(box(x, y, TW, TH, f"table {t}", f"used by {owner_txt}{shared_flag}",
                         [ops_txt], accent=False))

    # service -> table edges, labelled with the operations observed
    for lane_i, ((svc_name, table), c) in enumerate(sorted(access.items())):
        if svc_name not in pos or table not in tpos:
            continue
        sx, sy = pos[svc_name]
        tx, ty = tpos[table]
        start_x = sx + W // 2
        end_x = tx + TW // 2
        if abs(start_x - end_x) < 4:
            line = (f'  <line x1="{start_x}" y1="{sy + H}" x2="{end_x}" y2="{ty}" stroke="var(--muted)" '
                    f'stroke-width="1.4"/>\n  <polygon points="{end_x},{ty} {end_x-5},{ty-10} {end_x+5},{ty-10}" '
                    f'fill="var(--muted)"/>')
        else:
            lane = sy + H + 22 + lane_i * 18
            line = (f'  <path d="M {start_x} {sy + H} L {start_x} {lane} L {end_x} {lane} '
                    f'L {end_x} {ty}" fill="none" stroke="var(--muted)" stroke-width="1.2"/>\n'
                    f'  <polygon points="{end_x},{ty} {end_x-5},{ty-10} {end_x+5},{ty-10}" fill="var(--muted)"/>')
        label = " · ".join(f"{k} {v}" for k, v in sorted(c.items()))
        # label beside the arrow head, so it can never run off the canvas on the right-hand service
        parts.append(line + f'\n  <text x="{end_x + 10}" y="{ty - 8}" font-size="10.5" '
                            f'fill="var(--soft)" class="mono">{label}</text>')

    notes = [f"{sum(pair.values())} calls across {len(per_trace)} trace ids",
             "shared trace id is the only thing that joins services",
             f"shared tables: {', '.join(shared_tables) if shared_tables else 'none'}",
             "operations below each service come from the statement log, not from the schema"]

    svg = [f'<svg id="system" viewBox="0 0 900 620" width="900" height="620" role="img" aria-labelledby="t d">',
           '  <title id="t">Three related services: who calls whom, from the trace ids</title>',
           '  <desc id="d">Each box is a Spring service discovered in the tree, with its endpoint count, '
           'tables and test files. Arrows are call edges counted from shared trace ids in the call log. '
           'Services that exchange calls are connected; the number on each arrow is how often it happened '
           'in the sample.</desc>',
           '  <rect x="0" y="0" width="900" height="620" fill="var(--paper)"/>',
           '  <text x="24" y="40" font-size="12" letter-spacing="0.09em" fill="var(--soft)" class="mono">'
           'SERVICES, CALL EDGES AND TABLE ACCESS — ALL FROM LOGS</text>',
           '  <line x1="24" y1="52" x2="876" y2="52" stroke="var(--rule)" stroke-width="1"/>']
    svg += parts
    svg += ['  <line x1="24" y1="524" x2="876" y2="524" stroke="var(--rule)" stroke-width="1"/>']
    for i, n in enumerate(notes):
        svg.append(f'  <text x="24" y="{548+i*20}" font-size="11.5" fill="var(--muted)" class="mono">{n}</text>')
    svg.append('</svg>')

    html = f'''<!DOCTYPE html>
<html lang="en">
<!-- diagram-meta {{"sources":["kit/discover.py","kit/systemmap.py","samples/rpc.log","revive.yml"]}} -->
<head>
<meta charset="utf-8">
<title>System map — {root.name}</title>
<style>
  :root{{--paper:#f5f5f5;--paper-2:#ececec;--ink:#2d3142;--muted:#4f5d75;--soft:#7a8399;
        --rule:rgba(45,49,66,0.12);--rule-solid:#bfc0c0;--accent:#eb6c36;--accent-tint:rgba(235,108,54,0.08);}}
  html,body{{margin:0;background:var(--paper);}}
  body{{padding:40px;font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);}}
  figure{{margin:0;max-width:1000px;}}
  figcaption{{margin-top:18px;font-size:13px;line-height:1.55;color:var(--muted);max-width:80ch;}}
  .mono{{font-family:ui-monospace,"SF Mono",Menlo,monospace;}}
</style>
</head>
<body>
<figure>
{chr(10).join(svg)}
<figcaption><strong>Figure 1.</strong> Every box was discovered by reading source files, and every arrow was
counted from trace ids shared between services in the call log. A service that appears with no arrow either
has no caller in the sample or is never called — the diagram cannot tell those apart, which is why the count
is printed next to each edge instead of a guess.</figcaption>
</figure>
</body>
</html>
'''
    out_dir = (ROOT / "docs") if root == ROOT else (ROOT / "out")
    out_dir.mkdir(parents=True, exist_ok=True)
    name = "SYSTEM" if root == ROOT else f"SYSTEM-{root.name}"
    (out_dir / f"{name}.html").write_text(html, encoding="utf-8")

    md = [f"# System map — {root.name}", "",
          f"Services: {len(svc)} · calls in sample: {sum(pair.values())} · trace ids: {len(per_trace)}", "",
          "## Services", ""]
    for s in svc:
        md.append(f"- `{s['module']}` — {len(s['endpoints'])} endpoints, tables "
                  f"{', '.join(s['tables']) or 'none'}, {s['test_files']} test file(s)")
    md += ["", "## Call edges", ""]
    md += [f"- `{a}` → `{b}` — {c} call(s): " + ", ".join(sorted(exchange[f'{a}->{b}']))
           for (a, b), c in sorted(pair.items())] or ["- none: no shared trace id between services"]
    if shared_tables:
        md += ["", "## Tables owned by more than one service", ""]
        md += [f"- `{t}` — {n} services: no single-service map can show this coupling" for t, n in shared_tables.items()]
    (out_dir / f"{name}.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / ("system.json" if root == ROOT else f"system-{root.name}.json")).write_text(
        json.dumps({"services": svc, "edges": {f"{a}->{b}": c for (a, b), c in pair.items()},
                    "traces": len(per_trace), "shared_tables": shared_tables}, indent=2) + "\n", encoding="utf-8")

    print(f"services={len(svc)} edges={len(pair)} traces={len(per_trace)} -> {out_dir / name}.html")
    for (a, b), c in sorted(pair.items()):
        print(f"  {a} -> {b}: {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
