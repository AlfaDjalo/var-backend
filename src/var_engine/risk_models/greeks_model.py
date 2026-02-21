import numpy as np
from typing import Dict, Any
from var_engine.scenarios.scenario import Scenario


class GreeksService:

    def __init__(self, portfolio, rate: float = 0.0):
        self.portfolio = portfolio
        self.rate = float(rate)

    def compute(self, market_data: Dict[str, Any]):

        if "spot" not in market_data:
            raise ValueError("Market data missing 'spot'")

        if "cov" not in market_data:
            raise ValueError("Market data missing 'cov'")

        spot = market_data["spot"]
        cov = market_data["cov"]

        assets = list(spot.keys())

        # ---------------------------------
        # Realised vols from covariance
        # ---------------------------------
        vols = np.sqrt(np.diag(cov))

        vol_map = {
            asset: float(vol)
            for asset, vol in zip(assets, vols)
        }

        # ---------------------------------
        # Base scenario
        # ---------------------------------
        base_scenario = Scenario(
            spot=spot,
            vol=vol_map,
            rate=self.rate,
            dt=0.0
        )

        # ---------------------------------
        # Delegate to Portfolio
        # ---------------------------------

        position_greeks = self.portfolio.get_position_greeks(base_scenario)
        portfolio_greeks = self.portfolio.get_portfolio_greeks(base_scenario)
        factor_exposures = self.portfolio.get_factor_exposures(base_scenario)

        return {
            "positions": position_greeks,
            "totals": portfolio_greeks,
            "factor_exposures": factor_exposures,
            "metadata": {
                "vol_source": "realised_from_covariance",
                "rate": self.rate,
                "n_positions": len(self.portfolio.products)
            }
        }
