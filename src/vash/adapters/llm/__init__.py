"""The one internal LLM interface (C-03, R10).

Callers use `reply` with a role name. The route, the adapter and the fallback
are read from the freeze. The intake route never uses the pool and never
falls back (rule R2). The other roles fall back once and report degraded=True.
"""
from typing import Any, Mapping
from vash.core.exceptions import RouteUnavailable
from vash.core.interfaces import LLMAdapter, LLMReply, RouteSettings
from vash.core.registry import load_adapter

def route_for(freeze: Any, role: str) -> RouteSettings:
    """Return the RouteSettings for a role."""
    models = freeze.data.get("models", {})
    name = models.get(role)
    if not name:
        raise RouteUnavailable(
            f"No route defined for role '{role}'",
            f"Add models.{role} in project-stack.json"
        )
    routes = freeze.routes
    if name not in routes:
        raise RouteUnavailable(
            f"Route '{name}' for role '{role}' is not defined",
            f"Add models.routes.{name} in project-stack.json"
        )
    return routes[name]

def reply(
    freeze: Any,
    role: str,
    prompt: str,
    adapters: Mapping[str, LLMAdapter] | None = None
) -> LLMReply:
    """Generate a reply for a prompt on the route for the role."""
    route = route_for(freeze, role)

    def _get_adapter(r: RouteSettings) -> LLMAdapter:
        if adapters and r.name in adapters:
            return adapters[r.name]
        return load_adapter("llm", r.adapter, {
            "route": r.name,
            "model": r.model,
            "base_url": r.base_url,
            "key_env": r.key_env,
            "timeout_s": r.timeout_s,
        })  # type: ignore[return-value]

    adapter = _get_adapter(route)

    if role == "intake":
        return adapter.reply(prompt, route)

    try:
        return adapter.reply(prompt, route)
    except RouteUnavailable as e:
        models = freeze.data.get("models", {})
        fallback_name = models.get("fallback")
        if not fallback_name:
            raise e
        routes = freeze.routes
        if fallback_name not in routes:
            raise e
        fallback_route = routes[fallback_name]
        fallback_adapter = _get_adapter(fallback_route)
        try:
            res = fallback_adapter.reply(prompt, fallback_route)
            return LLMReply(
                text=res.text, route=res.route, model=res.model,
                degraded=True, usage=res.usage
            )
        except RouteUnavailable:
            raise e
