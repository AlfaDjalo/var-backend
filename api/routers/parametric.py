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

router = APIRouter(prefix="/parametric", tags=["Parametric"])
DATA_DIR = DATA_PATH


class InspectRequest(BaseModel):
    dataset_name: str

@router.post("/calculate")
# @router.post("/parametric/calculate", response_model=ParametricResponse)
def calculate_parametric_var(request: ParametricRequest):
    """
    Calculate Parametric VaR.
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

    # print(request)
    # file_path = os.path.join(DATA_DIR, request.dataset_name)
    # # file_path = f"{DATA_DIR}/{request.dataset_name}"
    # print(file_path)

    # if not os.path.exists(file_path):
    #     raise HTTPException(
    #         status_code=400,
    #         detail=f"Dataset not found: {request.dataset_name}"
    #     )

    # try:
    #     loader = CSVPriceLoader(path=file_path)
    #     returns = loader.load_returns()
    #     prices_db = loader.load_prices()

    #     if prices_df.empty or returns.empty:
    #         raise HTTPException(status_code=400, detail="Price or returns data empty")
        
    #     data_tickers = set(returns.columns)
    
        # if not request.positions:
        #     raise HTTPException(status_code=400, detail="Positions required")

        # Check all tickers in returns.columns are in positions keys
        # missing_tickers = set(returns.columns) - set(request.positions.keys())
        # if missing_tickers:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"Positions missing tickers present in returns data: {missing_tickers}"
        #     )

        # products = []
        # for product_input in request.products:
        #     product = ProductFactory.from_input(
        #         product_input=product_input,
        #         spot_prices=prices_df.iloc[-1].to_dict(),
        #         position_input_type="quantity"
        #     )

        #     if hasattr(product, "product_id") and product.product_id not in data_tickers:
        #         pass
        #     products.append(product)

        
        # Extract spot prices (last price) from dataset, for example using returns or price loader
        # Assuming loader.load_prices() returns price DataFrame, otherwise use last available data from returns
        # prices_df = loader.load_prices()  # You may need to implement this method if not exists

        # print(prices_df.head(5))

        # Alternatively, approximate spot by last available price:
        # spot_prices = prices_df.iloc[-1] if not prices_df.empty else None
        # if spot_prices is None:
        #     raise HTTPException(status_code=400, detail="Price data not available for spot extraction")

        # for ticker in returns.columns:
        #     quantity = request.positions.get(ticker, 0.0)
        #     spot = float(spot_prices.get(ticker, 0.0))

        #     products.append(build_equity_products(
        #         tickers=returns.columns,
        #         positions=request.positions,
        #         spot_prices=spot_prices.to_dict(),
        #         position_input_type=request.position_input_type,
        #     ))

            # portfolio = Portfolio(products)



            # products.append(
            #     StockProduct(
            #         product_id=ticker,
            #         quantity=quantity,
            #         spot=spot,
            #     )
            # )

        # products = [
        #     StockProduct(
        #         product_id=request.product_id,
        #         quantity=request.quantity,
        #         spot=request.spot,
        #     )
        #     for ticker in returns.columns
        # ]

        # portfolio = Portfolio(products)

    model = ParametricVaR(
        confidence_level=request.confidence_level,
        cov_window_days=request.estimation_window_days,
    )

            # positions = pd.Series(request.positions).reindex(returns.columns)
            # portfolio = Portfolio(returns=returns, positions=positions)
        # else:
        #     portfolio = Portfolio(returns=returns)


        # if request.positions:
        #     positions = pd.Series(request.positions).reindex(returns.columns)
        #     portfolio = Portfolio(returns=returns, positions=positions)
        # else:
        #     portfolio = Portfolio(returns=returns)

    results = model.run(portfolio, market_data=market_data)
    # results = model.run(portfolio, returns)
    # results = model.run(portfolio, returns)

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

    # except Exception as e:
    #     print(f"Error in calculation: {e}")
    #     raise HTTPException(status_code=400, detail=f"Calculation failed: {str(e)}")
    
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


# @router.post("/parametric/inspect")
# def inspect_dataset(request: InspectRequest):
#     file_path = f"{DATA_DIR}/{request.dataset_name}"
#     print(file_path)

#     try:
#         loader = CSVPriceLoader(path=file_path)
#         df = loader.load_returns()
#     except Exception as e:
#         print(f"Error retreiving asset names: {e}")
#         raise HTTPException(status_code=400, detail=f"Data load failed: {str(e)}")
    
#     # df = load_dataset(request.dataset_name)

#     asset_columns = [c for c in df.columns if c.lower() != "data"]

#     return {
#         "assets": asset_columns
#     }
