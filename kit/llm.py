"""Minimal OpenAI chat client — standard library only, no SDK, no dependency to audit.

The key comes from the environment and is never written to disk, never logged, and never put in the
prompt. If OPENAI_API_KEY is absent the caller must fall back to a local path; this module never invents
a key and never silently returns an empty answer.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

# Any OpenAI-compatible endpoint works: OpenAI, Command Code, a local vLLM, an internal gateway.
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
UA = "legacy-revive-lab/0.1 (+https://github.com/lasttoss/legacy-revive-lab)"


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

    def send(json_mode: bool) -> tuple[str, dict]:
        body_obj = {
            "model": model or DEFAULT_MODEL,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:                    # not every compatible gateway implements response_format
            body_obj["response_format"] = {"type": "json_object"}
        req = urllib.request.Request(BASE_URL + "/chat/completions",
                                     data=json.dumps(body_obj).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json",
                                              "Authorization": f"Bearer {key}",
                                              "Accept": "application/json",
                                              # without an explicit agent, some gateways answer
                                              # 403 "error code: 1010" to the default urllib agent
                                              "User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = json.loads(r.read().decode("utf-8"))
        return out["choices"][0]["message"]["content"], out.get("usage", {})

    last: Exception | None = None
    for attempt in (1, 2):
        try:
            try:
                text, usage = send(json_mode=True)
            except urllib.error.HTTPError as e:
                if e.code not in (400, 422):             # only "unsupported parameter" is retried
                    raise
                text, usage = send(json_mode=False)
            print(f"usage: {usage or 'not reported by this endpoint'}", file=sys.stderr)
            return text
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            raise LLMError(f"HTTP {e.code}: {detail}") from e
        except (urllib.error.URLError, TimeoutError, KeyError) as e:
            last = e
            if attempt == 2:
                break
    raise LLMError(f"request failed twice: {last}")
