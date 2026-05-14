"""
Narration service — generates calm, measured narration audio using
OpenAI Text-to-Speech via the Emergent universal key.

The cinematic voices we expose (echo, sage, onyx, fable) are chosen
for their grounded, observational quality. Avoid energetic voices.
"""
from __future__ import annotations

import os
import logging
from emergentintegrations.llm.openai import OpenAITextToSpeech

logger = logging.getLogger(__name__)

# Voices ordered for contemplative cinema first.
CINEMATIC_VOICES = [
    {"key": "echo", "label": "Echo — smooth, measured"},
    {"key": "sage", "label": "Sage — wise, deliberate"},
    {"key": "onyx", "label": "Onyx — deep, grounded"},
    {"key": "fable", "label": "Fable — narrative, restrained"},
    {"key": "alloy", "label": "Alloy — neutral"},
    {"key": "ash", "label": "Ash — clear, austere"},
]

TTS_MODELS = ["tts-1-hd", "tts-1"]


def _client() -> OpenAITextToSpeech:
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        raise RuntimeError("EMERGENT_LLM_KEY is not configured")
    return OpenAITextToSpeech(api_key=key)


async def synthesize(
    text: str,
    voice: str = "echo",
    model: str = "tts-1-hd",
    speed: float = 0.95,
) -> bytes:
    """Return MP3 bytes for the given narration text."""
    if not text or not text.strip():
        raise ValueError("Narration text is empty")
    # Keep the first 4096 chars to respect the API limit; longer scripts
    # should be split into multiple segments by the caller.
    text = text.strip()[:4096]
    tts = _client()
    audio = await tts.generate_speech(
        text=text,
        model=model,
        voice=voice,
        speed=speed,
        response_format="mp3",
    )
    return audio
