"""
Clip ranker.

Given a list of `ProviderClip` candidates and a scene rubric, ask
Claude Sonnet 4.5 to score each clip 0–1 on cinematic restraint +
relevance, with a one-line rationale.

Broken into small helpers for testability:
    _pre_filter         : drop clips whose metadata matches rejected_keywords
    _build_payload      : serialise rubric + clips for the LLM
    _call_ranker_llm    : single LLM call returning a list of scores
    _apply_scores       : merge scores back onto the clip objects
    _filter_threshold   : drop below-threshold clips in Contemplative Mode
"""
from __future__ import annotations

import json
import logging
import os
import re
import uuid
from typing import List

from emergentintegrations.llm.chat import LlmChat, UserMessage

from .providers import ProviderClip

logger = logging.getLogger(__name__)

RANK_SYSTEM = """You are a cinematic curator selecting stock footage for a slow,
contemplative essay film. You favour:

    realism · contemplative atmosphere · muted palette · observational framing ·
    slow movement · natural lighting · institutional film feeling · essay-film
    aesthetic · emotional subtlety

You reject:

    vlog · hyperactive · neon/cyberpunk · motivational · commercial ·
    drone-spam · social-media style · oversaturated · fast cuts · selfie

For each clip given to you, score it from 0.0 to 1.0 based on how well it
fits the rubric and the contemplative ethos. Also write one short sentence
(≤20 words) explaining the score.

Return ONLY a JSON array, one object per clip, in the same order, of the form:
[
  {"i": 0, "score": 0.87, "rationale": "Muted dawn light, observational long take, no human movement."},
  ...
]
No extra prose, no code fences."""

DEFAULT_THRESHOLD = 0.55
MAX_CLIPS_PER_CALL = 24


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extract_json_array(raw: str) -> list:
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\[.*\]", s, re.DOTALL)
    if not m:
        raise ValueError(f"Could not extract JSON array: {raw[:200]}")
    return json.loads(m.group(0))


def _pre_filter(clips: List[ProviderClip], rubric: dict) -> List[ProviderClip]:
    """Drop clips that obviously fail the rubric or are malformed.

    Two filters:
      1. Zero-dimension clips (data-quality quirk on free Pixabay tier).
      2. Clips whose title/tags/query contain a rejected_keyword.
    """
    rejects = {k.lower() for k in (rubric.get("rejected_keywords") or [])}
    kept: List[ProviderClip] = []
    for c in clips:
        if c.width <= 0 or c.height <= 0:
            continue
        if rejects:
            haystack = " ".join([
                c.title.lower(),
                c.query.lower(),
                " ".join(c.tags).lower(),
            ])
            if any(bad in haystack for bad in rejects):
                continue
        kept.append(c)
    return kept


def _build_payload(
    clips: List[ProviderClip],
    rubric: dict,
    contemplative_mode: bool,
) -> dict:
    return {
        "rubric": {
            "emotional_tone": rubric.get("emotional_tone", ""),
            "pacing": rubric.get("pacing", "slow"),
            "environment": rubric.get("environment", ""),
            "atmosphere": rubric.get("atmosphere", ""),
            "restraint_level": rubric.get("restraint_level", 0.8),
            "preferred_keywords": rubric.get("preferred_keywords", []),
            "rejected_keywords": rubric.get("rejected_keywords", []),
        },
        "contemplative_mode": bool(contemplative_mode),
        "clips": [
            {
                "i": idx,
                "provider": c.provider,
                "title": c.title[:160],
                "tags": (c.tags or [])[:10],
                "duration": c.duration,
                "query": c.query,
                "resolution": f"{c.width}x{c.height}",
            }
            for idx, c in enumerate(clips)
        ],
    }


async def _call_ranker_llm(payload: dict) -> list:
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        raise RuntimeError("EMERGENT_LLM_KEY is not configured")

    chat = LlmChat(
        api_key=key,
        session_id=f"rank-{uuid.uuid4()}",
        system_message=RANK_SYSTEM,
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")

    resp = await chat.send_message(UserMessage(text=json.dumps(payload)))
    return _extract_json_array(resp if isinstance(resp, str) else str(resp))


def _apply_scores(clips: List[ProviderClip], scores: list) -> None:
    by_idx = {int(s.get("i", -1)): s for s in scores if isinstance(s, dict)}
    for idx, c in enumerate(clips):
        s = by_idx.get(idx) or {"score": 0.5, "rationale": "Unscored."}
        try:
            c.score = max(0.0, min(1.0, float(s.get("score", 0.5))))
        except (TypeError, ValueError):
            c.score = 0.5
        c.rationale = str(s.get("rationale") or "")[:240]


def _filter_threshold(
    clips: List[ProviderClip],
    threshold: float,
) -> List[ProviderClip]:
    return [c for c in clips if (c.score or 0.0) >= threshold]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
async def rank_clips(
    clips: List[ProviderClip],
    rubric: dict,
    contemplative_mode: bool = True,
    threshold: float = DEFAULT_THRESHOLD,
) -> List[ProviderClip]:
    """Score each clip, attach rationale, return sorted by score desc."""
    if not clips:
        return []

    clips = _pre_filter(clips, rubric)
    if not clips:
        return []

    clips = clips[:MAX_CLIPS_PER_CALL]
    payload = _build_payload(clips, rubric, contemplative_mode)

    try:
        scores = await _call_ranker_llm(payload)
    except Exception as e:  # noqa: BLE001
        logger.warning("Ranker LLM failed, falling back to flat scores: %s", e)
        scores = [
            {"i": i, "score": 0.5, "rationale": "Unscored."}
            for i in range(len(clips))
        ]

    _apply_scores(clips, scores)
    clips.sort(key=lambda x: (x.score or 0.0), reverse=True)

    if contemplative_mode:
        clips = _filter_threshold(clips, threshold)

    return clips
