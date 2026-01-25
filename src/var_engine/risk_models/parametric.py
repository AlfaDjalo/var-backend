import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Callable, Optional

from .var_model import VaRModel
from .base import VaRResult
# from .var_model import VaRModel, VaRResult

class ParametricVaR(VaRModel):
    """
    Variance-covariance (parametric) VaR model.
    Assumes joint normality of returns.
    """

    def __init__(
            self,
            confidence_level: float,
            cov_window_days: int = 252,
            cov_estimator: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
            ):
        super().__init__(confidence_level)
        self.cov_window_days = cov_window_days
        self.cov_estimator = cov_estimator or (lambda r: r.cov())

        # self._portfolio_vol = None
        # self._correlation = None

    def run(self, portfolio, returns: pd.DataFrame) -> VaRResult:
        self._returns = returns
        return super().run(portfolio)

    def compute_var(self, portfolio, pnl=None, scenarios=None) -> float:
        returns = self._returns

        product_ids = [p.product_id for p in portfolio.products]
        returns = returns[product_ids]

        returns_window = returns.tail(self.cov_window_days)
        if len(returns_window) < self.cov_window_days:
            raise ValueError("Not enough data for covariance window")

        cov = self.cov_estimator(returns_window)

        market_values = np.array([p.market_value for p in portfolio.products])
        portfolio_value = portfolio.portfolio_value

        port_var = market_values.T @ cov.values @ market_values
        port_vol = np.sqrt(port_var)

        z = norm.ppf(self.confidence_level)

        self._volatility = port_vol / portfolio_value
        self._correlation = self._correlation_from_cov(cov)

        return -z * port_vol

    # def compute_var(
    #     self,
    #     portfolio,
    #     pnl=None,
    #     scenarios=None
    # ) -> float:
    #     """
    #     Closed-form VaR calculation.
    #     """
    #     returns = portfolio.returns[portfolio.product_ids]
    #     returns_window = returns.tail(self.cov_window_days)

    #     if len(returns_window) < self.cov_window_days:
    #         raise ValueError(
    #             f"Not enough data for covariance window ({self.cov_window_days})"
    #         )

    #     cov = self.cov_estimator(returns_window)

    #     market_values = portfolio.market_values
    #     portfolio_value = portfolio.portfolio_value

    #     # Portfolio variance in currency units
    #     port_var = market_values.T @ cov.values @ market_values
    #     port_vol = np.sqrt(port_var)

    #     z = norm.ppf(self.confidence_level)
    #     self._volatility = port_vol / portfolio_value
    #     self._correlation = self._correlation_from_cov(cov)

    #     return -z * port_vol

    # def _generate_pnl(self, portfolio, returns: pd.DataFrame) -> pd.Series:
    # # def run(self, portfolio, scenarios=None) -> VaRResult:
    #     """
    #     Analytically generate a P&L distribution assuming normal returns.
    #     """
    #     returns = returns[portfolio.product_ids]
    #     # returns = portfolio.returns

    #     returns_window = returns.tail(self.cov_window_days)
    #     if len(returns_window) < self.cov_window_days:
    #         raise ValueError(
    #             f"Not enough data for covariance window ({self.cov_window_days})"
    #         )
        
    #     cov_matrix = self.cov_estimator(returns_window)

    #     market_values = portfolio.market_values
    #     # market_values = portfolio.market_values.values
    #     portfolio_value = portfolio.portfolio_value

    #     if portfolio_value <= 0:
    #         raise ValueError("Portfolio value must be positive")

    #     # Portfolio variance in currency units
    #     port_var = market_values.T @ cov_matrix.values @ market_values
    #     port_vol = np.sqrt(port_var)

    #     self._portfolio_vol = port_vol
    #     self._correlation = self._correlation_from_cov(cov_matrix)

    #     # Generate synthetic normal P&L distribution
    #     z = norm.ppf(np.linspace(0.001, 0.999, 1000))
    #     pnl = -z * port_vol

    #     return pd.Series(pnl)
    
    # def compute_var(self, pnl: pd.Series) -> float:
    #     """
    #     VaR is the quantile of the P&L distribution.
    #     """
    #     return -pnl.quantile(1 - self.confidence_level)

    def model_metadata(self) -> dict:
        meta = super().model_metadata()
        meta.update(
            {
                "cov_window_days": self.cov_window_days,
                "volatility": self._volatility,
                "correlation_matrix": self._correlation,
            }
        )
        return meta
    
        # # Parametric VaR
        # z = norm.ppf(self.confidence_level)
        # var_abs = -z * port_vol
        # var_pct = var_abs / portfolio_value

        # # Optional diagnostics
        # vol_pct = port_vol / portfolio_value
        # corr_matrix = self._correlation_from_cov(cov_matrix)

        # return VaRResult(
        #     portfolio_value=portfolio_value,
        #     var_absolute=float(var_abs),
        #     var_percent=float(var_pct),
        #     confidence_level=self.confidence_level,
        #     volatility=float(vol_pct),
        #     metadata={
        #         "model": "ParametricVaR",
        #         "cov_window_days": self.cov_window_days,
        #         "correlation_matrix": corr_matrix,
        #     },
        # )
    
    # def run(self, portfolio, returns: pd.DataFrame) -> VaRResult:
    # # def run(self, portfolio, scenarios=None) -> VaRResult:
    #     """
    #     Override base run(): parametric VaR does not rely on scenarios.
    #     """
    #     returns = returns[portfolio.product_ids]
    #     # returns = portfolio.returns

    #     returns_window = returns.tail(self.cov_window_days)
    #     if len(returns_window) < self.cov_window_days:
    #         raise ValueError(
    #             f"Not enough data for covariance window ({self.cov_window_days})"
    #         )
        
    #     cov_matrix = self.cov_estimator(returns_window)

    #     market_values = portfolio.market_values
    #     portfolio_value = portfolio.portfolio_value

    #     if portfolio_value <= 0:
    #         raise ValueError("Portfolio value must be positive")

    #     # Portfolio variance in currency units
    #     port_var = market_values.T @ cov_matrix.values @ market_values
    #     port_vol = np.sqrt(port_var)

    #     # Parametric VaR
    #     z = norm.ppf(self.confidence_level)
    #     var_abs = -z * port_vol
    #     var_pct = var_abs / portfolio_value

    #     # Optional diagnostics
    #     vol_pct = port_vol / portfolio_value
    #     corr_matrix = self._correlation_from_cov(cov_matrix)

    #     return VaRResult(
    #         portfolio_value=portfolio_value,
    #         var_absolute=float(var_abs),
    #         var_percent=float(var_pct),
    #         confidence_level=self.confidence_level,
    #         volatility=float(vol_pct),
    #         metadata={
    #             "model": "ParametricVaR",
    #             "cov_window_days": self.cov_window_days,
    #             "correlation_matrix": corr_matrix,
    #         },
    #     )
    
    @staticmethod
    def _correlation_from_cov(cov: pd.DataFrame):
        std = np.sqrt(np.diag(cov.values))
        if np.any(std == 0):
            raise ValueError("Zero-variance asset detected")
        return (cov.values / np.outer(std, std)).tolist()
    
    