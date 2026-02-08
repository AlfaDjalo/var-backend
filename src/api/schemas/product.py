from typing import Literal, Union, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class BaseProductInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(..., description="Unique product identifier")
    product_type: str = Field(..., description="Discriminator for product type")


class StockProductInput(BaseProductInput):
    product_type: Literal["stock"] = "stock"

    ticker: str = Field(..., description="Ticker / asset identifier")
    quantity: float = Field(..., gt=0, description="Number of shares held")


class OptionProductInput(BaseProductInput):
    product_type: Literal["equity_option"] = "equity_option"

    underlying_ticker: str = Field(..., description="Underlying equity ticker")
    strike: float = Field(..., description="Strike price")
    maturity: float = Field(..., gt=0, description="Time to maturity in years")
    option_type: Literal["call", "put"] = Field(..., description="Option type")
    quantity: float = Field(..., gt=0, description="Number of contracts held")

    pricing_model: Optional[str] = Field(
        "black_scholes",
        description="Pricing model key to resolve backend-side"
    )


class BondProductInput(BaseProductInput):
    product_type: Literal["bond"] = "bond"

    issuer: str = Field(..., description="Issuer name or ID")
    maturity: float = Field(..., gt=0, description="Time to maturity in years")
    coupon: float = Field(..., ge=0, description="Annual coupon rate")
    notional: float = Field(..., gt=0, description="Notional amount")
    frequency: int = Field(2, description="Coupon payment frequency per year")


ProductInput = Union[
    StockProductInput,
    OptionProductInput,
    BondProductInput,
]


class VaRRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str = Field(..., description="Dataset filename to use")
    asof_date: str = Field(..., description="Valuation date (YYYY-MM-DD)")
    confidence_level: float = Field(0.01, gt=0, lt=1, description="VaR confidence level")
    estimationWindowDays: int = Field(252, ge=1, description="Estimation window size in days")
    products: List[ProductInput] = Field(..., description="List of portfolio products")


# Example usage:
# var_req = VaRRequest(
#     dataset_name="portfolio_prices_10.csv",
#     asof_date="2026-01-30",
#     confidence_level=0.01,
#     estimationWindowDays=252,
#     products=[
#         StockProductInput(product_id="AAPL_1", ticker="AAPL", quantity=100),
#         OptionProductInput(
#             product_id="AAPL_CALL_1",
#             underlying_id="AAPL",
#             strike=150,
#             maturity=0.5,
#             option_type="call",
#             quantity=10,
#             pricing_model="black_scholes",
#         ),
#         BondProductInput(
#             product_id="BOND_1",
#             issuer="US_Treasury",
#             maturity=5,
#             coupon=0.02,
#             notional=1000000,
#             frequency=2,
#         ),
#     ],
# )
