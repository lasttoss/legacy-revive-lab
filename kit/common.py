"""Shared helpers for the revival kit. Python 3 standard library only."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"
APP = ROOT / "legacy-app"
SRC = APP / "src" / "main" / "java"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def access() -> list[dict]:
    return read_jsonl(SAMPLES / "access.log")


def sql() -> list[dict]:
    return read_jsonl(SAMPLES / "sql.log")


def endpoint_of(path: str) -> str:
    """Collapse /api/customers/17 and /api/customers/3 into /api/customers/{id}."""
    return re.sub(r"/\d+", "/{id}", path.split("?")[0])


def java_files() -> list[Path]:
    return sorted(SRC.rglob("*.java")) if SRC.exists() else []
