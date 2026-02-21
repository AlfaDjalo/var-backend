from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# Shared Product Schema (reuse from VaR if identical)
# ============================================================

class ProductInput(BaseModel):
    product_id: str
    product_type: str

    # Equity
    ticker: Optional[str] = None

    # Options
    underlying_ticker: Optional[str] = None
    strike: Optional[float] = None
    maturity: Optional[float] = None
    option_type: Optional[str] = None

    # Common
    quantity: float

    # Bonds
    issuer: Optional[str] = None
    coupon: Optional[float] = None
    frequency: Optional[int] = None


# ============================================================
# Risk Request
# ============================================================

class RiskRequest(BaseModel):
    """
    Point-in-time risk request.
    Simpler than VaR: no simulation settings.
    """

    dataset_name: str

    as_of_date: Optional[date] = None

    base_currency: str = Field(
        default="USD",
        description="Reporting currency for aggregated risk."
    )

    products: List[ProductInput]

    # Optional overrides (future-proofing)
    spot_overrides: Optional[Dict[str, float]] = None
    vol_overrides: Optional[Dict[str, float]] = None
    rate_overrides: Optional[Dict[str, float]] = None


# ============================================================
# Greeks Containers
# ============================================================

class DollarGreeks(BaseModel):
    """
    All values are dollar Greeks.
    """

    delta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0
    theta: float = 0.0
    rho: float = 0.0


class PositionRisk(BaseModel):
    """
    Per-position risk report.
    """

    product_id: str
    product_type: str

    currency: Optional[str] = "USD"

    greeks: DollarGreeks


class FactorExposure(BaseModel):
    """
    Aggregated exposure by risk factor.

    Examples:
        spot:AAPL
        vol:AAPL
        rate:USD
        fx:EURUSD
    """

    factor: str
    exposure: float
    currency: Optional[str] = "USD"


# ============================================================
# Portfolio-Level Risk
# ============================================================

class PortfolioRisk(BaseModel):
    """
    Portfolio aggregate Greeks.
    """

    currency: str = "USD"

    greeks: DollarGreeks


# ============================================================
# Metadata
# ============================================================

class RiskMetadata(BaseModel):
    """
    Future-proof metadata container.
    """

    pricing_datetime: datetime
    scenario_description: Optional[str] = None

    model: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# Main Response
# ============================================================

class RiskReportResponse(BaseModel):
    """
    Master risk response.

    Designed to grow into:
      - attribution
      - stress testing
      - historical snapshots
    """

    as_of_date: Optional[date]

    base_currency: str

    portfolio_risk: PortfolioRisk

    positions: List[PositionRisk]

    factor_exposures: List[FactorExposure]

    metadata: RiskMetadata
