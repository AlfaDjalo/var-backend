from typing import Dict
from var_engine.scenarios.scenario import Scenario
from .base import Product

class StockProduct(Product):
    """
    Equity product priced off spot scenarios.
    """

    def __init__(self, product_id: str, ticker: str, quantity: float):
        # market_value = quantity * spot
        super().__init__(product_id)
        # super().__init__(product_id, market_value)

        self.ticker = ticker
        self.quantity = float(quantity)
        # self.initial_spot = float(spot)

    def revalue(self, scenario):
        """
        Revalue stock under a scenario.

        Scenario must contain:
            scenario.spot[product_id] -> new spot price
        """
        try:
            new_spot = scenario.spot[self.ticker]
            # new_spot = scenario.spot[self.product_id]
        except KeyError:
            raise KeyError(f"Scenario missing spot for {self.product_id}")

        return self.quantity * new_spot

    def get_sensitivities(self, scenario: Scenario) -> Dict[str, float]:
        spot = scenario.spot[self.ticker]
        market_value = self.quantity * spot

        return {
            self.ticker: market_value
        }

        return super().get_sensitivities(scenario)

# from .base import Product

# class StockProduct(Product):
#     """
#     Linear equity product.
#     """
#     def revalue(self, scenario):
#         """
#         Scenario is expected to contain a return for this equity.
#         """
#         r = scenario[self.product_id]
#         return self.market_value * (1.0 + r)