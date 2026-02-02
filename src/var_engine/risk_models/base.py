from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import pandas as pd

@dataclass
class VaRResult:
    """
    Standardised output for a VaR calculation.
    """
    portfolio_value: float
    var_dollar: float
    var_percent: float
    confidence_level: float

    # Optional / method-specific outputs
    volatility: Optional[float] = None
    pnl_distribution: Optional[pd.Series] = None
    scenario_values: Optional[pd.Series] = None
    metadata: Optional[dict] = None


class ScenarioSet:
    """
    Container for scenario data used in revaluation.
    This can hold returns, rates, vols, or any other risk factors.
    """
    def __init__(self, scenarios: pd.DataFrame):
        """
        Args:
            scenarios: DataFrame indexed by scenario id or date.
                        Columns depend on product requirements.
        """
        self.scenarios = scenarios

    def __len__(self):
        return len(self.scenarios)
    
    