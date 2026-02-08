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
    
    def greeks(
            self,
            spot: float,
            strike: float,
            maturity: float,
            vol: float,
            rate: float,
            option_type: str,
    ):
        """
        Return Black–Scholes Greeks for European options.
        """

        option_type = option_type.lower()

        if maturity <= 0 or vol <= 0:
            return {
                "delta": 0.0,
                "gamma": 0.0,
                "vega": 0.0,
                "theta": 0.0,
                "rho": 0.0,                
            }
        
        sqrt_t = math.sqrt(maturity)

        d1 = (math.log(spot / strike) + (rate + 0.5 * vol**2) * maturity) / (vol * sqrt_t)

        d2 = d1 - vol * sqrt_t

        pdf_d1 = norm.pdf(d1)
        
        # --- DELTA ---
        if option_type == "call":
            delta = norm.cdf(d1)
        elif option_type == "put":
            delta = norm.cdf(d1) - 1
        else:
            raise ValueError("option_type must be 'call' or 'put'")
        
        # --- GAMMA ---
        gamma = pdf_d1 / (spot * vol * sqrt_t)

        # --- VEGA ---
        vega = spot * pdf_d1 * sqrt_t

        # --- THETA ---
        first_term = -(spot * pdf_d1 * vol) / (2 * sqrt_t)

        if option_type == "call":
            theta = (first_term - rate * strike * math.exp(-rate * maturity) * norm.cdf(d2))
        else:
            theta = (first_term + rate * strike * math.exp(-rate * maturity) * norm.cdf(-d2))

        # --- RHO ---
        if option_type == "call":
            rho = (strike * maturity * math.exp(-rate * maturity) * norm.cdf(d2))
        else:
            rho = (-strike * maturity * math.exp(-rate * maturity) * norm.cdf(-d2))

        return {
            "delta": float(delta),
            "gamma": float(gamma),
            "vega": float(vega),
            "theta": float(theta),
            "rho": float(rho),                
        }
