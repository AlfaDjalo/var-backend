from typing import Optional
import pandas as pd

class Portfolio:
    def __init__(self, returns: pd.DataFrame, positions: Optional[pd.Series]=None):
        """
        Initialise the Portfolio.

        Args:
            returns: DataFrame of asset returns; index = datetime, columns = tickers.
            positions: Optional Series mapping tickers to current market values.
                        If None, assumes equal weighted positions summing to 1.

        Raises:
            ValueError if tickers in positions don't align with returns columns.
        """
        self.returns = returns.copy()

        # Validate positions or set default equal positions summing to 1
        if positions is None:
            n_assets = len(self.returns.columns)
            equal_position = 1.0 / n_assets
            self.positions = pd.Series(
                data=[equal_position] * n_assets, index=self.returns.columns, dtype=float
            )
        else:
            # Validate tickers match exactly (no extras or missing)
            missing = set(positions.index) - set(self.returns.columns)
            if missing:
                raise ValueError(f"Positions contain tickers not in returns data: {missing}")

            # extra = set(self.returns.columns) - set(positions.index)
            # if missing:
            #     raise ValueError(f"Positions contain tickers not in returns data: {missing}")
            # if extra:
            #     raise ValueError(f"Returns data contain tickers not in positions: {extra}")

            # Reindex positions to returns columns, filling missing with zero
            positions = positions.reindex(self.returns.columns, fill_value=0)
            self.positions = positions
            
            # self.positions = positions.reindex(self.returns.columns).astype(float)

        if (self.positions < 0).any():
            # You might allow short positions, but for now let's just warn or raise
            print("Warning: Negative positions detected (short positions).") 
   
    @property
    def portfolio_value(self) -> float:
        """Current total portfolio market value (sum of positions)."""
        return self.positions.sum()

    @property
    def weights(self) -> pd.Series:
        """
        Derived portfolio weights as positions normalized to sum to 1.
        For display and relative comparisons only.
        """
        total = self.portfolio_value
        if total == 0: 
            return pd.Series(0, index=self.positions.index)
        return self.positions / total
        
    @property
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
