from fastapi import APIRouter, HTTPException
from api.schemas.var_covar import VarCovarRequest, VarCovarResponse
from var_engine.data_loader.csv_loader import CSVPriceLoader
from var_engine.portfolio.portfolio import Portfolio
from var_engine.methods.variance_covariance.model import VarianceCovarianceVaR

router = APIRouter()

DATA_DIR = "data"

@router.post("/var-covar/calculate", response_model=VarCovarResponse)
def calculate_var_covar(request: VarCovarRequest):
    file_path = f"{DATA_DIR}/{request.dataset_name}"

    try:
        loader = CSVPriceLoader(path=file_path)
        returns = loader.load_returns()
    
        if request.weights:
            weights = request.weights
        else:
            tickers = returns.columns.tolist()
            equal_weight = 1.0 / len(tickers)
            weights = {ticker: equal_weight for ticker in tickers}

        portfolio = Portfolio(returns=returns)
        # portfolio = Portfolio(returns=returns, weights=weights)

        var_covar = VarianceCovarianceVaR(
            confidence_level=request.confidence_level,
            cov_window_days=request.cov_window_days,
        )

        results = var_covar.calculate_var(portfolio)

        response = VarCovarResponse(
            var=results["VaR"],
            portfolio_volatility=results["portfolio_volatility"],
            portfolio_mean_return=results["portfolio_mean_return"],
            diagnostics=results.get("diagnostics")
        )

        return response

    except Exception as e:
        print(f"Error in calculation: {e}")
        raise HTTPException(status_code=400, detail=f"Calculation failed: {str(e)}")