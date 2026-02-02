from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Scenario:
    """
    Market scenario snapshot used for full revaluation.

    All values represent absolute market levels at the scenario horizon.
    """
    spot: Mapping[str, float]
    vol: Mapping[str, float]
    rate: float
    dt: float

    def __post_init__(self):
        if self.dt < 0.0:
            raise ValueError("Scenario dt must be non-negative")

        if not self.spot:
            raise ValueError("Scenario spot mapping cannot be empty")
