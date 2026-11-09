#!/usr/bin/env python3
"""Step 0 — find the services in a repository, before doing anything else.

    python3 kit/discover.py                       # this repository
    python3 kit/discover.py --root /path/to/repo  # any repository, unprepared
    make modules ROOT=/path/to/repo

It answers: which modules are Spring services, which endpoints do they declare, which tables do they own,
do they have tests, and do they emit logs we can learn from. Nothing is built, nothing is modified — source
is read as text, which is why this works on a repository you have never run.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MAPPING = re.compile(r'@(Get|Post|Put|Delete|Patch)Mapping\(\s*(?:value\s*=\s*)?"([^"]*)"')
BASE = re.compile(r'@RequestMapping\(\s*(?:value\s*=\s*)?"([^"]+)"')
CONTROLLER = re.compile(r"@(RestController|Controller)\b")
ENTITY = re.compile(r"@Entity\b")
TABLE = re.compile(r'@Table\(\s*name\s*=\s*"([^"]+)"')
SPRING_BOOT = re.compile(r"spring-boot")
GRADLE_SPRING = re.compile(r"org\.springframework\.boot")


SKIP = {"target", "build", "node_modules", "examples"}


def modules(root: Path) -> list[Path]:
    out = []
    for marker in ("pom.xml", "build.gradle", "build.gradle.kts"):
        for f in root.rglob(marker):
            # skip build output and the bundled example, but never the root the caller pointed at
            if SKIP & set(f.relative_to(root).parts[:-1]):
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            if SPRING_BOOT.search(text) or GRADLE_SPRING.search(text):
                out.append(f.parent)
    return sorted(set(out))


def java_files(module: Path) -> list[Path]:
    return [f for f in module.rglob("*.java") if "test" not in f.parts]


def test_files(module: Path) -> list[Path]:
    return [f for f in module.rglob("*.java") if "test" in [p.lower() for p in f.parts]]


def artifact_id(module: Path) -> str:
    """The module's own artifactId — the parent block has one too, and it is the wrong answer."""
    pom = module / "pom.xml"
    if pom.exists():
        text = pom.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"<parent>.*?</parent>", "", text, flags=re.S)
        m = re.search(r"<artifactId>([^<]+)</artifactId>", text)
        if m:
            return m.group(1)
    return module.name


def scan(module: Path, root: Path) -> dict:
    endpoints, tables, controllers, entities = [], [], 0, 0
    for f in java_files(module):
        text = f.read_text(encoding="utf-8", errors="replace")
        if CONTROLLER.search(text):
            controllers += 1
            base = (BASE.search(text).group(1).rstrip("/") if BASE.search(text) else "")
            for verb, path in MAPPING.findall(text):
                full = path if path.startswith(base or "\0") else base + path
                endpoints.append({"method": verb.upper(), "path": full, "file": str(f.relative_to(root))})
        if ENTITY.search(text):
            entities += 1
            m = TABLE.search(text)
            tables.append(m.group(1).lower() if m else re.sub(r"(?<!^)(?=[A-Z])", "_", f.stem).lower())
    return {
        "module": artifact_id(module),
        "path": str(module.relative_to(root)),
        "controllers": controllers,
        "entities": entities,
        "endpoints": endpoints,
        "tables": sorted(set(tables)),
        "test_files": len(test_files(module)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--json", action="store_true", help="print JSON instead of writing docs/MODULES.md")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"no such directory: {root}", file=sys.stderr)
        return 2

    found = [scan(m, root) for m in modules(root)]
    found = [s for s in found if s["controllers"] or s["entities"]]
    total_ep = sum(len(s["endpoints"]) for s in found)

    if args.json:
        print(json.dumps(found, indent=2))
        return 0

    lines = ["# Services in this repository", "",
             f"Discovered by `kit/discover.py` under `{root.name}`: **{len(found)} Spring service(s)**, "
             f"**{total_ep} endpoints**.", "",
             "Discovery reads source text only: no build, no run, no database. That is why it works on a",
             "repository nobody prepared for it.", "",
             "| Service | Path | Controllers | Endpoints | Entities | Tables | Test files |",
             "|---|---|---|---|---|---|---|"]
    for s in found:
        lines.append(f"| `{s['module']}` | `{s['path']}` | {s['controllers']} | {len(s['endpoints'])} | "
                     f"{s['entities']} | {', '.join(f'`{t}`' for t in s['tables']) or '—'} | {s['test_files']} |")

    shared = Counter(t for s in found for t in s["tables"])
    lines += ["", "## Tables owned by more than one service", ""]
    multi = [f"`{t}` — {n} services" for t, n in shared.items() if n > 1]
    lines += [f"- {m}" for m in multi] or ["- none: every table has exactly one owner"]

    lines += ["", "## Endpoints per service", ""]
    for s in found:
        lines.append(f"### `{s['module']}`")
        lines += [f"- `{e['method']} {e['path']}` — {e['file']}" for e in s["endpoints"]] or ["- none"]

    if len(found) > 1:
        lines += ["", "## What multiple services change", "",
                  "- the endpoint-to-endpoint map needs a shared trace id across services, not one per module;",
                  "- every per-service command takes a service name, so `make maps` must loop over this list;",
                  "- a table owned by two services is a coupling that no single-service map can show."]

    # a scan of someone else's repository must not write into theirs
    out = (ROOT / "docs/MODULES.md") if root == ROOT else (ROOT / "out" / f"MODULES-{root.name}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "out").mkdir(exist_ok=True)
    json_out = (ROOT / "out/modules.json") if root == ROOT else (ROOT / "out" / f"modules-{root.name}.json")
    json_out.write_text(json.dumps(found, indent=2) + "\n", encoding="utf-8")
    print(f"services={len(found)} endpoints={total_ep} -> {out.relative_to(ROOT)}")
    for s in found:
        print(f"  {s['module']:<24} {len(s['endpoints']):>3} endpoints  {len(s['tables'])} tables  "
              f"{s['test_files']} test files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
