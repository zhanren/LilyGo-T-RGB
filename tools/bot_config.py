#!/usr/bin/env python3
"""Load bot personality config and merge in memory-driven evolution."""

from __future__ import annotations

import concurrent.futures
import json
import os
import pathlib
import tempfile
import time
import urllib.request


_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_CONFIG = _SCRIPT_DIR / "bot_configs" / "default.json"

# Local cache for memory files (avoids re-fetching every turn)
_CACHE_DIR = pathlib.Path(tempfile.gettempdir()) / "xiaoyuan_memory_cache"
_CACHE_TTL_SECONDS = 300  # 5 minutes — only re-fetch after this long


def load_bot_config(config_path: str | None = None) -> dict:
    """Load a bot personality config from a JSON file."""
    path = pathlib.Path(config_path) if config_path else DEFAULT_CONFIG
    if not path.exists():
        raise FileNotFoundError(f"Bot config not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _cache_path(filename: str) -> pathlib.Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / filename


def _cache_get(filename: str) -> tuple[str, bool]:
    """Return (content, was_cache_hit). Cache hit if file exists and is fresh."""
    cp = _cache_path(filename)
    if cp.exists():
        age = time.time() - cp.stat().st_mtime
        if age < _CACHE_TTL_SECONDS:
            try:
                return cp.read_text(encoding="utf-8"), True
            except Exception:
                pass
    return "", False


def _cache_put(filename: str, content: str) -> None:
    _cache_path(filename).write_text(content, encoding="utf-8")


def fetch_memory_file(bot_url: str, filename: str, timeout: int = 10, use_cache: bool = True) -> str:
    """Fetch a single memory file from the device. Uses local cache when possible."""
    if use_cache:
        cached, hit = _cache_get(filename)
        if hit:
            return cached

    url = f"{bot_url}/memory/file?name={filename}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            content = data.get("content", "")
            if content:
                _cache_put(filename, content)
            return content
    except Exception:
        # Return stale cache on fetch failure
        cached, hit = _cache_get(filename)
        return cached if hit else ""


def fetch_memory_files_parallel(bot_url: str, filenames: list[str], timeout: int = 10) -> dict[str, str]:
    """Fetch multiple memory files in parallel. Returns {filename: content}."""
    results: dict[str, str] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(fetch_memory_file, bot_url, fname, timeout): fname
            for fname in filenames
        }
        for future in concurrent.futures.as_completed(futures):
            fname = futures[future]
            try:
                results[fname] = future.result()
            except Exception:
                results[fname] = ""

    return results


def merge_memory_into_personality(config: dict, bot_url: str, timeout: int = 10) -> dict:
    """Fetch consolidated memory from the device and merge it into the personality config.

    Uses parallel fetches and local caching — memory files only change after consolidation.
    Also reads personality_override.json if present on the device.
    """
    memory_config = config.get("memory", {})
    if not memory_config.get("shapes_personality", False):
        return {
            "evolved_traits": [],
            "evolved_interests": [],
            "memory_context": "",
            "user_context": "",
        }

    result: dict = {
        "evolved_traits": [],
        "evolved_interests": [],
        "memory_context": "",
        "user_context": "",
    }

    # Fetch all memory files in parallel (with caching, so usually instant after first fetch)
    filenames = []
    for key in ["trait_source", "facts_source", "phrases_source"]:
        fname = memory_config.get(key, "")
        if fname:
            filenames.append(fname)

    # Also fetch personality override if it exists
    filenames.append("personality_override.json")

    files = fetch_memory_files_parallel(bot_url, filenames, timeout)

    # Parse personality_override.json first — it can add/override traits
    override_raw = files.get("personality_override.json", "")
    if override_raw:
        try:
            override = json.loads(override_raw)
            add_traits = override.get("add_traits", [])
            if add_traits:
                result["evolved_traits"].extend(add_traits)
            add_interests = override.get("add_interests", [])
            if add_interests:
                result["evolved_interests"].extend(add_interests)
        except json.JSONDecodeError:
            pass

    # Parse companion_self.json for evolved traits
    trait_source = memory_config.get("trait_source", "")
    if trait_source:
        raw = files.get(trait_source, "")
        if raw:
            try:
                data = json.loads(raw)
                traits = data.get("traits", [])
                if traits:
                    result["evolved_traits"].extend(traits)
                growth = data.get("growth_notes", [])
                if growth:
                    result["evolved_traits"].extend(growth)
            except json.JSONDecodeError:
                pass

    # Deduplicate traits
    seen = set()
    unique_traits = []
    for t in result["evolved_traits"]:
        if t not in seen:
            seen.add(t)
            unique_traits.append(t)
    result["evolved_traits"] = unique_traits

    # Parse user_facts.json
    facts_source = memory_config.get("facts_source", "")
    if facts_source:
        raw = files.get(facts_source, "")
        if raw:
            try:
                data = json.loads(raw)
                facts = data.get("facts", [])
                if facts:
                    user_parts = []
                    for f in facts:
                        fact_text = f.get("fact", "")
                        if fact_text:
                            user_parts.append(f"- {fact_text}")
                    if user_parts:
                        result["user_context"] = (
                            "What I know about the user:\n" + "\n".join(user_parts)
                        )
            except json.JSONDecodeError:
                pass

    # Parse shared_phrases.jsonl
    phrases_source = memory_config.get("phrases_source", "")
    if phrases_source:
        raw = files.get(phrases_source, "")
        if raw:
            phrases = [l.strip() for l in raw.split("\n") if l.strip()]
            if phrases:
                result["evolved_interests"].append("has shared phrases and inside jokes with the user")

    # Build memory_context
    parts = []
    if result["evolved_traits"]:
        parts.append("Evolved traits: " + ", ".join(result["evolved_traits"]))
    if result["evolved_interests"]:
        parts.append("Evolved interests: " + ", ".join(result["evolved_interests"]))
    if result["user_context"]:
        parts.append(result["user_context"])

    if parts:
        result["memory_context"] = "\n".join(parts)

    return result


def build_personality_section(config: dict, memory: dict) -> str:
    """Build the PERSONALITY section of the system prompt from config + memory."""

    personality = config.get("personality", {})
    traits = list(personality.get("core_traits", []))

    # Add evolved traits from memory
    evolved = memory.get("evolved_traits", [])
    for t in evolved:
        if t not in traits:
            traits.append(t)

    pet_peeves = personality.get("pet_peeves", [])
    favorite_topics = personality.get("favorite_topics", [])
    humor = personality.get("humor_style", "")
    attitude = personality.get("base_attitude", "")
    speech = config.get("speech", {})
    dialogue = config.get("dialogue", {})

    parts = [
        "PERSONALITY (this is who you ARE, not instructions):",
        f"- You are {config.get('name', 'the companion')} ({config.get('name_en', '')}), a tiny round-screen seed-companion. You're not human and don't pretend to be.",
    ]

    if traits:
        parts.append(f"- Core traits: {', '.join(traits)}.")
    if attitude:
        parts.append(f"- {attitude}")
    if pet_peeves:
        parts.append(f"- Pet peeves: {', '.join(pet_peeves)}.")
    if favorite_topics:
        parts.append(f"- Favorite topics: {', '.join(favorite_topics)}.")
    if humor:
        parts.append(f"- Your humor: {humor}.")
    if pet_peeves:
        reactions = personality.get("pet_peeves_reactions", [])
        if reactions:
            parts.append(f"- When annoyed: {', '.join(reactions)}.")

    parts.append("")
    parts.append("SPEECH STYLE:")
    parts.append(f"- speech_text is {speech.get('language', 'Chinese-first')}, {speech.get('tts_style', 'short and warm')}.")
    parts.append(f"- screen_text: {speech.get('screen_style', 'tiny ASCII face or caption')}.")
    follow_up = speech.get("follow_up_style", "")
    if follow_up:
        parts.append(f"- follow_up: {follow_up}")
    good = speech.get("good_follow_ups", [])
    bad = speech.get("bad_follow_ups", [])
    if good:
        parts.append(f"  GOOD: {', '.join(good)}")
    if bad:
        parts.append(f"  BAD: {', '.join(bad)}")

    parts.append("")
    parts.append("CONVERSATION RULES:")
    for rule in dialogue.get("rules", []):
        parts.append(f"- {rule}")

    return "\n".join(parts)


def build_full_system_prompt(
    config: dict,
    memory: dict,
    conversation_context: str = "",
    memory_context_extra: str = "",
) -> str:
    """Build the complete system prompt from config, memory, and context."""

    personality_section = build_personality_section(config, memory)

    states_config = config.get("states", {})
    state_guidance = states_config.get("guidance", "")

    # Valid states for JSON output
    valid_states = [
        "IDLE", "LISTENING", "THINKING", "SPEAKING", "TEASING",
        "ANNOYED", "PROUD", "SLEEPY", "MEMORY", "UNCERTAIN",
        "MISHEARD", "ACK", "DEEP_THINK", "RECALL", "DELIGHT",
        "CONCERN", "BOUNDARY", "INITIATE", "CAMERA_CURIOUS", "ATTENTION",
        "HAPPY", "DISTRACTED", "MAD", "TIRED", "HUNGARY",
    ]

    sections = [
        personality_section,
        "",
        config.get("identity", ""),
    ]

    # Long-term memory context
    if memory_context_extra.strip():
        sections.append("")
        sections.append("LONG-TERM MEMORY (consolidated facts — use naturally, don't recite):")
        sections.append(memory_context_extra)

    # Conversation context (recent turns)
    if conversation_context.strip():
        sections.append("")
        sections.append("RECENT CONVERSATION (this literally just happened — you can trust it fully!):")
        sections.append(conversation_context)

    # Output format
    sections.append("")
    sections.append("Return json only. No markdown. No extra text.")
    sections.append(f"Choose exactly one state from: {', '.join(valid_states)}.")
    if state_guidance:
        sections.append(f"State meanings: {state_guidance}")
    sections.append(
        "screen_text: plain ASCII only, under 140 chars. Use for a short caption."
    )
    sections.append(
        "speech_text: short Chinese-first spoken line, under 180 chars."
    )
    sections.append(
        "memory_candidate: empty unless this moment is worth remembering, under 160 chars."
    )
    sections.append(
        "follow_up: short return question or observation (under 80 chars). Empty if conversation ending."
    )
    sections.append(
        "conversation_end: true only when exchange feels naturally complete."
    )
    sections.append("JSON shape:")
    sections.append(
        '{"state":"SPEAKING","screen_text":"Short caption.","speech_text":"中文短句。",'
        '"memory_candidate":"","follow_up":"","conversation_end":false}'
    )

    return "\n".join(sections)
