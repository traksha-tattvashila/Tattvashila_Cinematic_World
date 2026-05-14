"""
Scene → cinematic rubric.

Uses Claude Sonnet 4.5 (via emergentintegrations + EMERGENT_LLM_KEY) to
translate freeform scene descriptions into a strict JSON rubric used
downstream for stock retrieval and ranking.
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

MODEL_PROVIDER = "anthropic"
MODEL_NAME = "claude-sonnet-4-5-20250929"

SCENE_SYSTEM = """You are a cinematographer for an institutional slow-cinema studio.
Your role is to translate a freeform scene description into a precise rubric
for searching stock cinematic footage.

You explicitly REJECT vlog, motivational, hyperactive, neon, cyberpunk,
commercial, drone-spam, and social-media aesthetics. You prefer realism,
restraint, natural lighting, observational framing, slow movement, muted
colour, and emotional subtlety.

Return ONLY valid JSON (no markdown, no prose) with this exact shape:
{
  "emotional_tone": "<one short phrase>",
  "pacing": "glacial" | "slow" | "measured",
  "environment": "<one short phrase>",
  "restraint_level": <float 0.0-1.0, higher = more restrained>,
  "atmosphere": "<one short phrase>",
  "search_queries": ["q1", "q2", "q3"],
  "preferred_keywords": ["k1", "k2", ...],
  "rejected_keywords": ["k1", "k2", ...],
  "rationale": "<one sentence on why this rubric fits the scene>"
}

Rules:
- search_queries must be 3 to 5 short atmospheric phrases (2–5 words each),
  written as a human would search a stock library (e.g.
  "empty subway platform dawn", "quiet woman reading window light").
- Avoid generic words like "happy", "energetic", "vibrant".
- preferred_keywords: 5–10 atmospheric tags that should boost ranking.
- rejected_keywords: 5–10 tags whose presence should downrank.
- If contemplative_mode=ON, push restraint_level toward 0.85+ and add
  reject terms like "vlog", "tiktok", "motivational", "advertisement"."""


def _extract_json(raw: str) -> dict:
    """Forgiving JSON extraction from model output."""
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    # Try direct parse
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # Find first {...}
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if not m:
        raise ValueError(f"Could not extract JSON from model output: {raw[:200]}")
    return json.loads(m.group(0))


async def analyze_scene(
    description: str,
    contemplative_mode: bool = True,
    narration_text: Optional[str] = None,
) -> dict:
    """Return the rubric dict for the given scene description."""
    if not description.strip():
        raise ValueError("Scene description is empty")

    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        raise RuntimeError("EMERGENT_LLM_KEY is not configured")

    chat = LlmChat(
        api_key=key,
        session_id=f"scene-{uuid.uuid4()}",
        system_message=SCENE_SYSTEM,
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    parts = [
        f"Scene: {description.strip()}",
        f"Contemplative mode: {'ON' if contemplative_mode else 'OFF'}",
    ]
    if narration_text and narration_text.strip():
        parts.append(f"Narration excerpt: {narration_text.strip()[:600]}")
    parts.append("Return JSON only.")

    resp = await chat.send_message(UserMessage(text="\n".join(parts)))
    rubric = _extract_json(resp if isinstance(resp, str) else str(resp))

    # Defensive defaults
    rubric.setdefault("emotional_tone", "")
    rubric.setdefault("pacing", "slow")
    rubric.setdefault("environment", "")
    rubric.setdefault("atmosphere", "")
    rubric.setdefault("rationale", "")
    rubric["restraint_level"] = float(rubric.get("restraint_level", 0.8))
    rubric["search_queries"] = list(rubric.get("search_queries") or [])[:5]
    rubric["preferred_keywords"] = list(rubric.get("preferred_keywords") or [])[:12]
    rubric["rejected_keywords"] = list(rubric.get("rejected_keywords") or [])[:12]
    return rubric
