from abc import ABC, abstractmethod
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
        # portfolio_value = self.portfolio_value_at_scenario(portfolio, base_scenario)
        # portfolio_value = portfolio.portfolio_value
        if portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive")
        
        pnl = None
        scenario_values = None


        # if isinstance(scenarios, ScenarioSet):
        #     print("Scenarios: ", scenarios)
        # # if scenarios is not None:
        #     scenario_values = pd.Series(
        #         [portfolio.revalue(s) for s in scenarios]
        #     )
        #     # scenario_values = self.revalue_portfolio(portfolio, scenarios)
        #     pnl = scenario_values - portfolio_value

        scenario_values = pd.Series(
            [portfolio.revalue(s) for s in scenarios]
        )
        # scenario_values = self.revalue_portfolio(portfolio, scenarios)
        pnl = scenario_values - portfolio_value
        self._pnls = pnl.tolist()

        # scenario_values = self.revalue_portfolio(portfolio, scenarios)
        # pnl = self._generate_pnl(portfolio, data)
        # pnl: scenario_values - portfolio_value

        print("P&L: ", pnl)
        
        var_dol = self.compute_var(
            # portfolio=portfolio,
            pnl=pnl,
            # scenarios=scenarios
            )
        
        var_pct = var_dol / portfolio_value if portfolio_value != 0 else 0.0

        meta = self.model_metadata()

        return VaRResult(
            portfolio_value=float(portfolio_value),
            var_dollar=float(var_dol),
            var_percent=float(var_pct),
            confidence_level=self.confidence_level,
            volatility=meta.get("volatility"),
            # volatility=self.model_metadata().get("volatility"),
            pnl_distribution=pnl,
            scenario_values=scenario_values,
            metadata=meta,
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
        # return portfolio.revalue(scenarios.scenarios)
    
    # @abstractmethod
    # def compute_var(
    #     self,
    #     # portfolio,
    #     pnl: Optional[pd.Series],
    #     # scenarios: Optional[ScenarioSet]
    # ) -> float:
    #     """
    #     Compute the VaR metric from a P&L distribution.
    #     """
    #     pass


    def compute_var(self, pnl: pd.Series) -> float:
        if pnl is None or pnl.empty:
            raise ValueError("Valid P&L required")

        return float(
            -np.quantile(
                pnl,
                1.0 - self.confidence_level,
            )
        )


    def model_metadata(self) -> dict:
        """
        Optional metadata describing the model.
        Subclasses can extend this.
        """
        return {
            "model": self.__class__.__name__,
            "confidence_level": self.confidence_level
        }
    
    # def portfolio_value_at_scenario(self, portfolio, scenario) -> float:
    #     """
    #     Compute portfolio value at a given scenario.
        
    #     Args:
    #         portfolio: Portfolio instance
    #         scenario: Scenario instance or dict-like market data
        
    #     Returns:
    #         Portfolio value under the scenario
    #     """
    #     return portfolio.revalue(scenario)

    # def _generate_pnl(self, portfolio, data) -> pd.Series:
    #     """
    #     Default P&L generation via full revaluation under scenarios.
    #     Used by Historical / MC models.
    #     """
    #     if not isinstance(data, ScenarioSet):
    #         raise TypeError("Expected ScenarioSet for scenario-based VaR model")
        
    #     scenario_values = portfolio.revalue(data.scenarios)
    #     return scenario_values - portfolio.portfolio_value