from typing import Dict, Sequence, Optional
import numpy as np

from var_engine.scenarios.scenario import Scenario
from var_engine.scenarios.generator import ScenarioGenerator


class GBMScenarioGenerator(ScenarioGenerator):
    """
    Multivariate Geometric Brownian Motion scenario generator.

    Produces terminal market scenarios at a fixed horizon using
    correlated GBM dynamics with constant volatility.
    """

    def __init__(
        self,
        spot: Dict[str, float],
        # vols: Dict[str, float],
        # corr: np.ndarray,
        cov: np.ndarray,
        horizon: float,
        drifts: Optional[Dict[str, float]] = None,
        seed: Optional[int] = None,
        vol_of_vol: Optional[float] = None,
    ):
        """
        Parameters
        ----------
        spots : dict[str, float]
            Current spot levels per risk factor.
        vols : dict[str, float]
            Volatilities per risk factor.
        corr : np.ndarray
            Correlation matrix between risk factors.
        cov : np.ndarray
            Covariance matrix between risk factors.
        horizon : float
            Time horizon in years.
        drifts : Optional[dict[str, float]]
            Drift per risk factor. Defaults to zero.
        seed : Optional[int]
            RNG seed.
        vol_of_vol : Optional[float]
            Default annualised vol of vol.
        """
        super().__init__(horizon=horizon, seed=seed)

        self.assets = list(spot.keys())

        # if set(vols.keys()) != set(self.assets):
        #     raise ValueError("Spots and vols must have identical keys")

        if drifts is not None and set(drifts.keys()) != set(self.assets):
            raise ValueError("Drifts must have identical keys to spots")

        self.spot = np.array([spot[a] for a in self.assets], dtype=float)
        self.vols = np.sqrt(np.diag(cov))

        self.drifts = (
            np.array([drifts[a] for a in self.assets], dtype=float)
            if drifts is not None
            else np.zeros(len(self.assets))
        )

        self._validate_inputs(cov)

        # Cholesky factor for covariance
        self._chol = np.linalg.cholesky(cov)

        self.vol_of_vol = vol_of_vol


    def _validate_inputs(self, cov: np.ndarray) -> None:
    # def _validate_inputs(self, corr: np.ndarray) -> None:
        n = len(self.assets)

        if cov.shape != (n, n):
        # if corr.shape != (n, n):
            raise ValueError("Covariance matrix has incorrect shape")
            # raise ValueError("Correlation matrix has incorrect shape")

        if not np.allclose(cov, cov.T):
            raise ValueError("Covariance must be symmetric")
        
        if np.any(np.diag(cov) < 0):
            raise ValueError("Covariance diagonal must be non-negative")


    def generate(self, n: int) -> Sequence[Scenario]:
        """
        Generate n independent GBM market scenarios.
        """
        dim = len(self.assets)
        sqrt_t = np.sqrt(self.horizon)

        # Independent standard normals
        z = self.rng.standard_normal(size=(n, dim))

        # Correlated shocks
        z_corr = z @ self._chol.T

        diffusion = sqrt_t * z_corr
        drift_term = (self.drifts - 0.5 * self.vols ** 2) * self.horizon
        # diffusion = self.vols * sqrt_t * z_corr

        spot_t = self.spot * np.exp(drift_term + diffusion)

        vol_t = self._simulate_vols(n)

        scenarios = []

        for i in range(n):
            scenarios.append(
                Scenario(
                    spot={
                        asset: float(spot_t[i, j])
                        for j, asset in enumerate(self.assets)
                    },
                    vol={
                        asset: float(vol_t[i, j])
                        # asset: float(self.vols[j])
                        for j, asset in enumerate(self.assets)
                    },
                    rate=0.0,
                    dt=self.horizon,
                )
            )

        return scenarios


    def _simulate_vols(self, n: int):
        """
        Generate n independent GBM vol scenarios.
        """
        if self.vol_of_vol is None:
            return np.tile(self.vols, (n, 1))

        sqrt_t = np.sqrt(self.horizon)

        z = self.rng.standard_normal((n, len(self.assets)))

        eta = self.vol_of_vol

        drift = -0.5 * eta**2 * self.horizon
        diffusion = eta * sqrt_t * z

        vol_t = self.vols * np.exp(drift + diffusion)

        return vol_t