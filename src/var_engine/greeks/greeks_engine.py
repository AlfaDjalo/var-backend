import numpy as np


class GreeksEngine:

    def __init__(self, ir_curve, vol_surface):
        self.ir_curve = ir_curve
        self.vol_surface = vol_surface

    # -------------------------
    # Equity Delta (simple)
    # -------------------------

    def equity_delta(self, spot: float, quantity: float):
        return quantity

    def equity_dollar_delta(self, spot: float, quantity: float):
        return quantity * spot

    # -------------------------
    # Bond DV01 (finite diff)
    # -------------------------

    def bond_price(self, bond, rate):
        """
        Simple fixed-rate bond pricer
        """
        price = 0.0
        for t, cf in zip(bond.cashflow_times, bond.cashflows):
            price += cf * np.exp(-rate * t)
        return price

    def bond_dv01(self, bond):
        """
        Parallel bump DV01
        """
        bump = 0.0001

        base_rate = self.ir_curve.get_rate(0)
        bumped_rate = base_rate + bump

        base_price = self.bond_price(bond, base_rate)
        bumped_price = self.bond_price(bond, bumped_rate)

        dv01 = bumped_price - base_price

        return dv01

    # -------------------------
    # Bucketed DV01
    # -------------------------

    def bond_bucketed_dv01(self, bond, buckets):
        """
        Buckets = list of tenor points e.g. [1,2,5,10]
        """
        bump = 0.0001
        bucket_results = {}

        for bucket in buckets:
            base_rate = self.ir_curve.get_rate(bucket)

            bumped_curve = lambda m: (
                base_rate + bump if abs(m - bucket) < 1e-8 else self.ir_curve.get_rate(m)
            )

            base_price = 0.0
            bumped_price = 0.0

            for t, cf in zip(bond.cashflow_times, bond.cashflows):
                base_price += cf * np.exp(-self.ir_curve.get_rate(t) * t)

                r = bumped_curve(t)
                bumped_price += cf * np.exp(-r * t)

            bucket_results[bucket] = bumped_price - base_price

        return bucket_results
