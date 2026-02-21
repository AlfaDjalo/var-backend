from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ===============================
# Factor Schema
# ===============================

class FactorInputs(BaseModel):
    spot: Optional[Dict[str, float]] = None
    rates: Optional[Dict[str, float]] = None
    vols: Optional[Dict[str, float]] = None


# ===============================
# VaR Request Schemas
# ===============================

class BaseVaRRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    products: Optional[List[Dict[str, Any]]] = None

    confidence_level: float = Field(0.01, gt=0, lt=1)
    estimation_window_days: Optional[int] = Field(252, ge=1)

    asof_date: Optional[str] = Field(
        None, description="End date for data window (YYYY-MM-DD)"
    )

    # ✅ NEW — allow frontend factor overrides
    factors: Optional[FactorInputs] = None


class ParametricRequest(BaseVaRRequest):
    pass


class MonteCarloRequest(BaseVaRRequest):
    n_sims: int = Field(10_000, gt=0)
    random_seed: Optional[int] = None
    vol_of_vol: Optional[float] = None


class HistSimRequest(BaseVaRRequest):
    pass


# ===============================
# VaR Response Schemas
# ===============================

class BaseVaRResponse(BaseModel):
    portfolio_value: float
    var_dollar: float
    var_percent: float
    diagnostics: Optional[Dict[str, Any]] = None


class ParametricResponse(BaseVaRResponse):
    pass


class MonteCarloResponse(BaseVaRResponse):
    pass


class HistSimResponse(BaseVaRResponse):
    pass


class PositionInputType(str, Enum):
    notional = "notional"
    units = "units"
    weights = "weights"
