import numpy as np
import pandas as pd
from typing import Callable, Optional

from .var_model import VaRModel
from .base import VaRResult

class MonteCarloVaR(VaRModel):
    """
    Monte Carlo VaR model using multivariate normal simulation.
    """

    def __init__(
            self,
            confidence_level: float,
            parameter_estimation_window_days: int = 252,
            n_sims: int = 10_000,
            random_seed: int = 42,
            cov_estimator: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
            use_mean: bool = True,
            ):
        super().__init__(confidence_level)

        if n_sims <= 0:
            raise ValueError("n_sims must be positive")

        self.parameter_estimation_window_days = parameter_estimation_window_days
        self.n_sims = n_sims
        self.random_seed = random_seed
        self.use_mean = use_mean
        self.cov_estimator = cov_estimator or (lambda r: r.cov())

        self._volatility: Optional[float] = None
        self._returns: Optional[pd.DataFrame] = None
    
    def run(self, portfolio, returns: pd.DataFrame) -> VaRResult:
        self._returns = returns
        return super().run(portfolio)
    
    def compute_var(self, portfolio, pnl=None, scenarios=None) -> float:

        if self._returns is None:
            raise RuntimeError("Returns not set. Call run() first.")

        # historic_data = self._returns
        product_ids = [p.product_id for p in portfolio.products]
        returns = self._returns[product_ids]
        # historic_data = historic_data[product_ids]

        window = returns.tail(self.parameter_estimation_window_days)
        if len(window) < self.parameter_estimation_window_days:
            raise ValueError("Not enough data for historical data window")


        market_values = np.array([p.market_value for p in portfolio.products])
        portfolio_value = portfolio.portfolio_value

        weights = market_values / portfolio_value

        # Estimate parameters
        mu = window.mean().values if self.use_mean else np.zeros(len(product_ids))
        cov = self.cov_estimator(window).values

        L = self._factorize_covariance(cov)

        rng = np.random.default_rng(self.random_seed)
        z = rng.standard_normal(size=(self.n_sims, len(product_ids)))
        simulated_returns = z @ L.T + mu

        portfolio_returns = simulated_returns @ weights
        pnl_series = portfolio_returns * portfolio_value
        
        var_value = -np.quantile(pnl_series, self.confidence_level)

        self._volatility = np.std(pnl_series) / portfolio_value

        return var_value

    def _factorize_covariance(self, cov: np.ndarray) -> np.ndarray:
        """
        Cholesky factorization with eigen fallback.
        """
        try:
            return np.linalg.cholesky(cov)
        except np.linalg.LinAlgError:
            eigvals, eigvecs = np.linalg.eigh(cov)
            if np.any (eigvals < -1e-10):
                raise ValueError("Covariance matrix is not positive semi-definite")
            
            eigvals_clipped = np.clip(eigvals, 0.0, None)
            return eigvecs @ np.diag(np.sqrt(eigvals_clipped))

    def model_metadata(self) -> dict:
        meta = super().model_metadata()
        meta.update(
            {
                "model": "MonteCarloVaR",
                "n_sims": self.n_sims,
                "parameter_estimation_window_days": self.parameter_estimation_window_days,
                "use_mean": self.use_mean,
                "volatility": self._volatility,
                "random_seed": self.random_seed,
            }
        )
        return meta
    
    