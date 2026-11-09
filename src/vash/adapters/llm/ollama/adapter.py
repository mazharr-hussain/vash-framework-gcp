"""Local Ollama HTTP API adapter."""
import json
import os
import urllib.request
import urllib.error
from typing import Any, Mapping
from vash.core.interfaces import LLMAdapter, LLMReply, RouteSettings
from vash.core.exceptions import RouteUnavailable

class Adapter(LLMAdapter):
    """Ollama LLM adapter."""
    def __init__(self, settings: Mapping[str, Any]):
        super().__init__(settings)

    def reply(self, prompt: str, route: RouteSettings) -> LLMReply:
        base_url = route.base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        url = f"{base_url.rstrip('/')}/api/generate"
        data = {
            "model": route.model,
            "prompt": prompt,
            "stream": False
        }
        req = urllib.request.Request(
            url, data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=route.timeout_s) as response:
                res = json.loads(response.read().decode("utf-8"))
                text = res.get("response", "")
                usage = {}
                if "prompt_eval_count" in res:
                    usage["prompt_tokens"] = res["prompt_eval_count"]
                if "eval_count" in res:
                    usage["completion_tokens"] = res["eval_count"]
                return LLMReply(text=text, route=route.name, model=route.model, degraded=False, usage=usage)
        except urllib.error.HTTPError as e:
            raise RouteUnavailable(f"Ollama error {e.code}: {e.reason}", "Check Ollama logs")
        except (urllib.error.URLError, TimeoutError) as e:
            raise RouteUnavailable(f"Ollama connection failed: {e}", "Ensure Ollama is running")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise RouteUnavailable(f"Invalid JSON from Ollama: {e}", "Check Ollama version")
