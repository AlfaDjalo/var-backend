from typing import Dict
from var_engine.scenarios.scenario import Scenario
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
        coupon: float,
        maturity: float,
        frequency: int = 2,
    ):
        super().__init__(product_id)

        self.issuer = issuer
        self.notional = float(notional)
        self.coupon = float(coupon)
        self.maturity = float(maturity)
        self.frequency = int(frequency)

    # ---------------------------------------------------------
    # Internal PV calculation
    # ---------------------------------------------------------

    def _calculate_present_value(self, discount_rate: float) -> float:
        n_payments = int(self.maturity * self.frequency)
        coupon_payment = self.notional * self.coupon / self.frequency

        period_rate = discount_rate / self.frequency

        if period_rate > 0:
            pv_coupons = coupon_payment * (
                1 - (1 + period_rate) ** (-n_payments)
            ) / period_rate
            pv_principal = self.notional / (1 + period_rate) ** n_payments
        else:
            pv_coupons = coupon_payment * n_payments
            pv_principal = self.notional

        return pv_coupons + pv_principal

    # ---------------------------------------------------------
    # Revaluation
    # ---------------------------------------------------------

    def revalue(self, scenario: Scenario) -> float:
        try:
            if isinstance(scenario.rate, dict):
                rate = scenario.rate.get(self.issuer, 0.0)
            else:
                rate = scenario.rate
        except Exception:
            rate = 0.0

        return self._calculate_present_value(rate)

    # ---------------------------------------------------------
    # Factor Sensitivities (DV01-style)
    # ---------------------------------------------------------

    def get_sensitivities(self, scenario: Scenario) -> Dict[str, float]:
        """
        Return rate sensitivity (dollar change per 1bp).
        """
        try:
            if isinstance(scenario.rate, dict):
                rate = scenario.rate.get(self.issuer, 0.0)
            else:
                rate = scenario.rate
        except Exception:
            rate = 0.0

        base_pv = self._calculate_present_value(rate)
        bump_pv = self._calculate_present_value(rate + 0.0001)

        # DV01 (change per 1bp)
        dv01 = (bump_pv - base_pv) / 0.0001

        return {
            f"rate:{self.issuer}": float(dv01)
        }

    # ---------------------------------------------------------
    # Full Dollar Greeks
    # ---------------------------------------------------------

    def get_dollar_greeks(self, scenario: Scenario) -> Dict[str, float]:
        """
        Bond risk profile approximated as:

            Delta = 0
            Gamma = 0
            Vega = 0
            Theta = 0
            Rho = rate sensitivity

        Rho = dollar change per 1 unit rate change
        """

        try:
            if isinstance(scenario.rate, dict):
                rate = scenario.rate.get(self.issuer, 0.0)
            else:
                rate = scenario.rate
        except Exception:
            rate = 0.0

        base_pv = self._calculate_present_value(rate)
        bump_pv = self._calculate_present_value(rate + 0.0001)

        # Sensitivity per unit rate (not per bp)
        rho = (bump_pv - base_pv) / 0.0001

        return {
            "dollar_delta": 0.0,
            "dollar_gamma": 0.0,
            "dollar_vega": 0.0,
            "dollar_theta": 0.0,
            "dollar_rho": float(rho),
        }
