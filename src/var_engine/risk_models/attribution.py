from dataclasses import dataclass
from typing import Dict


@dataclass
class PositionAttribution:
    position_pnl: Dict[str, float]   # product_id -> pnl
    factor_pnl: Dict[str, float]     # factor -> pnl


@dataclass
class ScenarioAttribution:
    scenario_pnl: float
    positions: Dict[str, float]
    factors: Dict[str, float]
