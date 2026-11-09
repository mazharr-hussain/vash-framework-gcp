"""Freeze file loading and validation (C-05)."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Any

import jsonschema

from vash.core.paths import vash_root
from vash.core.interfaces import RouteSettings
from vash.core.exceptions import FreezeFileMissing, FreezeInvalid


ROLE_FIELDS = ("intake", "coder", "critic", "fallback")


@dataclass(frozen=True)
class Freeze:
    """A loaded project-stack.json freeze."""
    path: Path
    data: Mapping[str, Any]

    @property
    def pack(self) -> tuple[str, str]:
        stack = self.data.get("stack", {})
        return (stack.get("pack", ""), stack.get("pack_version", ""))

    @property
    def forge(self) -> tuple[str, dict]:
        f = self.data.get("forge", {})
        return (f.get("choice", ""), f.get("settings", {}))

    @property
    def ci(self) -> tuple[str, dict]:
        c = self.data.get("ci", {})
        return (c.get("choice", ""), c.get("settings", {}))

    @property
    def cloud(self) -> tuple[str, dict]:
        c = self.data.get("cloud", {})
        return (c.get("choice", "none"), c.get("settings", {}))

    @property
    def routes(self) -> dict[str, RouteSettings]:
        raw = self.data.get("models", {}).get("routes", {})
        return {
            name: RouteSettings(
                name=name,
                adapter=r["adapter"],
                model=r["model"],
                vendor=r["vendor"],
                base_url=r.get("base_url"),
                key_env=r.get("key_env"),
                timeout_s=r["timeout_s"],
            )
            for name, r in raw.items()
        }

    @property
    def thresholds(self) -> dict[str, int]:
        return self.data.get("thresholds", {})

    @property
    def delivery(self) -> tuple[str, int | None]:
        """Delivery mode and iteration length; phased when the freeze has no delivery block."""
        d = self.data.get("delivery", {})
        return (d.get("mode", "phased"), d.get("iteration_days"))

    @property
    def floor(self) -> int:
        return self.data.get("floor", 88)

    @property
    def allowed_write(self) -> tuple[str, ...]:
        return tuple(self.data.get("paths", {}).get("allowed_write", []))

    @property
    def decisions(self) -> tuple[str, ...]:
        return tuple(self.data.get("decisions", []))

    @property
    def owner_exception(self) -> str | None:
        return self.data.get("owner_exception")


def _load_json(fp: Path) -> Any:
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise FreezeInvalid(f"Invalid JSON in {fp}: {e}", "Fix JSON syntax") from e


def _validate_schema(data: Any, schema_path: Path, label: str) -> None:
    if not schema_path.exists():
        raise FreezeInvalid(
            f"Schema not found: {schema_path}",
            "Set VASH_HOME to the VASH checkout"
        )
    schema = _load_json(schema_path)
    try:
        jsonschema.Draft202012Validator(schema).validate(data)
    except jsonschema.ValidationError as e:
        path = ".".join(str(p) for p in e.absolute_path)
        raise FreezeInvalid(
            f"{label} schema failed at {path}: {e.message}",
            "Fix the field"
        ) from e


def load_freeze(repo_root: Path) -> Freeze:
    """Load and validate project-stack.json."""
    fp = repo_root / "project-stack.json"
    if not fp.exists():
        raise FreezeFileMissing(f"Missing {fp}", "Create project-stack.json")
    data = _load_json(fp)

    schema_path = vash_root() / "method" / "schemas" / "project-stack.schema.json"
    _validate_schema(data, schema_path, "project-stack")

    models = data.get("models", {})
    routes = models.get("routes", {})

    for role in ROLE_FIELDS:
        if role in models:
            name = models[role]
            if name not in routes:
                raise FreezeInvalid(
                    f"models.{role} names an undefined route '{name}'",
                    "Add the route to models.routes or fix the name"
                )

    coder = routes.get(models.get("coder", ""), {})
    critic = routes.get(models.get("critic", ""), {})
    owner_exc = data.get("owner_exception")
    if coder and critic and owner_exc != "OD-1":
        if coder.get("vendor") == critic.get("vendor"):
            raise FreezeInvalid(
                "Critic vendor must differ from Coder vendor (unless owner_exception=OD-1)",
                "Change critic route or set owner_exception"
            )

    floor = data.get("floor", 88)
    for name, val in data.get("thresholds", {}).items():
        if isinstance(val, int) and val < floor:
            raise FreezeInvalid(
                f"Threshold '{name}'={val} is below floor {floor}",
                f"Raise to at least {floor}"
            )

    return Freeze(path=fp, data=data)


def load_stack_pack(repo_root: Path, pack_name: str) -> dict:
    """Load and validate a stack pack manifest."""
    fp = repo_root / "catalog" / "stacks" / pack_name / "stack.json"
    if not fp.exists():
        fp = vash_root() / "catalog" / "stacks" / pack_name / "stack.json"
    if not fp.exists():
        raise FreezeFileMissing(f"Missing {fp}", "Create stack.json")
    data = _load_json(fp)
    schema_path = vash_root() / "method" / "schemas" / "stack-pack.schema.json"
    _validate_schema(data, schema_path, "stack-pack")
    return data
