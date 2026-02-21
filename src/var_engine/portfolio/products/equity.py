from typing import Dict
from var_engine.scenarios.scenario import Scenario
from .base import Product


class StockProduct(Product):
    """
    Equity product priced off spot scenarios.
    """

    def __init__(self, product_id: str, ticker: str, quantity: float):
        super().__init__(product_id)

        self.ticker = ticker
        self.quantity = float(quantity)

    # ---------------------------------------------------------
    # Revaluation
    # ---------------------------------------------------------

    def revalue(self, scenario: Scenario) -> float:
        """
        Revalue stock under a scenario.
        """
        try:
            new_spot = scenario.spot[self.ticker]
        except KeyError:
            raise KeyError(f"Scenario missing spot for {self.ticker}")

        return self.quantity * new_spot

    # ---------------------------------------------------------
    # Factor Sensitivities (for VaR / attribution)
    # ---------------------------------------------------------

    def get_sensitivities(self, scenario: Scenario) -> Dict[str, float]:
        """
        Return dollar delta exposure for delta-normal VaR.
        """
        spot = scenario.spot[self.ticker]
        market_value = self.quantity * spot

        return {
            f"spot:{self.ticker}": float(market_value)
        }

    # ---------------------------------------------------------
    # Full Dollar Greeks (for Risk page)
    # ---------------------------------------------------------

    def get_dollar_greeks(self, scenario: Scenario) -> Dict[str, float]:
        """
        Full dollar Greeks for equity.

        Equity characteristics:
            Delta = quantity
            Dollar Delta = quantity * spot
            Gamma = 0
            Vega = 0
            Theta = 0
            Rho = 0
        """
        try:
            spot = scenario.spot[self.ticker]
        except KeyError:
            raise KeyError(f"Scenario missing spot for {self.ticker}")

        dollar_delta = self.quantity * spot

        return {
            "dollar_delta": float(dollar_delta),
            "dollar_gamma": 0.0,
            "dollar_vega": 0.0,
            "dollar_theta": 0.0,
            "dollar_rho": 0.0,
        }
