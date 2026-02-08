from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field

class HistSimRequest(BaseModel):
    dataset_name: str = Field(..., description="Dataset file name to use")
    positions: Optional[Dict[str, float]] = Field(None, description="Optional asset positions keyed by ticker")
    hist_data_window_days: Optional[int] = Field(252, description="Historical Data window (days)")
    confidence_level: Optional[float] = Field(0.01, gt=0, lt=1, description="Confidence level for VaR")

class HistSimResponse(BaseModel):
    portfolio_value: float
    var_absolute: float
    var_percent: float
    diagnostics: Optional[Dict[str, Any]] = None