from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd

from api.schemas.var_covar import VarCovarRequest, VarCovarResponse
from var_engine.data_loader.csv_loader import CSVPriceLoader
from var_engine.portfolio.portfolio import Portfolio
from var_engine.methods.variance_covariance.model import VarianceCovarianceVaR

router = APIRouter()

DATA_DIR = "data"

class InspectRequest(BaseModel):
    dataset_name: str

@router.post("/var-covar/calculate", response_model=VarCovarResponse)
def calculate_var_covar(request: VarCovarRequest):
    file_path = f"{DATA_DIR}/{request.dataset_name}"
    print(file_path)

    try:
        loader = CSVPriceLoader(path=file_path)
        returns = loader.load_returns()
    
        if request.positions:
            positions = pd.Series(request.positions).reindex(returns.columns)
            portfolio = Portfolio(returns=returns, positions=positions)
        else:
            portfolio = Portfolio(returns=returns)

        var_covar = VarianceCovarianceVaR(
            confidence_level=request.confidence_level,
            cov_window_days=request.cov_window_days,
        )

        results = var_covar.calculate_var(portfolio)

        response = VarCovarResponse(
            portfolio_value=results["portfolio_value"],
            var_dollars=results["VaR_dollars"],
            var_percent=results["VaR_percent"],
            volatility_percent=results["volatility_percent"],
            correlation_matrix=results["correlation_matrix"],
            diagnostics=results.get("diagnostics"),
        )

        return response

    except Exception as e:
        print(f"Error in calculation: {e}")
        raise HTTPException(status_code=400, detail=f"Calculation failed: {str(e)}")
    
@router.post("/var-covar/inspect")
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
