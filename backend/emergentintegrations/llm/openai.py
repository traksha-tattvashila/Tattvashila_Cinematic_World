"""Stub for emergentintegrations.llm.openai.

Satisfies module-level imports so the backend can start.
Routes that invoke OpenAITextToSpeech will receive a 500 with an actionable message.
"""
from __future__ import annotations

_MSG = (
    "The emergentintegrations package is not installed in this environment. "
    "Text-to-speech narration is unavailable until the package can be installed. "
    "Uploaded audio narration (non-TTS) and all other routes are unaffected."
)


class OpenAITextToSpeech:
    def __init__(self, api_key: str = "", **kwargs):
        self._api_key = api_key

    async def generate_speech(
        self,
        text: str = "",
        voice: str = "echo",
        model: str = "tts-1-hd",
        speed: float = 1.0,
        **kwargs,
    ) -> bytes:
        raise RuntimeError(_MSG)
