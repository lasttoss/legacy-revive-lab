"""One file describes the repository; everything else reads it.

Without this, every script hard-codes `legacy-app/` and the toolkit only ever works on its own demo. With it,
the same commands run on a repository with three Spring services: point `root` at the checkout.

`revive.yml` is optional. When it is absent the layout is discovered (`kit/discover.py`), so a stranger can
run the toolkit on a repository that was never prepared for it.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path(os.environ.get("REVIVE_CONFIG", ROOT / "revive.yml"))


def _mini_yaml(text: str) -> dict:
    """A 60-line reader for the subset of YAML this file needs: nested maps, lists of maps, scalars.

    The alternative was a PyYAML dependency, which is a poor trade for one config file in a toolkit whose
    only selling point is that it has no dependencies.
    """
    lines = [(len(l) - len(l.lstrip()), l.strip()) for l in text.splitlines()
             if l.strip() and not l.strip().startswith("#")]
    def parse(i: int, indent: int):
        out: dict = {}
        while i < len(lines) and lines[i][0] == indent:
            key = lines[i][1].rstrip(":")
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                child_indent = lines[i][0]
                if lines[i][1].startswith("- "):
                    items, i = [], i
                    while i < len(lines) and lines[i][0] == child_indent and lines[i][1].startswith("- "):
                        item: dict = {}
                        key2 = lines[i][1][2:]
                        if ":" in key2:
                            k, v = key2.split(":", 1)
                            item[k.strip()] = v.strip().strip('"')
                            i += 1
                            while i < len(lines) and lines[i][0] > child_indent:
                                k2, v2 = lines[i][1].split(":", 1)
                                item[k2.strip()] = v2.strip().strip('"')
                                i += 1
                        else:
                            i += 1
                        items.append(item)
                    out[key] = items
                else:
                    out[key], i = parse(i, child_indent)
            else:
                out[key] = ""
        return out, i
    data, _ = parse(0, 0)
    return data


def load() -> dict:
    if not CONFIG.exists():
        return {}
    return _mini_yaml(CONFIG.read_text(encoding="utf-8"))


def repo_root() -> Path:
    cfg = load()
    root = cfg.get("root") or "."
    p = Path(root)
    return p if p.is_absolute() else (CONFIG.parent / p).resolve()


def services() -> list[dict]:
    cfg = load()
    return cfg.get("services") or []
