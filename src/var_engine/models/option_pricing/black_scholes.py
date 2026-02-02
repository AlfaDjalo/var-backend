import math
from scipy.stats import norm

from var_engine.models.option_pricing.base import OptionPricingModel

class BlackScholesModel(OptionPricingModel):
    """
    Black-Scholes pricing model for European options.
    """
    def price(
            self,
            spot: float,
            strike: float,
            maturity: float,
            vol: float,
            rate: float,
            option_type: str
    ) -> float:
        
        if maturity <= 0.0:
            if option_type == "call":
                return max(spot - strike, 0.0)
            elif option_type == "put":
                return max(strike - spot, 0.0)
            else:
                raise ValueError("option_type must be 'call' or 'put'")

        if vol <= 0.0:
            forward = spot * math.exp(rate * maturity)
            if option_type == "call":
                return math.exp(-rate * maturity) * max(forward - strike, 0.0)
            elif option_type == "put":
                return math.exp(-rate * maturity) * max(strike - forward, 0.0)
            else:
                raise ValueError("option_type must be 'call' or 'put'")

        sqrt_t = math.sqrt(maturity)

        d1 = (
            math.log(spot / strike) + (rate + 0.5 * vol ** 2) * maturity
        ) / (vol * sqrt_t)
        
        d2 = d1 - vol * sqrt_t

        if option_type == "call":
            price = (
                spot * norm.cdf(d1)
                - strike * math.exp(-rate * maturity) * norm.cdf(d2)
            )
        elif option_type == "put":
            price = (
                strike * math.exp(-rate * maturity) * norm.cdf(-d2)
                - spot * norm.cdf(-d1)
            )
        else:
            raise ValueError("option_type must be 'call' or 'put'")
        
        return float(price)