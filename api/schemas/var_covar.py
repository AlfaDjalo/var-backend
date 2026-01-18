from typing import Optional, Dict
from pydantic import BaseModel, Field

class VarCovarRequest(BaseModel):
    dataset_name: str = Field(..., description="Dataset file name to use")
    positions: Optional[Dict[str, float]] = Field(None, description="Optional asset positions keyed by ticker")
    confidence_level: Optional[float] = Field(0.01, ge=0, le=1, description="Confidence level for VaR")
    cov_window_days: Optional[int] = Field(252, ge=1, description="Window length for covariance estimation")

class VarCovarResponse(BaseModel):
    portfolio_value: float
    var_dollars: float
    var_percent: float
    volatility_percent: float
    diagnostics: Optional[Dict[str, float]] = None