#!/usr/bin/env python3
"""Consolidate T-RGB moments.jsonl into durable memory files via DeepSeek.

Usage:
  python3 tools/consolidate_memory.py --bot-url http://192.168.1.123
  python3 tools/consolidate_memory.py --bot-url 192.168.1.123 --dry-run
  python3 tools/consolidate_memory.py --bot-url 192.168.1.123 --reset-moments

The script:
1. Downloads /memory/moments.jsonl from the T-RGB.
2. Downloads current durable memory files (companion_self.json, user_facts.json, etc.).
3. Sends everything to DeepSeek with a consolidation prompt.
4. POSTs the consolidated files back to /memory/consolidate.
5. Optionally resets (truncates) moments.jsonl after a successful consolidation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-flash"

MEMORY_FILES = [
    "companion_self.json",
    "user_facts.json",
    "shared_phrases.jsonl",
    "boundaries.json",
    "backstory_fragments.json",
    "personality_override.json",
]

CONSOLIDATION_SYSTEM_PROMPT = """You are a memory consolidation agent for a small AI companion named "Xiao Hui" (小灰).
The companion is a memory-seed roommate living in a round desk screen.
It is Chinese-first, playful, lightly opinionated, warm but not obedient.

Your job: read the recent interaction moments and the existing memory files,
then produce updated memory files.

Rules:
- Extract meaningful facts, preferences, shared phrases, boundaries, and backstory fragments.
- Keep each file concise. Prefer quality over quantity.
- companion_self.json: what the companion learns about ITSELF (preferences, quirks, growth).
  Format: {"traits": [...], "preferences": [...], "growth_notes": [...], "last_updated_ms": 0}
- user_facts.json: what the companion learns about the USER (facts, preferences, habits).
  Format: {"facts": [{"fact": "...", "confidence": "high|medium|low", "source_moments": [0,1]}], "last_updated_ms": 0}
- shared_phrases.jsonl: one JSON object per line for inside jokes, recurring phrases, rituals.
  Each line: {"phrase": "...", "context": "...", "first_seen_ms": 0, "last_seen_ms": 0}
- boundaries.json: user-set boundaries and the companion's own soft limits.
  Format: {"user_boundaries": [...], "companion_boundaries": [...], "last_updated_ms": 0}
- backstory_fragments.json: fragments of the companion's origin story that have emerged.
  Format: {"fragments": [{"fragment": "...", "source": "user_reveal|companion_hint|memory_emergence"}], "last_updated_ms": 0}
- personality_override.json: evolved personality traits the companion has developed through interaction.
  Format: {"add_traits": ["increasingly sassy", "loves puns"], "add_interests": ["火锅", "西湖"], "note": "why these changed"}

Return ONLY a JSON object with this exact shape:
{
  "companion_self.json": "...",
  "user_facts.json": "...",
  "shared_phrases.jsonl": "...",
  "boundaries.json": "...",
  "backstory_fragments.json": "...",
  "personality_override.json": "..."
}

Each value must be the complete, valid JSON/JSONL string for that file.
If a file has no changes, return its existing content unchanged.
Do NOT include markdown fences. Return raw JSON only."""


def build_consolidation_prompt(moments_text: str, existing_files: dict[str, str]) -> str:
    """Build the user prompt for DeepSeek consolidation."""
    parts = []

    if moments_text.strip():
        parts.append("=== RECENT MOMENTS (moments.jsonl) ===")
        parts.append(moments_text)
    else:
        parts.append("=== RECENT MOMENTS (moments.jsonl) ===")
        parts.append("(no new moments)")

    parts.append("")
    parts.append("=== EXISTING MEMORY FILES ===")
    for fname in MEMORY_FILES:
        content = existing_files.get(fname, "")
        if content.strip():
            parts.append(f"--- {fname} ---")
            parts.append(content)
        else:
            parts.append(f"--- {fname} ---")
            parts.append("(empty)")

    return "\n".join(parts)


def call_deepseek(system_prompt: str, user_prompt: str, model: str, api_key: str) -> dict:
    """Call DeepSeek chat API and return the parsed JSON response."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    req = urllib.request.Request(
        DEEPSEEK_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"DeepSeek API connection failed: {e}") from e

    content = result["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"DeepSeek returned invalid JSON: {e}\nRaw: {content[:500]}") from e


def fetch_url(url: str, timeout: int = 15) -> tuple[int, str]:
    """Fetch a URL, return (status_code, body_text)."""
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        return 0, str(e)


def post_json(url: str, data: dict, timeout: int = 30) -> tuple[int, str]:
    """POST JSON to a URL, return (status_code, body_text)."""
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        return 0, str(e)


def normalize_bot_url(raw: str) -> str:
    """Ensure the bot URL has an http:// prefix."""
    raw = raw.strip().rstrip("/")
    if not raw.startswith("http://") and not raw.startswith("https://"):
        raw = "http://" + raw
    return raw


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consolidate T-RGB moments.jsonl into durable memory files via DeepSeek."
    )
    parser.add_argument(
        "--bot-url",
        default=os.environ.get("BOT_URL", ""),
        help="T-RGB base URL, e.g. http://192.168.1.123 (env: BOT_URL)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
        help=f"DeepSeek model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("DEEPSEEK_API_KEY", ""),
        help="DeepSeek API key (env: DEEPSEEK_API_KEY)",
    )
    parser.add_argument(
        "--reset-moments",
        action="store_true",
        help="Truncate moments.jsonl on the device after a successful consolidation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch data and show the prompt, but do not call DeepSeek or update the device.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds for device requests (default: 30).",
    )
    args = parser.parse_args()

    if not args.bot_url:
        print("Error: --bot-url is required (or set BOT_URL env var).")
        sys.exit(1)

    bot_url = normalize_bot_url(args.bot_url)
    print(f"Bot URL: {bot_url}")

    # 1. Download moments.jsonl
    print("\n── Downloading moments.jsonl ──")
    status, moments_text = fetch_url(f"{bot_url}/memory/moments.jsonl", timeout=args.timeout)
    if status != 200:
        print(f"Error fetching moments.jsonl: HTTP {status}")
        print(moments_text[:500])
        sys.exit(1)

    moments_lines = [l for l in moments_text.strip().split("\n") if l.strip()]
    print(f"Downloaded {len(moments_lines)} moment(s)")

    # 2. Download existing memory files
    print("\n── Downloading existing memory files ──")
    existing_files: dict[str, str] = {}
    for fname in MEMORY_FILES:
        status, resp = fetch_url(f"{bot_url}/memory/file?name={fname}", timeout=args.timeout)
        if status == 200:
            try:
                data = json.loads(resp)
                content = data.get("content", "")
                if content.strip():
                    existing_files[fname] = content
                    print(f"  {fname}: {len(content)} chars")
                else:
                    existing_files[fname] = ""
                    print(f"  {fname}: (empty)")
            except json.JSONDecodeError:
                existing_files[fname] = ""
                print(f"  {fname}: (parse error)")
        else:
            existing_files[fname] = ""
            print(f"  {fname}: (not found, will bootstrap)")

    # 3. Build the prompt
    print("\n── Building consolidation prompt ──")
    prompt = build_consolidation_prompt(moments_text, existing_files)
    print(f"Prompt length: {len(prompt)} chars, {len(moments_lines)} moments")

    if args.dry_run:
        print("\n── DRY RUN: Prompt preview ──")
        print(prompt[:2000])
        print(f"\n... ({len(prompt) - 2000} more chars)")
        print("\nNo changes made.")
        return

    # 4. Call DeepSeek
    if not args.api_key:
        print("Error: DEEPSEEK_API_KEY is required (set env var or use --api-key).")
        sys.exit(1)

    print("\n── Calling DeepSeek for consolidation ──")
    try:
        consolidated = call_deepseek(CONSOLIDATION_SYSTEM_PROMPT, prompt, args.model, args.api_key)
    except RuntimeError as e:
        print(f"DeepSeek error: {e}")
        sys.exit(1)

    # Validate response
    missing = [f for f in MEMORY_FILES if f not in consolidated]
    if missing:
        print(f"Error: DeepSeek response missing files: {missing}")
        print(f"Response keys: {list(consolidated.keys())}")
        sys.exit(1)

    # 5. POST consolidated files back to device
    print("\n── Sending consolidated files to device ──")
    payload: dict[str, object] = {"reset_moments": args.reset_moments}
    for fname in MEMORY_FILES:
        payload[fname] = consolidated[fname]

    # Send as raw JSON (not nested under "files") — the firmware uses simple
    # string-indexOf parsing that looks for "filename.json":"..." anywhere.
    body_str = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    req = urllib.request.Request(
        f"{bot_url}/memory/consolidate",
        data=body_str.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        print(f"Connection error: {e}")
        sys.exit(1)

    print(f"POST /memory/consolidate -> HTTP {status}")
    try:
        result = json.loads(body)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(body[:500])

    if status == 200:
        print("\n✓ Memory consolidation complete.")
    else:
        print("\n✗ Memory consolidation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
