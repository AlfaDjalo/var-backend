import numpy as np
import pandas as pd
from typing import Dict, Any, Sequence, Optional

from .var_model import VaRModel
from .base import VaRResult
from var_engine.scenarios.gbm import GBMScenarioGenerator
from var_engine.scenarios.scenario import Scenario

class MonteCarloVaR(VaRModel):
    """
    Monte Carlo VaR model using multivariate normal simulation.
    """

    def __init__(
            self,
            confidence_level: float,
            # parameter_estimation_window_days: int = 252,
            n_sims: int = 10_000,
            random_seed: int = 42,
            horizon: float = 1.0 / 252,
            # cov_estimator: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
            use_mean: bool = True,
            generator = GBMScenarioGenerator
            ):
        super().__init__(confidence_level)

        if n_sims <= 0:
            raise ValueError("n_sims must be positive")

        # self.parameter_estimation_window_days = parameter_estimation_window_days
        self.n_sims = n_sims
        self.random_seed = random_seed
        self.horizon = horizon

        self.use_mean = use_mean
        # self.cov_estimator = cov_estimator or (lambda r: r.cov())
        self.generator = generator

        self._volatility: Optional[float] = None
        # self._scenarios = None
        # self._pnl = None
    

    def run(self, portfolio, market_data: Dict[str, Any]) -> VaRResult:
        """
        Run Monte Carlo VaR using full revaluation under scenarios.
        """    
        scenarios = self._create_scenarios(market_data)

        base_scenario = self._create_base_scenario(market_data)

        return super().run(portfolio, base_scenario, scenarios)
    
    def _create_scenarios(self, market_data: Dict[str, Any]) -> Sequence[Scenario]:

        print(np.sqrt(np.diag(market_data["cov"])))

         # Create scenario generator
        generator = self.generator(
            spot=market_data["spot"],
            # vols=vols,
            # corr=corr,
            cov = market_data["cov"] * 252,
            horizon=self.horizon, #1.0/252,  # 1 day horizon
            seed=self.random_seed #None #request.random_seed
        )

        return generator.generate(n=self.n_sims)
    
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

    def compute_es(self, pnl: pd.Series) -> float:
        q = np.quantile(pnl, 1 - self.confidence_level)
        tail = pnl[pnl <= q]
        return -tail.mean()

    # def _factorize_covariance(self, cov: np.ndarray) -> np.ndarray:
    #     """
    #     Cholesky factorization with eigen fallback.
    #     """
    #     try:
    #         return np.linalg.cholesky(cov)
    #     except np.linalg.LinAlgError:
    #         eigvals, eigvecs = np.linalg.eigh(cov)
    #         if np.any (eigvals < -1e-10):
    #             raise ValueError("Covariance matrix is not positive semi-definite")
            
    #         eigvals_clipped = np.clip(eigvals, 0.0, None)
    #         return eigvecs @ np.diag(np.sqrt(eigvals_clipped))

    def model_metadata(self) -> dict:
        meta = super().model_metadata()
        meta.update(
            {
                "model": "MonteCarloVaR",
                "n_sims": self.n_sims,
                # "parameter_estimation_window_days": self.parameter_estimation_window_days,
                "use_mean": self.use_mean,
                "volatility": self._volatility,
                "random_seed": self.random_seed,
                "pnls": self._pnls
            }
        )
        return meta
    
    