#!/usr/bin/env python3
"""Cloud bot server — runs on Tencent Cloud, replaces the laptop for bot brain.

Usage:
  python3 cloud_server.py --port 8080 --bot-url http://192.168.1.138
  python3 cloud_server.py --port 8080 --bot-url http://192.168.1.138 --config tools/bot_configs/grumpy.json

Endpoints:
  POST /chat  {"text": "你好"}  →  {"state": "SPEAKING", "screen_text": "Hi!", "speech_text": "你好！", ...}
  GET  /health                  →  {"ok": true}
  POST /send-to-device          →  sends the last reply to the T-RGB display
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# Add tools/ to path for bot_config import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bot_config import (
    load_bot_config,
    merge_memory_into_personality,
    build_full_system_prompt,
)

# ── DeepSeek ──────────────────────────────────────────────────────────────
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-flash"

FIRMWARE_STATES = frozenset({
    "IDLE", "LISTENING", "THINKING", "SPEAKING", "TEASING",
    "ANNOYED", "PROUD", "SLEEPY", "MEMORY", "UNCERTAIN",
    "HAPPY", "DISTRACTED", "MAD", "TIRED", "HUNGARY",
    "MISHEARD", "ACK", "DEEP_THINK", "RECALL", "DELIGHT",
    "CONCERN", "BOUNDARY", "INITIATE", "CAMERA_CURIOUS", "ATTENTION",
})


def normalize_state(state: str) -> str:
    """Map any state to one the firmware accepts."""
    state = state.strip().upper()
    if state in FIRMWARE_STATES:
        return state
    fallback = {
        "MISHEARD": "UNCERTAIN", "ACK": "IDLE", "DEEP_THINK": "THINKING",
        "RECALL": "MEMORY", "DELIGHT": "PROUD", "CONCERN": "SLEEPY",
        "BOUNDARY": "ANNOYED", "INITIATE": "SPEAKING",
        "CAMERA_CURIOUS": "THINKING", "ATTENTION": "LISTENING",
    }
    return fallback.get(state, "SPEAKING")


def call_deepseek(system_prompt: str, user_text: str, model: str, api_key: str) -> dict:
    """Call DeepSeek and return parsed JSON reply."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": 256,
        "temperature": 0.85,
        "thinking": {"type": "disabled"},
        "response_format": {"type": "json_object"},
    }

    req = urllib.request.Request(
        DEEPSEEK_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    content = data["choices"][0]["message"]["content"]
    return json.loads(content)


# ── T-RGB Device Helpers ──────────────────────────────────────────────────

def fetch_url(url: str, timeout: int = 10) -> tuple[int, str]:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return 0, str(e)


def fetch_conversation_context(bot_url: str, timeout: int = 10) -> str:
    tail = 8 * 350
    status, raw = fetch_url(f"{bot_url}/memory/moments.jsonl?tail={tail}", timeout)
    if status != 200:
        return ""
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    parts = []
    for line in lines[-8:]:
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


def send_to_device(bot_url: str, state: str, screen_text: str, timeout: int = 10) -> bool:
    query = urllib.parse.urlencode({"state": state, "text": screen_text})
    status, _ = fetch_url(f"{bot_url}/say?{query}", timeout)
    return status == 200


def log_to_device(bot_url: str, reply: dict, prompt: str, timeout: int = 10) -> bool:
    query = urllib.parse.urlencode({
        "event": "reply",
        "source": "cloud",
        "state": reply.get("state", "SPEAKING"),
        "screen_text": reply.get("screen_text", ""),
        "speech_text": (reply.get("speech_text", "") or "")[:220],
        "memory": (reply.get("memory_candidate", "") or "")[:160],
        "prompt": prompt[:180],
    })
    status, _ = fetch_url(f"{bot_url}/log?{query}", timeout)
    return status == 200


# ── Flask App ────────────────────────────────────────────────────────────
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global state (set at startup)
CONFIG: dict = {}
BOT_URL: str = ""
MODEL: str = DEFAULT_MODEL
_last_reply: dict = {}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "bot": CONFIG.get("name", "unknown"), "bot_url": BOT_URL})


@app.route("/chat", methods=["POST"])
def chat():
    """Main endpoint: send text, get bot reply."""
    global _last_reply

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"ok": False, "error": "missing 'text' field"}), 400

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return jsonify({"ok": False, "error": "DEEPSEEK_API_KEY not set on server"}), 500

    # Fetch conversation context
    conversation_context = ""
    if BOT_URL:
        conversation_context = fetch_conversation_context(BOT_URL)

    # Merge memory
    memory = merge_memory_into_personality(CONFIG, BOT_URL) if BOT_URL else {}

    # Build system prompt
    system_prompt = build_full_system_prompt(
        CONFIG, memory,
        conversation_context=conversation_context,
        memory_context_extra=memory.get("memory_context", ""),
    )

    # Call DeepSeek
    try:
        raw = call_deepseek(system_prompt, text, MODEL, api_key)
    except Exception as e:
        return jsonify({"ok": False, "error": f"DeepSeek error: {e}"}), 502

    # Normalize and build reply
    reply = {
        "state": normalize_state(raw.get("state", "SPEAKING")),
        "screen_text": raw.get("screen_text", ""),
        "speech_text": raw.get("speech_text", ""),
        "memory_candidate": raw.get("memory_candidate", ""),
        "follow_up": raw.get("follow_up", ""),
        "conversation_end": bool(raw.get("conversation_end", False)),
    }
    _last_reply = reply

    # Optionally send to device and log
    if BOT_URL:
        send_to_device(BOT_URL, reply["state"], reply["screen_text"])
        log_to_device(BOT_URL, reply, text)

    return jsonify({"ok": True, "reply": reply})


@app.route("/send-to-device", methods=["POST"])
def send_last():
    """Re-send the last reply to the T-RGB display."""
    if not _last_reply or not BOT_URL:
        return jsonify({"ok": False, "error": "no reply cached or no BOT_URL"}), 400

    ok = send_to_device(BOT_URL, _last_reply["state"], _last_reply["screen_text"])
    return jsonify({"ok": ok})


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cloud bot server for T-RGB companion.")
    parser.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--bot-url", default=os.environ.get("BOT_URL", ""),
                        help="T-RGB device URL (optional — if set, replies also go to device)")
    parser.add_argument("--config", default="",
                        help="Bot config JSON path (default: tools/bot_configs/default.json)")
    parser.add_argument("--model", default=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
                        help=f"DeepSeek model (default: {DEFAULT_MODEL})")
    parser.add_argument("--debug", action="store_true", help="Flask debug mode")
    args = parser.parse_args()

    global CONFIG, BOT_URL, MODEL
    CONFIG = load_bot_config(args.config if args.config else None)
    BOT_URL = args.bot_url.rstrip("/") if args.bot_url else ""
    MODEL = args.model

    print(f"🤖 {CONFIG['name']} cloud server starting on port {args.port}")
    if BOT_URL:
        print(f"📟 Device: {BOT_URL}")
    else:
        print("📟 Device: none (replies returned via API only)")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
