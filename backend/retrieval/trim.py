"""
Adaptive trim window selection.

Given a source clip duration and (optionally) the narration / segment
time budget, ask Claude for a 4–12s start/duration pair that preserves
contemplative pacing.

Falls back to a deterministic 6–10s centred window if the LLM call
fails — the system never blocks on this.
"""
from __future__ import annotations

import json
import logging
import os
import re
import uuid
from typing import Optional

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

TRIM_SYSTEM = """You select a contemplative trim window for a stock cinematic clip.

Rules:
- Trim duration must be between 4.0 and 12.0 seconds.
- Prefer the calmest, most observational section: avoid the very start
  (often shaky / fade-in) and the very end (often action / fade-out).
- If narration_duration is provided, the trim must give the narration room
  to breathe — generally trim_duration >= narration_duration + 1.5.
- If pacing is "glacial", lean toward 8–12s; "slow" → 6–10s; "measured" → 4–8s.

Return ONLY JSON of the form:
{"start": <float seconds>, "duration": <float seconds>, "rationale": "<short>"}
No prose, no code fences."""


def _fallback(clip_duration: float, pacing: str, narration_dur: Optional[float]) -> dict:
    base = 8.0
    if pacing == "glacial":
        base = 10.0
    elif pacing == "measured":
        base = 6.0
    if narration_dur:
        base = max(base, narration_dur + 1.5)
    duration = max(4.0, min(12.0, min(base, max(2.0, clip_duration - 1.0))))
    start = max(0.0, (clip_duration - duration) / 2.0)
    return {
        "start": round(start, 2),
        "duration": round(duration, 2),
        "rationale": "Centred contemplative window.",
    }


def _extract_json(raw: str) -> dict:
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if not m:
        raise ValueError(f"Could not parse trim JSON: {raw[:160]}")
    return json.loads(m.group(0))


async def adaptive_trim(
    clip_duration: float,
    *,
    pacing: str = "slow",
    narration_duration: Optional[float] = None,
    rubric_atmosphere: str = "",
) -> dict:
    """Return {"start", "duration", "rationale"} for the trim window."""
    if not clip_duration or clip_duration <= 4.0:
        return {
            "start": 0.0,
            "duration": round(max(2.0, min(clip_duration, 12.0)), 2),
            "rationale": "Clip too short to trim — using full duration.",
        }

    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        return _fallback(clip_duration, pacing, narration_duration)

    try:
        chat = LlmChat(
            api_key=key,
            session_id=f"trim-{uuid.uuid4()}",
            system_message=TRIM_SYSTEM,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        payload = {
            "clip_duration": clip_duration,
            "pacing": pacing,
            "atmosphere": rubric_atmosphere,
            "narration_duration": narration_duration,
        }
        resp = await chat.send_message(UserMessage(text=json.dumps(payload)))
        out = _extract_json(resp if isinstance(resp, str) else str(resp))
        start = max(0.0, float(out.get("start", 0.0)))
        duration = float(out.get("duration", 8.0))
        duration = max(4.0, min(12.0, duration))
        # Clamp to clip range
        if start + duration > clip_duration:
            start = max(0.0, clip_duration - duration)
        return {
            "start": round(start, 2),
            "duration": round(duration, 2),
            "rationale": str(out.get("rationale", ""))[:240]
                or "Adaptive contemplative window.",
        }
    except Exception as e:  # noqa: BLE001
        logger.warning("Adaptive trim fallback: %s", e)
        return _fallback(clip_duration, pacing, narration_duration)
