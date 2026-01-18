from typing import Optional
import pandas as pd

class Portfolio:
    def __init__(self, returns: pd.DataFrame, positions: Optional[pd.Series]=None):
        """
        Initialise the Portfolio.

        Args:
            returns: DataFrame of asset returns; index = datetime, columns = tickers.
            positions: Optional Series mapping tickers to current market values.
                        If None, assumes equal weighted exposures summing to 1.

        Raises:
            ValueError if tickers in positions don't align with returns columns.
        """
        self.returns = returns.copy()

        # Validate positions or set default equal exposures summing to 1
        if positions is None:
            n_assets = len(self.returns.columns)
            equal_exposure = 1.0 / n_assets
            self.exposures = pd.Series(
                data=[equal_exposure] * n_assets, index=self.returns.columns, dtype=float
            )
        else:
            # Validate tickers match exactly (no extras or missing)
            missing = set(positions.index) - set(self.returns.columns)
            extra = set(self.returns.columns) - set(positions.index)
            if missing:
                raise ValueError(f"Positions contain tickers not in returns data: {missing}")
            if extra:
                raise ValueError(f"Returns data contain tickers not in positions: {extra}")

            self.exposures = positions.reindex(self.returns.columns).astype(float)

        if (self.exposures < 0).any():
            # You might allow short positions, but for now let's just warn or raise
            print("Warning: Negative exposures detected (short positions).") 
   
    @property
    def portfolio_value(self) -> float:
        """Current total portfolio market value (sum of exposures)."""
        return self.exposures.sum()

    @property
    def weights(self) -> pd.Series:
        """
        Derived portfolio weights as exposures normalized to sum to 1.
        For display and relative comparisons only.
        """
        total = self.portfolio_value
        if total == 0: 
            return pd.Series(0, index=self.exposures.index)
        return self.exposures / total
        
    def portfolio_returns(self) -> pd.Series:
        """
        Calculate the portfolio return time series as weighted sum of asset returns.

        Returns:
            Series indexed by date.
        """
        # portfolio return = sum(weights_i * returns_i)
        return self.returns.dot(self.weights)

    def revalue(self, scenario_returns: pd.DataFrame) -> pd.Series:
        """
        Revalue the portfolio under multiple scenarios of returns.

        Args:
            scenario_returns: DataFrame of scenario returns; index=scenario_id or datetime,
                              columns=tickers (same assets as this portfolio).

        Returns:
            Series of portfolio values or P&L per scenario.
        
        Notes:
            For equities, this can be calculated as:
                initial portfolio value * (1 + portfolio return in scenario)
            More complex instruments will override this method.
        """
        # For each scenario: portfolio value * (1 + portfolio return in that scenario)
        port_returns = scenario_returns.dot(self.weights)
        return self.portfolio_value * (1 + port_returns)
