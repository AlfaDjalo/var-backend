import numpy as np
import pandas as pd
from typing import Dict, Any, Sequence

from .var_model import VaRModel
from .base import VaRResult
from var_engine.scenarios.scenario import Scenario


class HistSimVaR(VaRModel):
    """
    Historical Simulation (HistSim) VaR model.

    Philosophy:
    - Spot is shocked using historical returns
    - Vol is constant and derived from realised covariance
    - Rate is constant
    - Each scenario is a complete market state
    """

    def __init__(
            self,
            confidence_level: float,
            hist_data_window_days: int = 252,
            rate: float = 0.0,
            ):
        super().__init__(confidence_level)
        self.hist_data_window_days = hist_data_window_days
        self.rate = rate


    def run(self, portfolio, market_data: Dict[str, Any]) -> VaRResult:
        base_scenario = self._create_base_scenario(market_data)
        scenarios = self._create_scenarios(market_data, base_scenario)

        return super().run(portfolio, base_scenario, scenarios)
    

    # -----------------------------------------------------
    # Scenario creation
    # -----------------------------------------------------

    def _create_base_scenario(self, market_data: Dict[str, Any]) -> Scenario:

        spot = market_data["spot"]
        cov = market_data["cov"]

        assets = list(spot.keys())
        
        vols = np.sqrt(np.diag(cov))

        vol_map = {
            a: float(v)
            for a, v in zip(assets, vols)
        }

        return Scenario(
            spot=spot,
            vol=vol_map,
            rate=self.rate,
            dt=0.0,
        )


    def _create_scenarios(self, market_data: Dict[str, Any], base_scenario: Scenario) -> Sequence[Scenario]:

        spots = market_data["spot"]
        returns = market_data["returns"]

        assets = list(spots.keys())
        
        returns = returns[assets]

        scenarios = []

        for _, row in returns.iterrows():
            shocked_spots = {
                a: spots[a] * (1.0 + float(row[a]))
                for a in assets
            }

            scenarios.append(
                Scenario(
                    spot=shocked_spots,
                    vol=base_scenario.vol,     # optional for HistSim
                    rate=self.rate,
                    dt=1/252,
                )
            )

        return scenarios

    def model_metadata(self) -> dict:
        meta = super().model_metadata()
        meta.update(
            {
                "hist_data_window_days": self.hist_data_window_days,
                "vol_assumption": "constant_realised",
                "rate": self.rate,                
                # "pnls": self._pnl_dist
                # "volatility": self._volatility,
            }
        )
        return meta
    
    