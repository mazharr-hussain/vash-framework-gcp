"""Fake LLM adapter for tests."""
from typing import Any, Mapping, Sequence
from vash.core.interfaces import LLMAdapter, LLMReply, RouteSettings
from vash.core.exceptions import RouteUnavailable

class FakeLLM(LLMAdapter):
    def __init__(self, settings: Mapping[str, Any], replies: Sequence[str] = ()):
        super().__init__(settings)
        self.replies = list(replies)
        self.requests: list[str] = []

    def reply(self, prompt: str, route: RouteSettings) -> LLMReply:
        self.requests.append(prompt)
        if not self.replies:
            raise RouteUnavailable("No more replies", "Add more to the fake")
        text = self.replies.pop(0)
        return LLMReply(text=text, route=route.name, model=route.model, degraded=False, usage={})
