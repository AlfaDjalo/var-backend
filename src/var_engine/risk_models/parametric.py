import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict, Any, Callable, Optional

from .var_model import VaRModel
from .base import VaRResult
from var_engine.scenarios.scenario import Scenario


class ParametricVaR(VaRModel):
    """
    Variance-covariance (parametric) VaR model.
    Handles multiple factor types: spot, vol, DV01, etc.
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

        # --- Build base scenario for portfolio revaluation ---
        base_scenario = self._create_base_scenario(market_data)
        portfolio_value = portfolio.revalue(base_scenario)

        # --- Get sensitivities (factor exposures) ---
        exposures = portfolio.get_sensitivities(base_scenario)
        if not exposures:
            raise ValueError("Portfolio sensitivities are empty")
        w = pd.Series(exposures)

        # --- Build factor returns DataFrame ---
        returns_df = self._build_factor_returns(market_data, w.index)

        # --- Covariance matrix over factor window ---
        cov_matrix = self.cov_estimator(returns_df.tail(self.cov_window_days))

        # --- Portfolio variance and volatility ---
        port_var = w.T @ cov_matrix @ w
        port_vol = np.sqrt(port_var)

        # --- Correlation matrix for metadata ---
        correlation = self._correlation_from_cov(cov_matrix)

        # --- Compute VaR ---
        z = norm.ppf(self.confidence_level)
        VaR = -z * port_vol
        var_dol = VaR
        var_pct = VaR / portfolio_value

        # --- P&L distribution ---
        pnl_dist = self._build_pnl_distribution(port_vol)

        meta = {
            **super().model_metadata(),
            "cov_window_days": self.cov_window_days,
            "volatility": port_vol,
            "correlation_matrix": correlation,
            "pnls": pnl_dist,
        }

        diagnostics_core = self._compute_diagnostics(
            pnl=pd.Series(pnl_dist),
            var=var_dol,
            es=var_dol,  # ES proxy for now
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
            metadata=diagnostics_combined,
        )

    def _build_factor_returns(self, market_data: Dict[str, Any], factor_keys):
        """
        Align historical returns DataFrame to factor exposures.

        factor_keys: list of factor names like "spot:GOOG", "vol:AAPL", "rate"

        Returns:
            pd.DataFrame with columns matching factor_keys
        """
        returns_df = market_data["returns"].copy()

        # Map factor_keys to underlying columns in returns_df
        factor_map = {}
        for f in factor_keys:
            if f.startswith("spot:"):
                asset = f.split(":")[1]
                factor_map[f] = asset
            elif f.startswith("vol:"):
                asset = f.split(":")[1]
                factor_map[f] = f"vol:{asset}"  # optional, if your returns DF has vol series
            elif f.startswith("rate"):
                factor_map[f] = "rate"
            else:
                factor_map[f] = f  # fallback

        # Subset and rename to factor_keys
        df = pd.DataFrame()
        for fk, col in factor_map.items():
            if col not in returns_df.columns:
                # Fill missing factors with 0 returns
                df[fk] = 0.0
            else:
                df[fk] = returns_df[col]

        return df

    def _create_base_scenario(self, market_data: Dict[str, Any]) -> Scenario:
        """
        Build base scenario from market data.
        Currently supports spot and vol; rate defaults to 0.0
        """
        spot = market_data.get("spot", {})
        cov = market_data.get("cov", np.array([]))

        vols = np.sqrt(np.diag(cov)) if cov.size else {a: 0.2 for a in spot.keys()}
        assets = list(spot.keys())

        return Scenario(
            spot=spot,
            vol={a: float(v) for a, v in zip(assets, vols)},
            rate=market_data.get("rate", 0.0),
            dt=0.0,
        )

    def _build_pnl_distribution(self, port_vol: float):
        probs = np.linspace(0.001, 0.999, self.n_points)
        z = norm.ppf(probs)
        return pd.Series(z * port_vol).tolist()

    @staticmethod
    def _correlation_from_cov(cov: pd.DataFrame):
        std = np.sqrt(np.diag(cov.values))
        std[std == 0] = 1.0  # avoid division by zero
        return (cov.values / np.outer(std, std)).tolist()
