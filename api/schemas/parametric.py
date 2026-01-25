from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field

class ParametricRequest(BaseModel):
    dataset_name: str = Field(..., description="Dataset file name to use")
    positions: Optional[Dict[str, float]] = Field(None, description="Optional asset positions keyed by ticker")
    confidence_level: Optional[float] = Field(0.01, gt=0, lt=1, description="Confidence level for VaR")
    cov_window_days: Optional[int] = Field(252, ge=1, description="Window length for covariance estimation")

class ParametricResponse(BaseModel):
    portfolio_value: float
    var_absolute: float
    var_percent: float
    volatility_percent: float
    correlation_matrix: Optional[List[List[float]]] = None
    diagnostics: Optional[Dict[str, Any]] = None