"""Fake cloud adapter for tests."""
from typing import Any, Mapping
from vash.core.interfaces import CloudAdapter, CloudPlan
from vash.core.exceptions import FreezeInvalid

class FakeCloud(CloudAdapter):
    def __init__(self, settings: Mapping[str, Any]):
        super().__init__(settings)
        self.applied: dict[str, bool] = {}

    def plan(self, environment: str) -> CloudPlan:
        return CloudPlan(environment=environment, summary="fake plan", changes=1)

    def apply(self, environment: str, approved: bool) -> dict[str, Any]:
        if not approved:
            raise FreezeInvalid("Requires approval", "Set approved=True")
        self.applied[environment] = True
        return {"ip": "1.2.3.4"}

    def destroy(self, environment: str, approved: bool) -> None:
        if not approved:
            raise FreezeInvalid("Requires approval", "Set approved=True")
        self.applied[environment] = False

    def outputs(self, environment: str) -> dict[str, Any]:
        return {"ip": "1.2.3.4"}
