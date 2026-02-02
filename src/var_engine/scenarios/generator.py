from abc import ABC, abstractmethod
from typing import Sequence, Optional
import numpy as np

from var_engine.scenarios.scenario import Scenario


class ScenarioGenerator(ABC):
    """
    Abstract base class for all market scenario generators.

    A ScenarioGenerator produces full market scenarios at a fixed
    future horizon. It is model-aware but portfolio-agnostic.
    """

    def __init__(self, horizon: float, seed: Optional[int] = None):
        """
        Parameters
        ----------
        horizon : float
            Time horizon of each scenario (in years).
        seed : Optional[int]
            Random seed for reproducibility.
        """
        if horizon <= 0.0:
            raise ValueError("Scenario horizon must be positive")

        self.horizon = horizon
        self._rng = np.random.default_rng(seed)

    @property
    def rng(self) -> np.random.Generator:
        """
        Random number generator used by this scenario generator.
        """
        return self._rng

    @abstractmethod
    def generate(self, n: int) -> Sequence[Scenario]:
        """
        Generate n independent market scenarios.

        Parameters
        ----------
        n : int
            Number of scenarios to generate.

        Returns
        -------
        Sequence[Scenario]
            Generated market scenarios.
        """
        if n <= 0:
            raise ValueError("Number of scenarios must be positive")

        raise NotImplementedError

    def reset_rng(self, seed: Optional[int] = None) -> None:
        """
        Reset the random number generator.

        Parameters
        ----------
        seed : Optional[int]
            New seed to use.
        """
        self._rng = np.random.default_rng(seed)
