import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict, Any, Callable, Optional

from .var_model import VaRModel
from .base import VaRResult
# from var_engine.portfolio.portfolio import Portfolio
from var_engine.scenarios.scenario import Scenario



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
            n_points: int = 10001,
            ):
        super().__init__(confidence_level)
        self.cov_window_days = cov_window_days
        self.cov_estimator = cov_estimator or (lambda r: r.cov())
        self.n_points = n_points

    def run(self, portfolio, market_data: Dict[str, Any]) -> VaRResult:

        base_scenario = self._create_base_scenario(market_data)
        portfolio_value = portfolio.revalue(base_scenario)

        # print("Base scenario: ", base_scenario)

        exposures = portfolio.get_sensitivities(base_scenario)
        # print("Exposures: ", exposures)
        w = pd.Series(exposures)

        returns = market_data["returns"]
        cov = returns.cov().loc[w.index, w.index]

        port_var = w.T @ cov @ w
        port_vol = np.sqrt(port_var)
        correlation = self._correlation_from_cov(cov)
        # self._volatility = port_vol
        # self._correlation = self._correlation_from_cov(cov)

        z = norm.ppf(self.confidence_level)
        VaR = -z * port_vol
        var_dol = VaR
        var_pct = VaR / portfolio_value

        # --- Deterministic P&L distribution ---
        pnl_dist = self._build_pnl_distribution(port_vol)
        # self._pnl_dist = self._build_pnl_distribution(port_vol)

        # meta = self.model_metadata()
        meta = {
            **super().model_metadata(),
            "cov_window_days": self.cov_window_days,
            "volatility": port_vol,
            "correlation_matrix": correlation,
            "pnls": pnl_dist 
        }

        diagnostics_core = self._compute_diagnostics(
            pnl=pd.Series(pnl_dist),
            scenario_values=pd.Series(pnl_dist),  # or scenario_values if available
            var=var_dol,
            es=var_dol,  # ES not trivial here — use VaR as proxy or compute exact
        )

        diagnostics_combined = {
            "metadata": meta,
            **diagnostics_core,
        }

        return VaRResult(
            portfolio_value=float(portfolio_value),
            var_dollar=float(var_dol),
            var_percent=float(var_pct),
            confidence_level=self.confidence_level,
            # volatility=meta.get("volatility"),
            # volatility=self.model_metadata().get("volatility"),
            # pnl_distribution=pnl_dist,
            # scenario_values=scenario_values,
            metadata=diagnostics_combined,
            # metadata=self.model_metadata()
        )

        # self._returns = returns
        # return super().run(portfolio)

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

    def _build_pnl_distribution(self, port_vol: float):

        probs = np.linspace(0.001, 0.999, self.n_points)
        z = norm.ppf(probs)

        return pd.Series(z * port_vol).tolist()


        # z = np.linspace(-4, 4, self.n_points)

        # pnl = z * port_vol
        # pdf = norm.pdf(z)

        # return {
        #     "z": z.tolist(),
        #     "pnl": pnl.tolist(),
        #     "pdf": pdf.tolist(),
        # }

    # def model_metadata(self) -> dict:
    #     meta = super().model_metadata()
    #     meta.update(
    #         {
    #             "cov_window_days": self.cov_window_days,
    #             "volatility": self._volatility,
    #             "correlation_matrix": self._correlation,
    #             "pnls": self._pnl_dist,                
    #         }
    #     )
    #     return meta
    
    @staticmethod
    def _correlation_from_cov(cov: pd.DataFrame):
        std = np.sqrt(np.diag(cov.values))
        if np.any(std == 0):
            raise ValueError("Zero-variance asset detected")
        return (cov.values / np.outer(std, std)).tolist()
    
    