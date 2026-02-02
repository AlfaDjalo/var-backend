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
    # -------------------------------------------------
    # 3. Validate tickers
    # -------------------------------------------------
    tickers = set()
    for product in products:
        if "ticker" in product and product["ticker"] is not None:
            tickers.add(product["ticker"])
        elif "underlying_ticker" in product and product["underlying_ticker"] is not None:
            tickers.add(product["underlying_ticker"])

        # if hasattr(product, "ticker"):
        #     tickers.add(product.ticker)
        # elif hasattr(product, "underlying_ticker"):
        #     tickers.add(product.underlying_ticker)
    print("tickers: ", tickers)
    missing = tickers - set(df.columns)
    if missing:
        raise HTTPException(400, f"Tickers not found in dataset: {missing}")

    # -------------------------------------------------
    # 4. Windowing
    # -------------------------------------------------
    window = payload.estimation_window_days
    df = df.tail(window + 1)
    print("Window: ", window)
    if len(df) < 2:
        raise HTTPException(400, "Not enough data for historical simulation")
    
    latest_prices = df.iloc[-1][list(tickers)].to_dict()

    # -------------------------------------------------
    # 5. Calculate returns
    # -------------------------------------------------
    returns = df[list(tickers)].pct_change().dropna()
    
    # -------------------------------------------------
    # 6. Base scenario (current market state)
    # -------------------------------------------------
    base_scenario = latest_prices

    # -------------------------------------------------
    # 7. Generate historical scenario PnLs
    # -------------------------------------------------
    pnl_list = []

    for _, row in returns.iterrows():

        scenario = {
            ticker: latest_prices[ticker] * (1 + row[ticker])
            for ticker in tickers
        }

        pnl = portfolio.pnl(scenario, base_scenario)
        pnl_list.append(pnl)

    pnl_array = np.array(pnl_list)

    # -------------------------------------------------
    # 8. Calculate VaR
    # -------------------------------------------------
    confidence = payload.confidence_level

    var_dollar = -np.quantile(pnl_array, confidence)

    portfolio_value = portfolio.revalue(base_scenario)

    if portfolio_value <= 0:
        raise HTTPException(400, "Portfolio value must be positive")
    
    var_percent = var_dollar / portfolio_value

    return {
        "portfolio_value": float(portfolio_value),
        "var_dollar": float(var_dollar),
        "var_percent": float(var_percent),
    }
