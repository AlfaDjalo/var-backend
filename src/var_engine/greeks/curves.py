from dataclasses import dataclass
import numpy as np


# -------------------------
# Interest Rate Curves
# -------------------------

class InterestRateCurve:
    def get_rate(self, maturity: float) -> float:
        raise NotImplementedError


@dataclass
class FlatInterestRateCurve(InterestRateCurve):
    rate: float

    def get_rate(self, maturity: float) -> float:
        return self.rate


@dataclass
class PiecewiseInterestRateCurve(InterestRateCurve):
    tenors: list[float]
    rates: list[float]

    def get_rate(self, maturity: float) -> float:
        return float(np.interp(maturity, self.tenors, self.rates))


# -------------------------
# Volatility Curves
# -------------------------

class VolatilitySurface:
    def get_vol(self, maturity: float, strike: float) -> float:
        raise NotImplementedError


@dataclass
class FlatVolatilitySurface(VolatilitySurface):
    vol: float

    def get_vol(self, maturity: float, strike: float) -> float:
        return self.vol
