from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import pandas as pd
from typing import Dict, Any

from api.config import DATA_PATH
from api.schemas.var import ParametricRequest, ParametricResponse
from var_engine.data_loader.csv_loader import CSVPriceLoader
from api.helpers.portfolio import build_portfolio_from_request
from var_engine.risk_models.parametric import ParametricVaR


# import os

# from var_engine.portfolio.portfolio import Portfolio
# from var_engine.portfolio.product_factory import ProductFactory
# from var_engine.portfolio.builders import ProductFactory

# router = APIRouter()
router = APIRouter(prefix="/parametric", tags=["Parametric"])
DATA_DIR = DATA_PATH


class InspectRequest(BaseModel):
    dataset_name: str

# @router.post("/parametric/calculate")
@router.post("/calculate")
# @router.post("/parametric/calculate", response_model=ParametricResponse)
def calculate_parametric_var(request: ParametricRequest):
    """
    Calculate Parametric VaR.
    """
    print("request: ", request)
    # -------------------------------------------------
    # 1. Load dataset
    # -------------------------------------------------
    # print("Loading dataset.")
    dataset_name = request.dataset_name
    # print("dataset_name:", dataset_name)
    if not dataset_name:
        raise HTTPException(400, "Dataset name required")
    # print("DATA_DIR:", DATA_DIR)

    csv_path = Path(DATA_DIR) / dataset_name
    # print("csv_path:", csv_path)
    if not csv_path.exists():
        raise HTTPException(400, f"Dataset not found: {dataset_name}")

    loader = CSVPriceLoader(
        path=csv_path,
        asof_date=request.asof_date
    )
    prices = loader.load_prices()
    returns = loader.load_returns()

    if prices.empty or returns.empty:
        raise HTTPException(400, "Insufficient data")

    if request.estimation_window_days:
        returns = returns.tail(request.estimation_window_days)

    # Get latest prices (spots)
    latest_prices = prices.iloc[-1]

    spot: Dict[str, float] = {
        k: float(v) for k, v in latest_prices.to_dict().items()
    }

    # Estimate covariance from returns

    cov = returns.cov()

    market_data: Dict[str, Any] = {
        "spot": spot,
        "returns": returns,
        "cov": cov,
        "horizon": 1.0 / 252,
    }

    # -------------------------------------------------
    # 2. Build portfolio from products
    # -------------------------------------------------
    products = request.products
    print("products: ", products)
    if not products:
        raise HTTPException(400, "Products required")
    
    try:
        portfolio = build_portfolio_from_request(products)

    except Exception as e:
        raise HTTPException(400, f"Failed to build portfolio: {str(e)}")
    # print("Portfolio: ", portfolio)

    model = ParametricVaR(
        confidence_level=request.confidence_level,
        cov_window_days=request.estimation_window_days,
    )


    results = model.run(portfolio, market_data=market_data)

    print("Diagnostics: ", results.metadata.keys())

    response = ParametricResponse(
        portfolio_value=results.portfolio_value,
        var_dollar=results.var_dollar,
        var_percent=results.var_percent,
        # volatility_percent=results.volatility,            
        # correlation_matrix=results.metadata["correlation_matrix"],
        diagnostics=results.metadata,
    )

    # print(response)

    return response

    
# @router.post("/parameric/inspect")
@router.post("/inspect")
def inspect_dataset(request: InspectRequest):
    file_path = f"{DATA_DIR}/{request.dataset_name}"
    print(file_path)

    try:
        loader = CSVPriceLoader(path=file_path)
        df = loader.load_prices()  # Use load_prices here to get prices, not returns
        if df.empty:
            raise HTTPException(status_code=400, detail="Price data is empty")

        asset_columns = [c for c in df.columns if c.lower() != "date"]

        # Get last available prices as dict
        spot_prices = df.iloc[-1].to_dict()

        return {
            "assets": asset_columns,
            "spot_prices": spot_prices,
        }

    except Exception as e:
        print(f"Error retrieving asset names and spot prices: {e}")
        raise HTTPException(status_code=400, detail=f"Data load failed: {str(e)}")


