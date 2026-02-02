from typing import List, Dict, Any #,Optional
import numpy as np

from var_engine.portfolio.product_factory import ProductFactory
from var_engine.portfolio.products.base import Product

# from .products.equity import StockProduct

class Portfolio:
    """
    Portfolio of heterogeneous products.

    Products are instantiated internally via the ProductFactory, which
    allows flexible handling of multiple product types and pricing models.

    Parameters
    ----------
    products: List of Product instances
    """
    def __init__(self, products: List):
        self.products = list(products)

        if not self.products:
            raise ValueError("Portfolio must contain at least one product")

    @classmethod
    def from_raw_products(cls, raw_products: List[Dict[str, Any]]):
        """
        Factory method to create Portfolio from raw product dicts.

        Args:
            raw_products: List of dicts with product data, each must include a "type" key.

        Returns:
            Portfolio instance with fully constructed Product objects.
        """
        products = [
            ProductFactory.create_product(raw)
            for raw in raw_products            
        ]
        return cls(products)        

    # @property
    # def portfolio_value(self) -> float:
    #     """Total market value of all products."""
    #     return sum(p.market_value for p in self.products)

    @property
    def product_ids(self) -> List[str]:
        """
        Ordered list of product IDs.
        This ordering is the contract used by risk models.
        """
        return [p.product_id for p in self.products]        

    # @property
    # def market_values(self) -> np.ndarray:
    #     """
    #     Ordered vector of market values aligned with product_ids.
    #     """
    #     return np.array([p.market_value for p in self.products], dtype=float)        

    def revalue(self, scenario):
        """
        Full revaluation of the portfolio under a given scenario.

        Args:
            scenario: dict-like or Scenario instance with market data.

        Returns:
            Total revalued portfolio value.
        """
        return sum(p.revalue(scenario) for p in self.products)

    def pnl(self, scenario, base_scenario) -> float:
        """
        Scenario P&L relative to current value.

        Args:
            scenario: dict-like or Scenario instance.
            base_scenario: dict-like or Scenario instance.

        Returns:
            Portfolio profit or loss under the scenario.
        """
        # print("P&L: ", self.revalue(scenario) - self.revalue(base_scenario))
        return self.revalue(scenario) - self.revalue(base_scenario)


    def get_sensitivities(self, scenario):
        """
        Collect sensitivities from each product, for parametric VaR or other analyses.

        Returns:
            List of sensitivities arrays/dicts aligned with products,
            or None if sensitivities not implemented for a product.
        """
        sensitivities = []
        for product in self.products:
            if hasattr(product, "sensitivities") and callable(product.sensitivities):
                sensitivities.append(product.sensitivities(scenario))
            else:
                sensitivities.append(None)
            return sensitivities   