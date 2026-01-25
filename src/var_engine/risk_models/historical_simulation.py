import numpy as np
import pandas as pd
# from scipy.stats import norm
from typing import Callable, Optional

from .var_model import VaRModel
from .base import VaRResult
# from .var_model import VaRModel, VaRResult

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

    def run(self, portfolio, returns: pd.DataFrame) -> VaRResult:
        self._returns = returns
        return super().run(portfolio)
    
    def compute_var(self, portfolio, pnl=None, scenarios=None) -> float:

        returns = self._returns
        product_ids = [p.product_id for p in portfolio.products]
        returns = returns[product_ids]

        returns_window = returns.tail(self.hist_data_window_days)
        if len(returns_window) < self.hist_data_window_days:
            raise ValueError("Not enough data for historical data window")

        market_values = np.array([p.market_value for p in portfolio.products])
        portfolio_value = portfolio.portfolio_value

        portfolio_returns = returns_window @ (market_values / portfolio_value)

        pnl_series = portfolio_returns * portfolio_value
        
        var_value = -pnl_series.quantile(self.confidence_level)

        self._volatility = pnl_series.std() / portfolio_value

        return var_value


    def model_metadata(self) -> dict:
        meta = super().model_metadata()
        meta.update(
            {
                "hist_data_window_days": self.hist_data_window_days,
                "volatility": self._volatility,
            }
        )
        return meta
    
    