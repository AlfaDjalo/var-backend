from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import pandas as pd
from typing import Dict, Any

from api.config import DATA_PATH
from api.schemas.var import MonteCarloRequest, MonteCarloResponse
from var_engine.data_loader.csv_loader import CSVPriceLoader
from api.helpers.portfolio import build_portfolio_from_request
from var_engine.risk_models.monte_carlo import MonteCarloVaR


router = APIRouter(prefix="/montecarlo", tags=["Monte Carlo Simulation"])
DATA_DIR = DATA_PATH


class InspectRequest(BaseModel):
    dataset_name: str

@router.post("/calculate")
def calculate_montecarlo_var(request: MonteCarloRequest):
    """
    Calculate Monte Carlo Simulation VaR.
    """
    # -------------------------------------------------
    # 1. Load dataset
    # -------------------------------------------------
    print("Loading dataset.")
    dataset_name = request.dataset_name
    print("dataset_name:", dataset_name)
    if not dataset_name:
        raise HTTPException(400, "Dataset name required")
    print("DATA_DIR:", DATA_DIR)

    csv_path = Path(DATA_DIR) / dataset_name
    print("csv_path:", csv_path)
    if not csv_path.exists():
        raise HTTPException(400, f"Dataset not found: {dataset_name}")

    loader = CSVPriceLoader(path=csv_path)
    prices = loader.load_prices()
    returns = loader.load_returns()

    if prices.empty or returns.empty:
        raise HTTPException(400, "Insufficient data")

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
    print("Portfolio: ", portfolio)


    model = MonteCarloVaR(
        confidence_level=request.confidence_level,
        n_sims=request.n_sims,
        random_seed=request.random_seed
    )

    results = model.run(portfolio, market_data=market_data)

    response = MonteCarloResponse(
        portfolio_value=results.portfolio_value,
        var_dollar=results.var_dollar,
        var_percent=results.var_percent,
        diagnostics=results.metadata,
    )

    return response

    
@router.post("/inspect")
def inspect_dataset(request: InspectRequest):
    file_path = f"{DATA_DIR}/{request.dataset_name}"

    try:
        loader = CSVPriceLoader(path=file_path)
        df = loader.load_returns()
    except Exception as e:
        print(f"Error retreiving asset names: {e}")
        raise HTTPException(status_code=400, detail=f"Data load failed: {str(e)}")
    
    asset_columns = [c for c in df.columns if c.lower() != "date"]

    return {
        "assets": asset_columns
    }
