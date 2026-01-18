import numpy as np
import pandas as pd
from typing import Callable, Optional, Dict
from scipy.stats import norm

class VarianceCovarianceVaR:
    def __init__(
            self,
            confidence_level: float = 0.01,
            cov_window_days: int = 252,
            cov_estimator: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
    ):
        """
        Args:
            confidence_level: e.g., 0.01 for 99% VaR.
            cov_window_days: lookback window size for covariance calculation.
            cov_estimator: optional function to compute covariance matrix from returns.
                           Signature: (returns_df) -> covariance_df
                           If None, uses sample covariance.
        """
        if not 0 < confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        self.confidence_level = confidence_level
        self.cov_window_days = cov_window_days
        self.cov_estimator = cov_estimator or (lambda r: r.cov())

    def calculate_var(self, portfolio) -> Dict[str, float]:
        """
        Calculate VaR and related metrics for the given portfolio.

        Args:
            portfolio: Portfolio instance with `returns` (DataFrame) and `exposures` (Series).

        Returns:
            Dictionary with keys:
              - 'VaR': Value at Risk (positive number representing potential loss)
              - 'portfolio_variance': Variance of portfolio returns
              - 'portfolio_volatility': Std deviation of portfolio returns
              - 'mean_return': Mean portfolio return over window
        """
        returns = portfolio.returns

        # Use last cov_window_days returns
        returns_window = returns.tail(self.cov_window_days)
        if returns_window.shape[0] < self.cov_window_days:
            raise ValueError(
                f"Not enough return data to calculate covariance matrix for window size {self.cov_window_days}"
            )
        
        # Calculate covariance matrix of returns
        cov_matrix = self.cov_estimator(returns_window)

        # Portfolio exposures aligned to returns columns
        exposures = portfolio.exposures.reindex(returns.columns)

        # Calculate portfolio variance = w.T * Cov * w
        port_var = exposures.T @ cov_matrix.values @ exposures

        # Portfolio volatility (std dev)
        port_vol = np.sqrt(port_var)

        # Mean portfolio return over the window (weighted sum)
        mean_ret = (returns_window.dot(portfolio.weights)).mean()

        # VaR calculation (assuming normality)
        z_score = norm.ppf(self.confidence_level)

        # VaR is positive number representing loss magnitude
        VaR = -z_score * port_vol

        return {
            "VaR": VaR,
            "portfolio_variance": port_var,
            "portfolio_volatility": port_vol,
            "portfolio_mean_return": mean_ret,
        }
