from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import Dict, Any

from api.helpers.portfolio import build_portfolio_from_request
from api.config import DATA_PATH
from var_engine.data_loader.csv_loader import CSVPriceLoader
from var_engine.risk_models.greeks_model import GreeksService

router = APIRouter(prefix="/greeks", tags=["Greeks"])

DATA_DIR = DATA_PATH


@router.post("/calculate")
def calculate_greeks(request: dict):

    dataset_name = request.get("dataset_name")
    if not dataset_name:
        raise HTTPException(400, "Dataset name required")

    csv_path = Path(DATA_DIR) / dataset_name
    if not csv_path.exists():
        raise HTTPException(400, f"Dataset not found: {dataset_name}")

    try:
        loader = CSVPriceLoader(
            path=csv_path,
            asof_date=request.get("asof_date")
        )

        market_data: Dict[str, Any] = loader.build_market_data(
            estimation_window_days=request.get("estimation_window_days")
        )
    except Exception as e:
        raise HTTPException(400, f"Failed to load market data: {e}")

    products = request.get("products")
    if not products:
        raise HTTPException(400, "Products required")

    try:
        portfolio = build_portfolio_from_request(products)
    except Exception as e:
        raise HTTPException(400, f"Failed to build portfolio: {e}")

    try:
        service = GreeksService(
            portfolio,
            rate=request.get("rate", 0.05),
        )

        results = service.compute(market_data=market_data)

    except Exception as e:
        raise HTTPException(500, f"Greeks calculation failed: {e}")

    return results
