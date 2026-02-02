import numpy as np
import pandas as pd
# from scipy.stats import norm
from typing import Dict, Any, Sequence
# from typing import Callable, Optional

from .var_model import VaRModel
from .base import VaRResult
# from .var_model import VaRModel, VaRResult
from var_engine.scenarios.scenario import Scenario

class HistSimVaR(VaRModel):
    """
    Historical Simulation(HistSim) VaR model.
    """

    def __init__(
            self,
            confidence_level: float,
            hist_data_window_days: int = 252,
            ):
        super().__init__(confidence_level)
        self.hist_data_window_days = hist_data_window_days

    def run(self, portfolio, market_data: Dict[str, Any]) -> VaRResult:
    # def run(self, portfolio, scenarios: pd.DataFrame) -> VaRResult:
        scenarios = self._create_scenarios(market_data)
        base_scenario = self._create_base_scenario(market_data)

        print("Base scenario: ", base_scenario)
        # return super().run(portfolio)
        return super().run(portfolio, base_scenario, scenarios)
    
    # def compute_var(self, portfolio, pnl=None, scenarios=None) -> float:

    #     returns = self._scenarios
    #     product_ids = [p.product_id for p in portfolio.products]
    #     returns = returns[product_ids]

    #     returns_window = returns.tail(self.hist_data_window_days)
    #     if len(returns_window) < self.hist_data_window_days:
    #         raise ValueError("Not enough data for historical data window")

    #     market_values = np.array([p.market_value for p in portfolio.products])
    #     portfolio_value = portfolio.portfolio_value

    #     portfolio_returns = returns_window @ (market_values / portfolio_value)

    #     pnl_series = portfolio_returns * portfolio_value
        
    #     var_value = -pnl_series.quantile(self.confidence_level)

    #     self._volatility = pnl_series.std() / portfolio_value

    #     return var_value


    def _create_scenarios(self, market_data: Dict[str, Any]) -> Sequence[Scenario]:

        spots = market_data["spot"]
        returns = market_data["returns"]

        assets = list(spots.keys())
        returns = returns[assets]

        scenarios = []

        for _, row in returns.iterrows():
            shocked_spots = {
                a: spots[a] * (1.0 + row[a])
                for a in assets
            }

            scenarios.append(
                Scenario(
                    spot=shocked_spots,
                    vol={},     # optional for HistSim
                    rate=0.0,
                    dt=1/252,
                )
            )

        return scenarios



    def _create_base_scenario(self, market_data: Dict[str, Any]) -> Scenario:

        spot = market_data["spot"]
        cov = market_data["cov"]

        vols = np.sqrt(np.diag(cov))
        assets = list(spot.keys())

        return Scenario(
            spot=spot,
            vol={a: float(v) for a, v in zip(assets, vols)},
            rate=0.0,
            dt=0.0,
        )

    def model_metadata(self) -> dict:
        meta = super().model_metadata()
        meta.update(
            {
                "hist_data_window_days": self.hist_data_window_days,
                # "volatility": self._volatility,
            }
        )
        return meta
    
    