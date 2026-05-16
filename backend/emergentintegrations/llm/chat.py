"""Stub for emergentintegrations.llm.chat.

Satisfies module-level imports so the backend can start.
Routes that actually invoke LlmChat will receive a 500 with an actionable message.
"""
from __future__ import annotations

_MSG = (
    "The emergentintegrations package is not installed in this environment. "
    "AI-powered features (scene analysis, clip ranking) are unavailable until "
    "the package can be installed. Core project/media/render routes are unaffected."
)


class UserMessage:
    def __init__(self, text: str = ""):
        self.text = text


class LlmChat:
    def __init__(self, api_key: str = "", session_id: str = "", system_message: str = "", **kwargs):
        self._api_key = api_key
        self._session_id = session_id
        self._system_message = system_message
        self._provider = "anthropic"
        self._model = ""

    def with_model(self, provider: str, model: str) -> "LlmChat":
        self._provider = provider
        self._model = model
        return self

    async def send_message(self, message: "UserMessage") -> str:
        raise RuntimeError(_MSG)
