#!/usr/bin/env python3
"""AI-generated line for the boot banner — replaces the old static mood text.

Calls an OpenAI-compatible chat endpoint to write one short line in the
persona/format below. The API key comes ONLY from the BOARD_AI_KEY env var
and is never hardcoded, logged, or printed. Any failure (missing key,
timeout, HTTP error, unparsable/empty reply) returns None so the caller can
fall back to a static message — the banner must always build.
"""
import json
import os
import re
import urllib.error
import urllib.request

API_URL = "https://gateway.9arm.co/v1/chat/completions"
MODEL = "qwen3.6-35b-a3b"
TIMEOUT_S = 15

ALLOWED_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 :./°-")
MAX_LINE_LEN = 24
MAX_LINES = 7
_LINE_SPLIT_RE = re.compile(r"\n| / ")

SYSTEM_PROMPT = """You write the message for a 24-column x 7-row split-flap
airport departure board.

HARD FORMAT (never break these):
- up to 7 lines, each up to 24 characters
- ALL CAPS
- allowed characters ONLY: A-Z 0-9 SPACE : . / ° -
- separate lines with a newline
- unused rows are fine — leave them out, the board blanks the rest for you
- info-dense, dry, zero filler. no greetings, no "here is", no explanations.

PERSONA: an 18 year old bangkok dev, weather nerd. dry humor over cute.
current projects: SOL (macOS menubar AI agent), BLOOD AI (discord bot),
sumo robot team on 127.0.0.1:67.

You have real creative range on this board: a two-line quip, a short list,
a mini status readout, whatever fits the board and the moment. You'll be
given live context — claude api status and local time. You may riff on any
of it, but you don't have to.

Reply with the message text ONLY. No quotes, no commentary.

Below are several EXAMPLE replies, separated by "---" for readability only —
never include "---" in your own reply, and never reply with more than one
message at once.

EXAMPLES:
CLAUDE DOWN / SO AM I
---
02:14 ICT
SUMO BOT STILL WINS
---
SOL STATUS:
SCREEN AWARENESS OK
PANIC STOP ARMED
LOCAL LLM WARM
---
BLOOD AI REFACTOR
13K LINES DEEP
PLUGIN ARCH: 60 PERCENT
STILL WORTH IT
---
GATE 67
NOW BOARDING
DESTINATION: SLEEP
DELAYED INDEFINITELY
---
TODAY I VALUE:
CLEAN COMPILES
STABLE WIFI
NO MERGE CONFLICTS
COFFEE
"""


def _clean_line(raw):
    cleaned = "".join(ch for ch in raw.upper() if ch in ALLOWED_CHARS)
    cleaned = " ".join(cleaned.split())
    return cleaned[:MAX_LINE_LEN].strip()


def _sanitize(raw_text):
    """Returns a list of 1-7 board-safe lines, or None if nothing survives."""
    if not raw_text:
        return None
    lines = []
    for candidate in _LINE_SPLIT_RE.split(raw_text.strip()):
        cleaned = _clean_line(candidate)
        if cleaned:
            lines.append(cleaned)
        if len(lines) == MAX_LINES:
            break
    return lines or None


def _call_api(api_key, user_prompt):
    body = json.dumps(
        {
            "model": MODEL,
            "temperature": 1.0,
            "max_tokens": 140,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"]


def get_message(claude_status="unknown", ict_time=""):
    """Returns a list of 1-7 sanitized, board-safe lines, or None on any failure."""
    api_key = os.environ.get("BOARD_AI_KEY")
    if not api_key:
        return None
    try:
        user_prompt = f"claude api status: {claude_status}\nlocal time: {ict_time}"
        raw = _call_api(api_key, user_prompt)
        return _sanitize(raw)
    except Exception:
        return None


if __name__ == "__main__":
    lines = get_message(claude_status="operational", ict_time="2026-07-10 21:14 ICT")
    print(lines if lines is not None else "None (no BOARD_AI_KEY, or call failed)")
