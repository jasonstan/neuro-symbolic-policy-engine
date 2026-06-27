"""SyntheticAdapter: loads cases and policies from YAML files (the hero scenario)."""

from importlib import resources
from pathlib import Path

import yaml

from nspk.types import Case, Policy


class SyntheticAdapter:
    @staticmethod
    def load_case(source: str | Path) -> Case:
        with Path(source).open() as f:
            data = yaml.safe_load(f)
        return Case.model_validate(data)

    @staticmethod
    def load_policy(source: str | Path) -> Policy:
        with Path(source).open() as f:
            data = yaml.safe_load(f)
        return Policy.model_validate(data)


def load_bundled_policy(name: str = "wealth_management") -> Policy:
    """Load a policy YAML packaged inside `nspk.policies`."""
    with resources.files("nspk.policies").joinpath(f"{name}.yaml").open() as f:
        data = yaml.safe_load(f)
    return Policy.model_validate(data)
