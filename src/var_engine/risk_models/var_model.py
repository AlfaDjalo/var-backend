from abc import ABC
from typing import Optional, Sequence
import pandas as pd
import numpy as np

from .base import VaRResult, ScenarioSet
from var_engine.scenarios.scenario import Scenario

class VaRModel(ABC):
    """
    Abstract base class for VaR risk models.

    A VaRModel:
    - Accepts a Portfolio and a ScenarioSet
    - Values the portfolio under scenarios
    - Computes VaR from the resulting P&L distribution    
    """

    def __init__(self, confidence_level: float):
        if not 0 < confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        self.confidence_level = confidence_level

    def run(self, portfolio, base_scenario: ScenarioSet = None, scenarios: Optional[Sequence[ScenarioSet]] = None) -> VaRResult:
    # def run(self, portfolio, scenarios: ScenarioSet) -> VaRResult:
        """
        High-entry point for VaR calculation.
        This flow should remain consistent across all VaR models.
        """
        portfolio_value = portfolio.revalue(base_scenario)

        if portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive")
        
        # pnl = None
        # scenario_values = None

        scenario_values = pd.Series(
            [portfolio.revalue(s) for s in scenarios]
        )
        # print("scenario_values: ", scenario_values)
        # scenario_values = self.revalue_portfolio(portfolio, scenarios)
        pnl = scenario_values - portfolio_value        
        self._pnl_dist = pnl.tolist()
        # self._pnls = pnl.tolist()

        # scenario_values = self.revalue_portfolio(portfolio, scenarios)
        # pnl = self._generate_pnl(portfolio, data)
        # pnl: scenario_values - portfolio_value

        # print("P&L: ", pnl)
        
        var_dol = self.compute_var(pnl=pnl)
        es = self.compute_es(pnl)
        
        var_pct = var_dol / portfolio_value if portfolio_value != 0 else 0.0

        diagnostics_core = self._compute_diagnostics(
            pnl=pnl,
            scenario_values=scenario_values.tolist(),
            var=var_dol,
            es=es,
        )

        meta = self.model_metadata()

        diagnostics = {
            "metadata": meta,
            **diagnostics_core,
        }
        # meta.update(diagnostics)

        return VaRResult(
            portfolio_value=float(portfolio_value),
            var_dollar=float(var_dol),
            var_percent=float(var_pct),
            confidence_level=self.confidence_level,
            # volatility=meta.get("volatility"),
            # volatility=self.model_metadata().get("volatility"),
            # pnl_distribution=pnl,
            # scenario_values=scenario_values,
            metadata=diagnostics,
            # metadata=self.model_metadata()
        )
    
    def revalue_portfolio(self, portfolio, scenarios: ScenarioSet) -> pd.Series:
        """
        Default full revaluation logic using the portfolio.
        Subclasses may override if needed.
        """
        return scenarios.scenarios.apply(
            lambda row: portfolio.revalue(row),
            axis=1
        )
    
    def compute_var(self, pnl: pd.Series) -> float:
        if pnl is None or pnl.empty:
            raise ValueError("Valid P&L required")

        q = np.quantile(pnl, self.confidence_level)
        return float(-q)
    
        # return float(
        #     -np.quantile(
        #         pnl,
        #         self.confidence_level,
        #     )
        # )


    def compute_es(self, pnl: pd.Series) -> float:
        if pnl is None or pnl.empty:
            raise ValueError("Valid P&L required")

        q = np.quantile(pnl, self.confidence_level)
        tail = pnl[pnl <= q]
        return float(-tail.mean())


    def _compute_diagnostics(
            self,
            pnl: pd.Series,
            scenario_values: pd.Series,
            var: float,
            es: float,
    ) -> dict:
        
        mean = float(pnl.mean())
        std = float(pnl.std(ddof=1))

        skew = float(pnl.skew())
        kurt = float(pnl.kurtosis())

        return {
            "distribution": {
                "mean": mean,
                "std": std,
                "skew": skew,
                "kurtosis": kurt,
                "min": float(pnl.min()),
                "max": float(pnl.max()),
            },
            "tail": {
                "var": float(var),
                "es": float(es),
            },
            "scenarios": {
                "n": int(len(pnl)),
            },
            "pnls": pnl.to_list()

        }


    def model_metadata(self) -> dict:
        """
        Optional metadata describing the model.
        Subclasses can extend this.
        """
        return {
            "model": self.__class__.__name__,
            # "confidence_level": self.confidence_level
        }