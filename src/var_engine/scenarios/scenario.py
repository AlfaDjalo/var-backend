from dataclasses import dataclass, field
from typing import Mapping, Optional, Any
import uuid

@dataclass(frozen=True)
class Scenario:
    """
    Market scenario snapshot used for full revaluation.

    All values represent absolute market levels at the scenario horizon.

    Attributes
    ----------
    id
        Unique identifier for drilldowns and attribution.
        Auto-generated if not provided.

    label
        Optional human-readable label
        (e.g. date string, "MC_1042", "Stress_2008").

    metadata
        Optional free-form metadata for diagnostics.
        (e.g. percentile, source, regime tag).
    """

    spot: Mapping[str, float]
    vol: Mapping[str, float]
    rate: float
    dt: float
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: Optional[str] = None
    metadata: Optional[Mapping[str, Any]] = None

    def __post_init__(self):
        if self.dt < 0.0:
            raise ValueError("Scenario dt must be non-negative")

        if not self.spot:
            raise ValueError("Scenario spot mapping cannot be empty")

        if not self.vol:
            raise ValueError("Scenario vol mapping cannot be empty")
        
        if not isinstance(self.id, str):
            raise ValueError("Scenario id must be a string")
        
    def with_label(self, label: str) -> "Scenario":
        """Return a copy with a new label."""
        return Scenario(
            spot=self.spot,
            vol=self.vol,
            rate=self.rate,
            dt=self.dt,
            id=self.id,
            label=label,
            metadata=self.metadata,
        )

    def with_metadata(self, metadata: Mapping[str, Any]) -> "Scenario":
        """Return a copy with metadata."""
        return Scenario(
            spot=self.spot,
            vol=self.vol,
            rate=self.rate,
            dt=self.dt,
            id=self.id,
            label=self.label,
            metadata=metadata,
        )        