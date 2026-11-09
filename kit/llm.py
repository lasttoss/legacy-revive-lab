"""Minimal OpenAI chat client — standard library only, no SDK, no dependency to audit.

The key comes from the environment and is never written to disk, never logged, and never put in the
prompt. If OPENAI_API_KEY is absent the caller must fall back to a local path; this module never invents
a key and never silently returns an empty answer.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

ENDPOINT = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"


class LLMError(RuntimeError):
    pass


def have_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def estimate_tokens(text: str) -> int:
    """Rough but stable: 4 characters per token. Good enough to see the bill before paying it."""
    return len(text) // 4


def chat(messages: list[dict], model: str | None = None, timeout: int = 60,
         temperature: float = 0.2) -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise LLMError("OPENAI_API_KEY is not set — use --dry-run or --fixture")

    payload = json.dumps({
        "model": model or os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    req = urllib.request.Request(ENDPOINT, data=payload, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    })

    last: Exception | None = None
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = json.loads(r.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:              # 4xx will not improve on retry
            detail = e.read().decode("utf-8", "replace")[:400]
            raise LLMError(f"HTTP {e.code}: {detail}") from e
        except (urllib.error.URLError, TimeoutError, KeyError) as e:
            last = e
            if attempt == 2:
                break
    raise LLMError(f"request failed twice: {last}")
