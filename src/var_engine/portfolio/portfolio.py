from typing import List, Dict, Any #,Optional
from collections import defaultdict
import numpy as np

from var_engine.portfolio.product_factory import ProductFactory
# from var_engine.portfolio.products.base import Product

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
        return self.revalue(scenario) - self.revalue(base_scenario)


    def get_sensitivities(self, scenario) -> Dict[str, float]:
        """
        Collect sensitivities from each product, for parametric VaR or other analyses.

        Returns:
            List of sensitivities arrays/dicts aligned with products,
            or None if sensitivities not implemented for a product.
        """
        total = defaultdict(float)

        # sensitivities = []
        for product in self.products:
            sens = product.get_sensitivities(scenario)

            for factor, value in sens.items():
                total[factor] += value

        return dict(total)

    def attribute_scenario(
            self,
            scenario,
            base_scenario,
            method: str = "GBA",
    ) -> Dict[str, Any]:
        """
        Attribute P&L for a scenario.

        method:
            "greeks" (current)
            "reval" (future extension)
        """        
        if method != "GBA":
            raise NotImplementedError("Only GBA implemented")
        
        factor_moves = self._factor_moves(scenario, base_scenario)

        portfolio_factor_totals = defaultdict(float)
        position_results = {}

        for product in self.products:
            sens = product.get_sensitivities(base_scenario)

            factor_pnls = {}
            total_pnl = 0.0

            for factor, sensitivity in sens.items():
                move = factor_moves.get(factor, 0.0)
                pnl = sensitivity * move
                
                if pnl == 0.0:
                    continue
                factor_pnls[factor] = pnl
                total_pnl += pnl
                portfolio_factor_totals[factor] += pnl

            position_results[product.product_id] = {
                "factors": dict(factor_pnls),
                "total": float(total_pnl),
            }

        portfolio_total = sum(portfolio_factor_totals.values())

        return {
            "positions": position_results,
            "portfolio": {
                "factors": dict(portfolio_factor_totals),
                "total": float(portfolio_total),
            },
        }
    
    def _factor_moves(self, scenario, base_scenario) -> Dict[str, float]:
        """
        Convert scenario vs base into factor moves.

        Requires Scenario to expose:
            spot, vol, rate
        """

        moves = {}

        for asset, s in scenario.spot.items():
            base = base_scenario.spot.get(asset)
            if base is None:
                continue
            moves[f"spot:{asset}"] = s - base

        for asset, v in scenario.vol.items():
            base = base_scenario.vol.get(asset)
            if base is None:
                continue
            moves[f"vol:{asset}"] = v - base

        moves["rate"] = scenario.rate - base_scenario.rate

        return moves

    def get_position_greeks(self, scenario):
        """
        Return per-position dollar Greeks.

        Returns:
            List[dict]
        """
        positions = []

        for product in self.products:

            if hasattr(product, "get_dollar_greeks"):
                greeks = product.get_dollar_greeks(scenario)
            else:
                # Fallback to sensitivities if full Greeks not implemented
                sens = product.get_sensitivities(scenario)
                greeks = {
                    "dollar_delta": sum(v for k, v in sens.items() if k.startswith("spot")),
                    "dollar_gamma": 0.0,
                    "dollar_vega": 0.0,
                    "dollar_theta": 0.0,
                    "dollar_rho": sum(v for k, v in sens.items() if "rate" in k),
                }

            positions.append({
                "product_id": product.product_id,
                "product_type": product.__class__.__name__,
                "greeks": greeks
            })

        return positions

    def get_portfolio_greeks(self, scenario):
        """
        Aggregate total portfolio dollar Greeks.
        """
        totals = {
            "dollar_delta": 0.0,
            "dollar_gamma": 0.0,
            "dollar_vega": 0.0,
            "dollar_theta": 0.0,
            "dollar_rho": 0.0,
        }

        for product in self.products:
            if hasattr(product, "get_dollar_greeks"):
                g = product.get_dollar_greeks(scenario)
            else:
                continue

            for k in totals:
                totals[k] += g.get(k, 0.0)

        return totals

    def get_factor_exposures(self, scenario):
        """
        Aggregate factor exposures across products.
        """
        totals = defaultdict(float)

        for product in self.products:
            sens = product.get_sensitivities(scenario)

            for factor, value in sens.items():
                totals[factor] += value

        return dict(totals)
