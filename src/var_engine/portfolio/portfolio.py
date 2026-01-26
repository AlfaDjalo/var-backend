from typing import Optional
import pandas as pd
import numpy as np

# from .products.equity import StockProduct

class Portfolio:
    """
    Portfolio of heterogenous products.
    """
    def __init__(self, products):
        self.products = List = list(products)

        if not self.products:
            raise ValueError("Portfolio must contain at least one product")

    @property
    def portfolio_value(self) -> float:
        return sum(p.market_value for p in self.products)

    @property
    def product_ids(self):
        """
        Ordered product identifiers.
        This ordering is the contract used by risk models.
        """
        return [p.product_id for p in self.products]        

    @property
    def market_values(self):
        """
        Ordered vector of market values aligned with product_ids.
        """
        return np.array([p.market_value for p in self.products], dtype=float)        

    def revalue(self, scenario):
        """
        Full revaluation of the portfolio under a single scenario.
        """
        return sum(p.revalue(scenario) for p in self.products)

    def pnl(self, scenario):
        """
        Scenario P&L relative to current value.
        """
        return self.revalue(scenario) - self.portfolio_value
    