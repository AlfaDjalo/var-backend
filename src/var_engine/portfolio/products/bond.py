from typing import Optional
from .base import Product

class BondProduct(Product):
    """
    Simple fixed coupon bond product.
    """
    def __init__(
            self,
            product_id: str,
            issuer: str,
            notional: float,
            coupon: float,          # annual coupon rate, e.g. 0.05 for 5%
            maturity: float,        # years to maturity
            frequency: int = 2     # coupon payments per year (default semi-annual)
    ):
        super().__init__(product_id)
        self.issuer = issuer
        self.notional = float(notional)
        self.coupon = float(coupon)
        self.maturity = float(maturity)
        self.frequency = int(frequency)

    def _calculate_present_value(self, discount_rate: float) -> float:
        """
        Calculate present value of the bond cash flows discounted at given rate.

        Args:
            discount_rate: Annual discount rate (continuously compounded or simple assumed here)

        Returns:
            Present value of bond.
        """
        # Number of coupon payments remaining
        n_payments = int(self.maturity * self.frequency)
        coupon_payment = self.notional * self.coupon / self.frequency

        # Discount factor per period assuming simple compounding (can extend to more complex)
        period_rate = discount_rate / self.frequency

        # Present value of coupons (annuity formula)
        if period_rate > 0:
            pv_coupons = coupon_payment * (1 - (1 + period_rate) ** (-n_payments)) / period_rate
            pv_principal = self.notional / (1 + period_rate) ** n_payments
        else:
            # If zero rate, sum coupons directly
            pv_coupons = coupon_payment * n_payments
            pv_principal = self.notional

        return pv_coupons + pv_principal

    def revalue(self, scenario):
        """
        Revalue bond using interest rate from scenario.

        Assumes scenario.rate provides annual discount rate for issuer (or a general rate).

        Args:
            scenario: dict-like or object with 'rate' attribute or dict of rates by issuer

        Returns:
            Updated market value (float)
        """
        try:
            if hasattr(scenario, "rate"):
                if isinstance(scenario.rate, dict):
                    rate = scenario.rate.get(self.issuer, 0.0)
                else:
                    rate = scenario.rate
            else:
                rate = scenario.get("rate", 0.0)

        except Exception:
            rate = 0.0

        return self._calculate_present_value(rate)