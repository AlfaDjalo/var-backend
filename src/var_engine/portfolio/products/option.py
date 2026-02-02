from typing import Dict
from var_engine.portfolio.products.base import Product
from var_engine.scenarios.scenario import Scenario
from var_engine.models.option_pricing.base import OptionPricingModel


class OptionProduct(Product):
    """
    Vanilla European option priced off spot/vol/rate scenarios.
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
        # initial_spot: float,
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
        initial_spot : float
            Spot used to compute initial market value.
        """
        self.underlying_ticker = underlying_ticker
        self.strike = float(strike)
        self.maturity = float(maturity)
        self.option_type = option_type.lower()
        self.quantity = float(quantity)
        self.pricing_model = pricing_model

        if self.option_type not in {"call", "put"}:
            raise ValueError("option_type must be 'call' or 'put'")

        # Compute initial market value
        # initial_price = pricing_model.price(
        #     spot=initial_spot,
        #     strike=self.strike,
        #     maturity=self.maturity,
        #     vol=pricing_model.initial_vol,
        #     rate=pricing_model.initial_rate,
        #     option_type=self.option_type,
        # )

        super().__init__(product_id)
        # super().__init__(product_id, self.quantity * initial_price)

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
        spot = scenario.spot[self.underlying_ticker]
        vol = scenario.vol[self.underlying_ticker]

        greeks = self.pricing_model.greeks(
            spot=spot,
            strike=self.strike,
            maturity=self.maturity,
            vol=vol,
            rate=scenario.rate,
            option_type=self.option_type
        )

        delta = greeks["delta"]

        exposure = delta * spot * self.quantity
        
        return {
            self.underlying_ticker: exposure
        }