#!/usr/bin/env python3
"""Ask DeepSeek on the laptop, then show the answer on the LilyGo T-RGB."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request


DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-flash"
VALID_STATES = ("IDLE", "HAPPY", "DISTRACTED", "MAD", "TIRED", "HUNGARY")
DEFAULT_PERSONA = (
    "You are the personality inside a tiny round-screen desk bot. "
    "Answer warmly and playfully, but keep it short enough for a 480x480 screen. "
    "Use plain ASCII text only. Do not use emoji, curly quotes, or fancy punctuation."
)

SCREEN_SAFE_REPLACEMENTS = {
    0x00A0: " ",
    0x2018: "'",
    0x2019: "'",
    0x201A: "'",
    0x201B: "'",
    0x201C: '"',
    0x201D: '"',
    0x201E: '"',
    0x201F: '"',
    0x2013: "-",
    0x2014: "-",
    0x2015: "-",
    0x2022: "-",
    0x2026: "...",
}


@dataclass
class BotReply:
    state: str
    text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a prompt to DeepSeek and forward the answer to the T-RGB bot."
    )
    parser.add_argument("prompt", nargs="+", help="What you want to ask the bot.")
    parser.add_argument(
        "--bot-url",
        default=os.environ.get("BOT_URL", ""),
        help="Base URL for the T-RGB, like http://192.168.1.123. Can also use BOT_URL.",
    )
    parser.add_argument(
        "--state",
        default="AUTO",
        help="Face state to show. Use AUTO to let DeepSeek choose, or IDLE/HAPPY/DISTRACTED/MAD/TIRED/HUNGARY.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
        help=f"DeepSeek model name. Defaults to {DEFAULT_MODEL}, or DEEPSEEK_MODEL.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=140,
        help="Maximum characters sent to the small screen.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Skip DeepSeek and use a fake answer for local testing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the T-RGB URL instead of sending it.",
    )
    parser.add_argument(
        "--bot-timeout",
        type=int,
        default=20,
        help="Seconds to wait for the T-RGB HTTP server.",
    )
    parser.add_argument(
        "--skip-bot-check",
        action="store_true",
        help="Do not test BOT_URL before calling DeepSeek.",
    )
    return parser.parse_args()


def make_screen_safe(text: str) -> str:
    text = text.translate(SCREEN_SAFE_REPLACEMENTS)
    return "".join(char if 32 <= ord(char) <= 126 else " " for char in text)


def trim_for_screen(text: str, max_chars: int) -> str:
    text = " ".join(make_screen_safe(text).split())
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 3)].rstrip() + "..."


def normalize_state(state: str) -> str:
    state = make_screen_safe(state).strip().upper()
    if state in VALID_STATES:
        return state
    return "HAPPY"


def extract_chat_text(response_json: dict) -> str:
    choices = response_json.get("choices", [])
    if not choices:
        return ""

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()

    return ""


def build_system_prompt(max_chars: int) -> str:
    persona = os.environ.get("BOT_PERSONA", DEFAULT_PERSONA)
    return (
        f"{persona}\n\n"
        "Return json only. No markdown. No extra text.\n"
        "Choose exactly one state from this list: "
        f"{', '.join(VALID_STATES)}.\n"
        f"Keep text under {max_chars} characters.\n"
        "Use this exact JSON shape:\n"
        '{"state":"HAPPY","text":"Short screen-safe reply."}'
    )


def parse_bot_reply(content: str, max_chars: int) -> BotReply:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"DeepSeek did not return valid JSON:\n{content}") from exc

    state = normalize_state(str(payload.get("state", "HAPPY")))
    text = trim_for_screen(str(payload.get("text", "")), max_chars)
    if not text:
        raise RuntimeError(f"DeepSeek JSON did not include reply text:\n{content}")

    return BotReply(state=state, text=text)


def ask_deepseek(prompt: str, model: str, max_chars: int) -> BotReply:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY. Set it in your terminal first.")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": build_system_prompt(max_chars)},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 120,
        "temperature": 0.8,
        "thinking": {"type": "disabled"},
        "response_format": {"type": "json_object"},
    }

    request = urllib.request.Request(
        DEEPSEEK_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_json = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek request failed: HTTP {exc.code}\n{body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"DeepSeek request failed: {exc.reason}") from exc

    answer = extract_chat_text(response_json)
    if not answer:
        raise RuntimeError("DeepSeek response did not contain text.")

    return parse_bot_reply(answer, max_chars)


def normalize_bot_url(bot_url: str) -> str:
    if not bot_url:
        raise RuntimeError("Missing bot URL. Pass --bot-url or set BOT_URL.")

    return bot_url.rstrip("/")


def build_bot_url(bot_url: str, state: str, text: str) -> str:
    query = urllib.parse.urlencode({"state": state, "text": text})
    return f"{bot_url}/say?{query}"


def check_bot(bot_url: str, timeout: int) -> str:
    check_url = f"{bot_url}/"
    try:
        with urllib.request.urlopen(check_url, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            first_line = body.splitlines()[0] if body.splitlines() else "OK"
            return f"HTTP {response.status}: {first_line}"
    except socket.timeout as exc:
        raise RuntimeError(
            f"T-RGB did not answer at {check_url} within {timeout}s.\n"
            "Check that the board is powered on, still showing a Wi-Fi IP, "
            "and your laptop is on the same Wi-Fi."
        ) from exc
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"T-RGB check failed: HTTP {exc.code}\n{body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"T-RGB check failed at {check_url}: {exc.reason}\n"
            "Open that URL in your browser. If it does not load, update BOT_URL "
            "to the IP currently shown on the LilyGo screen."
        ) from exc


def send_to_bot(url: str, dry_run: bool, timeout: int) -> str:
    if dry_run:
        return "DRY RUN"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return f"HTTP {response.status}: {body}"
    except socket.timeout as exc:
        raise RuntimeError(
            f"T-RGB request timed out after {timeout}s.\n"
            "The AI answer was generated, but the board did not answer the /say request. "
            "Check the board IP, reset the board if the screen looks frozen, then try again."
        ) from exc
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"T-RGB request failed: HTTP {exc.code}\n{body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"T-RGB request failed: {exc.reason}") from exc


def main() -> int:
    args = parse_args()
    prompt = " ".join(args.prompt)
    bot_url = normalize_bot_url(args.bot_url)

    if not args.dry_run and not args.skip_bot_check:
        print(f"Checking T-RGB at {bot_url}/ ...", flush=True)
        print(f"T-RGB check: {check_bot(bot_url, args.bot_timeout)}", flush=True)

    if args.mock:
        reply = BotReply(
            state=normalize_state(args.state if args.state != "AUTO" else "HAPPY"),
            text=trim_for_screen(f"I heard you ask: {prompt}", args.max_chars),
        )
    else:
        reply = ask_deepseek(prompt, args.model, args.max_chars)

    if args.state != "AUTO":
        reply.state = normalize_state(args.state)

    print(f"Bot state: {reply.state}")
    print(f"Bot answer: {reply.text}")
    url = build_bot_url(bot_url, reply.state, reply.text)
    print(f"T-RGB URL: {url}")
    result = send_to_bot(url, args.dry_run, args.bot_timeout)
    print(f"T-RGB result: {result}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
