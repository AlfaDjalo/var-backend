from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict

class MonteCarloRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str = Field(..., description="Dataset file name to use")
    positions: Optional[Dict[str, float]] = Field(None, description="Optional asset positions keyed by ticker")
    parameter_estimation_window_days: Optional[int] = Field(252, description="Data window for estimation of distribution parameters (days)")
    confidence_level: Optional[float] = Field(0.01, gt=0, lt=1, description="Confidence level for VaR")
    n_sims: int = Field(10_000, gt=0, description="Number of Monte Carlo simulations")
    random_seed: Optional[int] = Field(None, description="Random seed for reproducibility")

class MonteCarloResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    portfolio_value: float
    var_absolute: float
    var_percent: float
    diagnostics: Optional[Dict[str, Any]] = None