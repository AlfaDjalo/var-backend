from typing import Dict
from var_engine.portfolio.products.base import Product
from var_engine.scenarios.scenario import Scenario
from var_engine.models.option_pricing.base import OptionPricingModel


class OptionProduct(Product):
    """
    Vanilla European option priced off spot/vol/rate scenarios.
    Produces dollar sensitivities.
    """

    def __init__(
        self,
        product_id: str,
        underlying_ticker: str,
        strike: float,
        maturity: float,           # in years
        option_type: str,          # "call" or "put"
        quantity: float,
        pricing_model: OptionPricingModel,
    ):
        """
        Parameters
        ----------
        product_id : str
            Unique identifier for the option.
        underlying_id : str
            Product ID of the underlying asset.
        strike : float
            Option strike.
        maturity : float
            Time to maturity in years.
        option_type : str
            "call" or "put".
        quantity : float
            Number of option contracts.
        pricing_model : OptionPricingModel
            Pricing model used for valuation.
        """
        self.underlying_ticker = underlying_ticker
        self.strike = float(strike)
        self.maturity = float(maturity)
        self.option_type = option_type.lower()
        self.quantity = float(quantity)
        self.pricing_model = pricing_model

        if self.option_type not in {"call", "put"}:
            raise ValueError("option_type must be 'call' or 'put'")

        super().__init__(product_id)

    def revalue(self, scenario: Scenario) -> float:
        """
        Revalue option under a market scenario.
        """
        try:
            spot = scenario.spot[self.underlying_ticker]
            vol = scenario.vol[self.underlying_ticker]
        except KeyError as e:
            raise KeyError(f"Scenario missing data for {self.underlying_ticker}") from e

        remaining_maturity = max(self.maturity - scenario.dt, 0.0)

        price = self.pricing_model.price(
            spot=spot,
            strike=self.strike,
            maturity=remaining_maturity,
            vol=vol,
            rate=scenario.rate,
            option_type=self.option_type,
        )

        return self.quantity * price


    def get_sensitivities(self, scenario: Scenario) -> Dict[str, float]:
        """
        Return $-delta exposure for delta-normal VaR.

        Exposure = delta * spot * quantity
        """
        try:
            spot = scenario.spot[self.underlying_ticker]
            vol = scenario.vol[self.underlying_ticker]
        except KeyError as e:
            raise KeyError(f"Scenario missing data for {self.underlying_ticker}") from e
        remaining_maturity = max(self.maturity - scenario.dt, 0.0)

        greeks = self.pricing_model.greeks(
            spot=spot,
            strike=self.strike,
            maturity=remaining_maturity,
            vol=vol,
            rate=scenario.rate,
            option_type=self.option_type
        )

        unit_delta = greeks["delta"]
        dollar_delta = unit_delta * spot * self.quantity

        # exposure = delta * spot * self.quantity
        
        return {
            # f"spot:{self.underlying_ticker}": greeks["delta"] * spot * self.quantity,
            f"spot:{self.underlying_ticker}": float(dollar_delta),
            f"vol:{self.underlying_ticker}": greeks["vega"] * self.quantity,
            "rate": greeks["rho"] * self.quantity,
        }


        # return {
        #     f"spot:{self.underlying_ticker}": float(dollar_delta)
        # }
    
    # ---------------------------------------------------------
    # Optional: full $ Greeks (future use)
    # ---------------------------------------------------------
    def get_dollar_greeks(self, scenario: Scenario) -> Dict[str, float]:
        """
        Full dollar Greeks for advanced risk models.
        Not required for delta-normal VaR.
        """

        spot = scenario.spot[self.underlying_ticker]
        vol = scenario.vol[self.underlying_ticker]

        remaining_maturity = max(self.maturity - scenario.dt, 0.0)

        g = self.pricing_model.greeks(
            spot=spot,
            strike=self.strike,
            maturity=remaining_maturity,
            vol=vol,
            rate=scenario.rate,
            option_type=self.option_type,
        )

        return {
            "dollar_delta": g["delta"] * spot * self.quantity,
            "dollar_gamma": g["gamma"] * (spot ** 2) * self.quantity,
            "dollar_vega": g["vega"] * self.quantity,
            "dollar_theta": g["theta"] * self.quantity,
            "dollar_rho": g["rho"] * self.quantity,
        }    