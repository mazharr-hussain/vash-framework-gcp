"""OpenAI-compatible LLM adapter."""
import json
import os
import urllib.request
import urllib.error
from typing import Any, Mapping
from vash.core.interfaces import LLMAdapter, LLMReply, RouteSettings
from vash.core.exceptions import RouteUnavailable, VashError

class Adapter(LLMAdapter):
    """OpenAI-compatible LLM adapter."""
    def __init__(self, settings: Mapping[str, Any]):
        super().__init__(settings)

    def reply(self, prompt: str, route: RouteSettings) -> LLMReply:
        base_url = route.base_url or self.settings.get("base_url")
        if not base_url:
            raise VashError("base_url is required for openai_compatible", "Set models.routes.<name>.base_url")

        key_env = route.key_env or self.settings.get("key_env")
        api_key = os.environ.get(key_env, "") if key_env else ""
        if not api_key:
            raise RouteUnavailable(
                f"API key missing in env var {key_env}",
                f"Set {key_env} environment variable"
            )
        url = f"{base_url.rstrip('/')}/chat/completions"
        data = {
            "model": route.model,
            "messages": [{"role": "user", "content": prompt}]
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        req = urllib.request.Request(
            url, data=json.dumps(data).encode("utf-8"),
            headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=route.timeout_s) as response:
                res = json.loads(response.read().decode("utf-8"))
                text = res["choices"][0]["message"]["content"]
                usage = res.get("usage", {})
                return LLMReply(text=text, route=route.name, model=route.model, degraded=False, usage=usage)
        except urllib.error.HTTPError as e:
            raise RouteUnavailable(f"API error {e.code}: {e.reason}", "Check API limits or key")
        except (urllib.error.URLError, TimeoutError) as e:
            raise RouteUnavailable(f"Connection failed: {e}", "Check network connection")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise RouteUnavailable(f"Invalid JSON response: {e}", "Check the API endpoint")
