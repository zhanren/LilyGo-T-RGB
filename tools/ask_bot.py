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

# Config system
from bot_config import (
    load_bot_config,
    merge_memory_into_personality,
    build_full_system_prompt,
)

DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-flash"

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
    follow_up: str = ""
    conversation_end: bool = False


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
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Do not inject the bot's consolidated memory into the system prompt.",
    )
    parser.add_argument(
        "--conversation-timeout",
        type=int,
        default=0,
        help="Seconds to wait for user reply before logging a conversation-end event. 0 disables.",
    )
    parser.add_argument(
        "--config",
        default=os.environ.get("BOT_CONFIG", ""),
        help="Path to bot config JSON file. Defaults to tools/bot_configs/default.json. Can also set BOT_CONFIG.",
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
    """Map any state to one the firmware accepts."""
    state = make_screen_safe(state).strip().upper()

    # Firmware-supported states (must match main.cpp face_states)
    FIRMWARE_STATES = frozenset({
        "IDLE", "LISTENING", "THINKING", "SPEAKING", "TEASING",
        "ANNOYED", "PROUD", "SLEEPY", "MEMORY", "UNCERTAIN",
        "HAPPY", "DISTRACTED", "MAD", "TIRED", "HUNGARY",
        "MISHEARD", "ACK", "DEEP_THINK", "RECALL", "DELIGHT",
        "CONCERN", "BOUNDARY", "INITIATE", "CAMERA_CURIOUS", "ATTENTION",
    })

    if state in FIRMWARE_STATES:
        return state

    # Map extended states to firmware-safe equivalents
    EXTENDED_MAP = {
        "MISHEARD": "UNCERTAIN",
        "ACK": "IDLE",
        "DEEP_THINK": "THINKING",
        "RECALL": "MEMORY",
        "DELIGHT": "PROUD",
        "CONCERN": "SLEEPY",
        "BOUNDARY": "ANNOYED",
        "INITIATE": "SPEAKING",
        "CAMERA_CURIOUS": "THINKING",
        "ATTENTION": "LISTENING",
    }

    return EXTENDED_MAP.get(state, "SPEAKING")


def extract_chat_text(response_json: dict) -> str:
    choices = response_json.get("choices", [])
    if not choices:
        return ""

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()

    return ""


def ask_deepseek(prompt: str, model: str, system_prompt: str) -> BotReply:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY. Set it in your terminal first.")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 256,
        "temperature": 0.85,
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

    return parse_bot_reply(answer, 140)


def parse_bot_reply(content: str, max_chars: int) -> BotReply:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"DeepSeek did not return valid JSON:\n{content}") from exc

    state = normalize_state(str(payload.get("state", "SPEAKING")))
    raw_screen_text = payload.get("screen_text", payload.get("text", ""))
    screen_text = trim_for_screen(str(raw_screen_text), max_chars)
    speech_text = trim_text(str(payload.get("speech_text", screen_text)), 180)
    memory_candidate = trim_text(str(payload.get("memory_candidate", "")), 160)
    follow_up = trim_text(str(payload.get("follow_up", "")), 80)
    conversation_end = bool(payload.get("conversation_end", False))

    if not screen_text:
        raise RuntimeError(f"DeepSeek JSON did not include reply text:\n{content}")

    return BotReply(
        state=state,
        screen_text=screen_text,
        speech_text=speech_text,
        memory_candidate=memory_candidate,
        follow_up=follow_up,
        conversation_end=conversation_end,
    )


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


def fetch_memory_context(bot_url: str, timeout: int) -> str:
    """Fetch consolidated memory files from the device and format them for the system prompt."""
    memory_files = [
        ("companion_self.json", "Who I am"),
        ("user_facts.json", "What I know about the user"),
        ("shared_phrases.jsonl", "Shared phrases and inside jokes"),
        ("boundaries.json", "User boundaries"),
        ("backstory_fragments.json", "Backstory fragments"),
    ]

    parts = []
    for fname, label in memory_files:
        url = f"{bot_url}/memory/file?name={fname}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                content = data.get("content", "")
                if content.strip():
                    parts.append(f"[{label}]")
                    parts.append(content)
        except Exception:
            pass  # File doesn't exist yet, skip

    return "\n".join(parts)


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


def fetch_conversation_context(bot_url: str, timeout: int, num_turns: int = 8) -> str:
    """Fetch the most recent moments from the device using ?tail= to avoid downloading the whole file."""
    # ~250 bytes per moment line, 8 lines ≈ 2000 bytes. Use 3000 for safety.
    tail_bytes = num_turns * 350
    url = f"{bot_url}/memory/moments.jsonl?tail={tail_bytes}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return ""

    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    if not lines:
        return ""

    # Take the last N turns
    recent = lines[-num_turns:]

    parts = []
    for line in recent:
        try:
            m = json.loads(line)
            prompt = m.get("prompt", "")
            speech = m.get("speech_text", "")
            state = m.get("state", "")
            if prompt and speech:
                parts.append(f"User: {prompt} → 小圆 [{state}]: {speech}")
        except json.JSONDecodeError:
            continue

    return "\n".join(parts)


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
    # Load bot configuration
    config = load_bot_config(args.config)
    bot_name = config.get("name", "companion")
    print(f"Bot: {bot_name}", end="")

    # Fetch conversation context (recent turns from moments.jsonl)
    conversation_context = ""
    if bot_url:
        try:
            conversation_context = fetch_conversation_context(bot_url, timeout=min(args.bot_timeout, 10))
            if conversation_context:
                lines = conversation_context.count("\n") + 1
                print(f", {lines} recent turns loaded")
            else:
                print()
        except Exception as e:
            print(f"\nConversation fetch skipped: {e}")
    else:
        print()

    # Fetch consolidated memory and merge into personality (unless --no-memory)
    memory = {"evolved_traits": [], "evolved_interests": [], "memory_context": "", "user_context": ""}
    if bot_url and not args.no_memory:
        try:
            memory = merge_memory_into_personality(config, bot_url, timeout=min(args.bot_timeout, 10))
            if memory["evolved_traits"]:
                print(f"Evolved traits: {', '.join(memory['evolved_traits'])}")
            if memory["user_context"]:
                print(f"User context: {len(memory['user_context'])} chars loaded")
        except Exception as e:
            print(f"Memory merge skipped: {e}")

    # Build the full system prompt from config + memory
    system_prompt = build_full_system_prompt(
        config,
        memory,
        conversation_context=conversation_context,
        memory_context_extra=memory.get("memory_context", ""),
    )

    if args.mock:
        reply = BotReply(
            state=normalize_state(args.state if args.state != "AUTO" else "SPEAKING"),
            screen_text=trim_for_screen(f"I heard you ask: {prompt}", args.max_chars),
            speech_text=trim_text(f"我听到了。你刚才说: {prompt}", 180),
            memory_candidate="",
        )
    else:
        reply = ask_deepseek(prompt, args.model, system_prompt)

    if args.state != "AUTO":
        reply.state = normalize_state(args.state)

    print(f"Bot state: {reply.state}", end="")
    if reply.conversation_end:
        print(" (conversation ending)")
    else:
        print()
    print(f"Screen text: {reply.screen_text}")
    print(f"Speech text: {reply.speech_text}")
    if reply.memory_candidate:
        print(f"Memory candidate: {reply.memory_candidate}")
    if reply.follow_up:
        print(f"Follow-up: {reply.follow_up}")

    url = build_bot_url(bot_url, reply.state, reply.screen_text) if bot_url else "(no bot URL)"
    print(f"T-RGB URL: {url}")
    result = "(no bot URL)" if not bot_url else send_to_bot(url, args.dry_run, args.bot_timeout)
    print(f"T-RGB result: {result}")
    if bot_url and not args.skip_memory_log:
        log_result = send_memory_log(bot_url, reply, prompt, source, args.dry_run, args.bot_timeout)
        print(f"Memory log: {log_result}")
    if args.speak:
        print(f"TTS: {speak_text(reply.speech_text or reply.screen_text, args.voice)}", flush=True)

    # If the bot ended the conversation, note it
    if reply.conversation_end and bot_url and not args.skip_memory_log:
        end_url = f"{bot_url}/log?event=conversation_end&source={source}&state={reply.state}"
        end_result = send_to_bot(end_url, args.dry_run, args.bot_timeout)
        print(f"Conversation end log: {end_result}")

    # If --conversation-timeout is set, wait for user reply
    if args.conversation_timeout > 0 and bot_url:
        print(f"\nWaiting {args.conversation_timeout}s for your reply... (Ctrl+C to stop)")
        try:
            _ = input()
        except (KeyboardInterrupt, EOFError):
            timeout_url = (
                f"{bot_url}/log?"
                f"event=conversation_timeout&source=laptop&state={reply.state}"
                f"&screen_text={urllib.parse.quote('Conversation timed out.')}"
            )
            timeout_result = send_to_bot(timeout_url, args.dry_run, args.bot_timeout)
            print(f"Conversation timeout log: {timeout_result}")


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
