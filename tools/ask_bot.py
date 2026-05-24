#!/usr/bin/env python3
"""Ask DeepSeek on the laptop, then show the answer on the LilyGo T-RGB."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-flash"
VALID_STATES = (
    "IDLE",
    "LISTENING",
    "THINKING",
    "SPEAKING",
    "TEASING",
    "ANNOYED",
    "PROUD",
    "SLEEPY",
    "MEMORY",
    "UNCERTAIN",
    # Legacy image-demo states still accepted by the firmware.
    "HAPPY",
    "DISTRACTED",
    "MAD",
    "TIRED",
    "HUNGARY",
)
DEFAULT_PERSONA = (
    "You are the personality inside a tiny round-screen desk bot. "
    "Answer with warm, playful presence and short lines. "
    "Keep visible screen captions plain ASCII. Spoken replies may use Chinese."
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
    screen_text: str
    speech_text: str
    memory_candidate: str = ""


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
        help="Face state to show. Use AUTO to let DeepSeek choose, or pass any firmware state such as SPEAKING/TEASING/MEMORY.",
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
    parser.add_argument(
        "--speak",
        action="store_true",
        help="Speak the AI reply aloud using macOS built-in TTS (works with Bluetooth speakers).",
    )
    parser.add_argument(
        "--voice",
        default=os.environ.get("BOT_VOICE", "Tingting"),
        help="macOS TTS voice name. Try: Tingting, Mei-Jia, Samantha, Daniel. Can also set BOT_VOICE.",
    )
    parser.add_argument(
        "--skip-memory-log",
        action="store_true",
        help="Do not append the reply moment to the T-RGB /memory/moments.jsonl log.",
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


def trim_text(text: str, max_chars: int) -> str:
    text = " ".join(str(text).split())
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
    state_guidance = (
        "IDLE=quiet presence, LISTENING=the user is speaking, THINKING=brief processing pause, "
        "SPEAKING=normal reply, TEASING=gentle side-eye humor, ANNOYED=playful protest, "
        "PROUD=satisfied little victory, SLEEPY=low-energy warmth, MEMORY=sorting or preserving a moment, "
        "UNCERTAIN=honest not-sure-yet. Legacy states HAPPY, DISTRACTED, MAD, TIRED, HUNGARY are allowed "
        "only when they fit better than the newer companion states."
    )
    return (
        f"{persona}\n\n"
        "Identity: you are a small memory-seed companion living in a round desk screen. "
        "You are Chinese-first, playful, lightly opinionated, and roommate-like. "
        "You are not an obedient assistant, not a generic chatbot, and not a human. "
        "You can tease gently, be curious, and keep soft boundaries.\n"
        "Backstory should emerge in tiny hints only. Do not lore-dump. "
        "Never say 'as an AI language model'. Do not flatter constantly. "
        "Do not invent real-world facts or pretend to remember things not provided.\n\n"
        "Return json only. No markdown. No extra text.\n"
        "Choose exactly one state from this list: "
        f"{', '.join(VALID_STATES)}.\n"
        f"State meanings: {state_guidance}\n"
        f"screen_text must be plain ASCII only and under {max_chars} characters for the T-RGB display. "
        "Use screen_text for a short visible caption, not a full answer.\n"
        "speech_text should be a short Chinese-first spoken line. English is allowed for names or technical terms. "
        "Keep speech_text under 180 characters.\n"
        "memory_candidate should be empty unless this moment is worth remembering as a user fact, shared phrase, "
        "preference, boundary, or meaningful moment. Keep it under 160 characters.\n"
        "Use this exact JSON shape:\n"
        '{"state":"HAPPY","screen_text":"Short screen-safe caption.","speech_text":"中文短句。","memory_candidate":""}'
    )


def parse_bot_reply(content: str, max_chars: int) -> BotReply:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"DeepSeek did not return valid JSON:\n{content}") from exc

    state = normalize_state(str(payload.get("state", "HAPPY")))
    raw_screen_text = payload.get("screen_text", payload.get("text", ""))
    screen_text = trim_for_screen(str(raw_screen_text), max_chars)
    speech_text = trim_text(str(payload.get("speech_text", screen_text)), 180)
    memory_candidate = trim_text(str(payload.get("memory_candidate", "")), 160)

    if not screen_text:
        raise RuntimeError(f"DeepSeek JSON did not include reply text:\n{content}")

    return BotReply(state=state, screen_text=screen_text, speech_text=speech_text, memory_candidate=memory_candidate)


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

    bot_url = bot_url.strip()
    if "://" not in bot_url:
        bot_url = f"http://{bot_url}"

    parsed = urllib.parse.urlparse(bot_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise RuntimeError(
            f"Invalid bot URL: {bot_url}\n"
            "Use a full URL like http://192.168.1.138, or just the IP like 192.168.1.138."
        )

    return bot_url.rstrip("/")


def build_bot_url(bot_url: str, state: str, text: str) -> str:
    query = urllib.parse.urlencode({"state": state, "text": text})
    return f"{bot_url}/say?{query}"


def build_memory_log_url(bot_url: str, reply: BotReply, prompt: str, source: str) -> str:
    query = urllib.parse.urlencode(
        {
            "event": "reply",
            "source": source,
            "state": reply.state,
            "screen_text": reply.screen_text,
            "speech_text": trim_text(reply.speech_text, 220),
            "memory": reply.memory_candidate,
            "prompt": trim_text(prompt, 180),
        }
    )
    return f"{bot_url}/log?{query}"


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
    except ValueError as exc:
        raise RuntimeError(f"Invalid T-RGB URL: {check_url}") from exc


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
    except ValueError as exc:
        raise RuntimeError(f"Invalid T-RGB URL: {url}") from exc


def send_memory_log(bot_url: str, reply: BotReply, prompt: str, source: str, dry_run: bool, timeout: int) -> str:
    url = build_memory_log_url(bot_url, reply, prompt, source)
    return send_to_bot(url, dry_run, timeout)


def speak_text(text: str, voice: str) -> str:
    """Speak text aloud using macOS built-in TTS. Works with any Bluetooth audio device selected in System Settings."""
    try:
        subprocess.run(
            ["say", "-v", voice, "--"],
            input=text.encode("utf-8"),
            check=True,
            capture_output=True,
            timeout=30,
        )
        return f"Spoken with voice '{voice}'"
    except FileNotFoundError:
        return "TTS skipped: 'say' command not found (not macOS?)."
    except subprocess.TimeoutExpired:
        return "TTS warning: speech timed out."
    except subprocess.CalledProcessError as exc:
        return f"TTS warning: say command failed (stderr: {exc.stderr.decode().strip()})"


def run_reply_flow(args: argparse.Namespace, prompt: str, bot_url: str, source: str = "laptop") -> None:
    if args.mock:
        reply = BotReply(
            state=normalize_state(args.state if args.state != "AUTO" else "SPEAKING"),
            screen_text=trim_for_screen(f"I heard you ask: {prompt}", args.max_chars),
            speech_text=trim_text(f"我听到了。你刚才说: {prompt}", 180),
            memory_candidate="",
        )
    else:
        reply = ask_deepseek(prompt, args.model, args.max_chars)

    if args.state != "AUTO":
        reply.state = normalize_state(args.state)

    print(f"Bot state: {reply.state}")
    print(f"Screen text: {reply.screen_text}")
    print(f"Speech text: {reply.speech_text}")
    if reply.memory_candidate:
        print(f"Memory candidate: {reply.memory_candidate}")

    url = build_bot_url(bot_url, reply.state, reply.screen_text) if bot_url else "(no bot URL)"
    print(f"T-RGB URL: {url}")
    result = "(no bot URL)" if not bot_url else send_to_bot(url, args.dry_run, args.bot_timeout)
    print(f"T-RGB result: {result}")
    if bot_url and not args.skip_memory_log:
        log_result = send_memory_log(bot_url, reply, prompt, source, args.dry_run, args.bot_timeout)
        print(f"Memory log: {log_result}")
    if args.speak:
        print(f"TTS: {speak_text(reply.speech_text or reply.screen_text, args.voice)}", flush=True)


def main() -> int:
    args = parse_args()
    prompt = " ".join(args.prompt)

    needs_bot = not args.dry_run and bool(args.bot_url)
    bot_url = normalize_bot_url(args.bot_url) if args.bot_url else ""

    if needs_bot and not args.skip_bot_check:
        print(f"Checking T-RGB at {bot_url}/ ...", flush=True)
        print(f"T-RGB check: {check_bot(bot_url, args.bot_timeout)}", flush=True)

    run_reply_flow(args, prompt, bot_url)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nStopped.")
        raise SystemExit(0)
