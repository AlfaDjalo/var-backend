from var_engine.config.loader import ConfigLoader
from var_engine.data_loader.csv_loader import CSVPriceLoader
from var_engine.portfolio.portfolio import Portfolio
from var_engine.risk_models.variance_covariance.model import VarianceCovarianceVaR

import pandas as pd

def main():
    config = ConfigLoader("config/settings.yaml")
    data_cfg = config.data_config

    loader = CSVPriceLoader(
        path=data_cfg["path"],
        date_column=data_cfg.get("date_column", "date"),
    )

    returns = loader.load_returns()

    print(returns.head(5))

    portfolio_eq = Portfolio(returns=returns)

    print("Portfolio value:", portfolio_eq.portfolio_value)
    print("Positions (equal weight):")
    print(portfolio_eq.positions)

    print("\nWeights:")
    print(portfolio_eq.weights)

    print("\nPortfolio returns head:")
    print(portfolio_eq.portfolio_returns().head())

    positions = pd.Series(1_000_000, index=returns.columns)
    portfolio_custom = Portfolio(returns=returns, positions=positions)

    print("\nCustom portfolio value:", portfolio_custom.portfolio_value)
    print("Custom Positions:")
    print(portfolio_custom.positions)

    print("\nCustom weights:")
    print(portfolio_custom.weights)

    print("\nCustom portfolio returns head:")
    print(portfolio_custom.portfolio_returns().head())    

    var_calc = VarianceCovarianceVaR(confidence_level=0.01, cov_window_days=252)

    results = var_calc.calculate_var(portfolio_eq)

    print("VaR (99%):", results["VaR"])
    print("Portfolio Variance:", results["portfolio_variance"])
    print("Portfolio Volatility:", results["portfolio_volatility"])
    print("Mean Return:", results["mean_return"])

if __name__ == "__main__":
    main()