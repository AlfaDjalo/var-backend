from var_engine.greeks.greeks_engine import GreeksEngine
from var_engine.greeks.curves import (
    FlatInterestRateCurve,
    FlatVolatilitySurface,
)

from var_engine.portfolio.products.equity import StockProduct
from var_engine.portfolio.products.option import OptionProduct
from var_engine.portfolio.products.bond import BondProduct


class GreeksService:
    """
    Service responsible for computing portfolio Greeks.
    Delegates actual calculations to GreeksEngine.
    """

    def __init__(self, portfolio, rate=0.05, vol=0.2):
        self.portfolio = portfolio
        self.ir_curve = FlatInterestRateCurve(rate)
        self.vol_surface = FlatVolatilitySurface(vol)
        self.engine = GreeksEngine(self.ir_curve, self.vol_surface)

    def compute(self):

        results = {
            "positions": [],
            "totals": {
                "delta": 0.0,
                "dollar_delta": 0.0,
                "dv01": 0.0,
            }
        }

        for product in self.portfolio.products:

            # -------------------------------------------------
            # STOCK
            # -------------------------------------------------
            if isinstance(product, StockProduct):

                delta = self.engine.equity_delta(
                    product.spot,
                    product.quantity
                )

                dollar_delta = self.engine.equity_dollar_delta(
                    product.spot,
                    product.quantity
                )

                results["positions"].append({
                    "id": product.product_id,
                    "type": "stock",
                    "delta": delta,
                    "dollar_delta": dollar_delta
                })

                results["totals"]["delta"] += delta
                results["totals"]["dollar_delta"] += dollar_delta

            # -------------------------------------------------
            # OPTION
            # -------------------------------------------------
            elif isinstance(product, OptionProduct):

                delta = self.engine.option_delta(product)

                dollar_delta = delta * product.spot * product.quantity

                results["positions"].append({
                    "id": product.product_id,
                    "type": "equity_option",
                    "delta": delta,
                    "dollar_delta": dollar_delta
                })

                results["totals"]["delta"] += delta
                results["totals"]["dollar_delta"] += dollar_delta

            # -------------------------------------------------
            # BOND
            # -------------------------------------------------
            elif isinstance(product, BondProduct):

                dv01 = self.engine.bond_dv01(product)

                bucketed = self.engine.bond_bucketed_dv01(
                    product,
                    buckets=[1, 2, 5, 10]
                )

                results["positions"].append({
                    "id": product.product_id,
                    "type": "bond",
                    "dv01": dv01,
                    "bucketed_dv01": bucketed
                })

                results["totals"]["dv01"] += dv01

            # -------------------------------------------------
            # UNKNOWN PRODUCT
            # -------------------------------------------------
            else:
                raise TypeError(
                    f"Unsupported product class: {type(product).__name__}"
                )

        return results
