from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# VaR Request Schemas
class BaseVaRRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    products: Optional[List[Dict[str, Any]]] = None
    # products: Optional[Dict[str, float]] = None 
    # positions: Optional[Dict[str, float]] = None
    confidence_level: float = Field(0.01, gt=0, lt=1)
    estimation_window_days: int = Field(252, ge=1)
    # position_input_type: PositionInputType = Field(
    #     PositionInputType.notional,
    #     description="How position values should be interpreted"
    # )
    asof_date: Optional[str] = Field(
        None, description="End date for data window (YYYY-MM-DD)"
    )

class ParametricRequest(BaseVaRRequest):
    # cov_window_days: int = Field(252, ge=1)
    pass

class MonteCarloRequest(BaseVaRRequest):
    # parameter_estimation_window_days: int = Field(252, ge=1)
    n_sims: int = Field(10_000, gt=0)
    random_seed: Optional[int] = None
    vol_of_vol: Optional[float] = None


class HistSimRequest(BaseVaRRequest):
    # hist_data_window_days: int = Field(252, ge=1)
    pass

# VaR Response Schemas
class BaseVaRResponse(BaseModel):
    portfolio_value: float
    var_dollar: float
    var_percent: float
    diagnostics: Optional[Dict[str, Any]] = None    

class ParametricResponse(BaseVaRResponse):
    # volatility_percent: float
    # correlation_matrix: Optional[List[List[float]]] = None
    pass

class MonteCarloResponse(BaseVaRResponse):
    pass


class HistSimResponse(BaseVaRResponse):
    pass


class PositionInputType(str, Enum):
    notional = "notional"
    units = "units"
    weights = "weights"
