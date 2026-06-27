"""Adapter seam: the engine consumes an abstract `Case`; environments plug in here.

A `CaseAdapter` knows how to construct a `Case` from some source (YAML file, captured episode,
event stream, ...). The synthetic adapter loads from YAML files in the hero scenario. Future
seams — e.g. the EnterpriseOps-Gym "real-data track" — implement this Protocol. See ADR-0003.
"""

from typing import Any, Protocol

from nspk.types import Case


class CaseAdapter(Protocol):
    def load_case(self, source: Any) -> Case: ...
