from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import os

from api.schemas.histsim import HistSimRequest, HistSimResponse
from var_engine.data_loader.csv_loader import CSVPriceLoader
from var_engine.portfolio.portfolio import Portfolio
from var_engine.portfolio.products.equity import StockProduct
from var_engine.risk_models.historical_simulation import HistSimVaR

router = APIRouter()
DATA_DIR = "data"

class InspectRequest(BaseModel):
    dataset_name: str

@router.post("/histsim/calculate", response_model=HistSimResponse)
def calculate_histsim_var(request: HistSimRequest):
    file_path = f"{DATA_DIR}/{request.dataset_name}"
    print(file_path)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=400,
            detail=f"Dataset not found: {request.dataset_name}"
        )

    try:
        loader = CSVPriceLoader(path=file_path)
        returns = loader.load_returns()
    
        if not request.positions:
            raise HTTPException(status_code=400, detail="Positions required")


        # Check all tickers in returns.columns are in positions keys
        missing_tickers = set(returns.columns) - set(request.positions.keys())
        if missing_tickers:
            raise HTTPException(
                status_code=400,
                detail=f"Positions missing tickers present in returns data: {missing_tickers}"
            )
        
        products = [
            StockProduct(
                product_id=ticker,
                market_value=float(request.positions[ticker]),
            )
            for ticker in returns.columns
        ]

        portfolio = Portfolio(products)

        model = HistSimVaR(
            confidence_level=request.confidence_level,
            hist_data_window_days=request.hist_data_window_days,
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

        results = model.run(portfolio, returns)
        # results = model.run(portfolio, returns)

        response = HistSimResponse(
            portfolio_value=results.portfolio_value,
            var_absolute=results.var_absolute,
            var_percent=results.var_percent,
            diagnostics=results.metadata,
        )

        print(response)

        return response

    except Exception as e:
        print(f"Error in calculation: {e}")
        raise HTTPException(status_code=400, detail=f"Calculation failed: {str(e)}")
    
@router.post("/histsim/inspect")
def inspect_dataset(request: InspectRequest):
    file_path = f"{DATA_DIR}/{request.dataset_name}"
    print(file_path)

    try:
        loader = CSVPriceLoader(path=file_path)
        df = loader.load_returns()
    except Exception as e:
        print(f"Error retreiving asset names: {e}")
        raise HTTPException(status_code=400, detail=f"Data load failed: {str(e)}")
    
    # df = load_dataset(request.dataset_name)

    asset_columns = [c for c in df.columns if c.lower() != "data"]

    return {
        "assets": asset_columns
    }
