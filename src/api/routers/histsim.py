# api/routers/histsim.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import pandas as pd
from typing import Dict, Any

from api.config import DATA_PATH
from api.schemas.var import HistSimRequest, HistSimResponse
from var_engine.data_loader.csv_loader import CSVPriceLoader
from api.helpers.portfolio import build_portfolio_from_request
from var_engine.risk_models.historical_simulation import HistSimVaR

router = APIRouter(prefix="/histsim", tags=["Historical Simulation"])
DATA_DIR = DATA_PATH


@router.post("/calculate")
def calculate_histsim(request: HistSimRequest):
    """
    Calculate Historical Simulation VaR using proper product structure.
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

    if request.estimation_window_days:
        returns = returns.tail(request.estimation_window_days)

    # Get latest prices (spot)
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
    # df = pd.read_csv(csv_path)

    # if DATE_COLUMN not in df.columns:
    #     raise HTTPException(400, f"Missing {DATE_COLUMN}")

    # df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])
    # df = df.set_index(DATE_COLUMN).sort_index()

    # -------------------------------------------------
    # 2. Build portfolio from products
    # -------------------------------------------------
    products = request.products
    print("products: ", products)
    if not products:
        raise HTTPException(400, "Products required")

    # if not isinstance(products, dict):
    #     raise HTTPException(400, "Products must be dict[ticker,value]")
    
    try:
        # products_dicts = [p for p in products]
        # products_dicts = [p.model_dump() for p in payload.products]
        portfolio = build_portfolio_from_request(products)
        # portfolio = build_portfolio_from_request(products_dicts)
    except Exception as e:
        raise HTTPException(400, f"Failed to build portfolio: {str(e)}")
    print("Portfolio: ", portfolio)


    model = HistSimVaR(
        confidence_level=request.confidence_level,
        hist_data_window_days = request.estimation_window_days
    )

    results = model.run(portfolio, market_data=market_data)



    response = HistSimResponse(
        portfolio_value=results.portfolio_value,
        var_dollar=results.var_dollar,
        var_percent=results.var_percent,
        diagnostics=results.metadata,
    )

    return response
