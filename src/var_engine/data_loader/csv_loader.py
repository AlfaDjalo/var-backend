import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any


class DataLoaderError(Exception):
    pass


class CSVPriceLoader:
    def __init__(
        self,
        path: str | Path,
        date_column: str = "Date",
        asof_date: Optional[str] = None,
    ):
        self.path = Path(path)
        self.date_column = date_column
        self.asof_date = pd.to_datetime(asof_date) if asof_date else None

        if not self.path.exists():
            raise DataLoaderError(f"CSV file not found: {self.path}")

    def load_prices(self, asof_date: Optional[str] = None) -> pd.DataFrame:
        df = pd.read_csv(self.path)
        if self.date_column not in df.columns:
            raise DataLoaderError(
                f"Date column '{self.date_column}' not found in CSV"
            )

        df[self.date_column] = pd.to_datetime(df[self.date_column])
        df = df.set_index(self.date_column).sort_index()

        effective_asof = pd.to_datetime(asof_date) if asof_date else self.asof_date
        if effective_asof is not None:
            df = df.loc[df.index <= effective_asof]
            if df.empty:
                raise DataLoaderError(
                    f"No data available on or before asof_date={effective_asof.date()}"
                )

        if not all(np.issubdtype(dtype, np.number) for dtype in df.dtypes):
            raise DataLoaderError("All price columns must be numeric")

        return df

    def load_returns(self, asof_date: Optional[str] = None) -> pd.DataFrame:
        prices = self.load_prices(asof_date=asof_date)
        returns = np.log(prices / prices.shift(1)).dropna()
        if returns.empty:
            raise DataLoaderError("Return DataFrame is empty after processing")
        return returns

    # --------------------------------------------
    # New method: Build market data dictionary
    # --------------------------------------------
    def build_market_data(
        self,
        asof_date: Optional[str] = None,
        estimation_window_days: Optional[int] = None,
        horizon: float = 1.0 / 252,
    ) -> Dict[str, Any]:
        """
        Returns a market_data dict compatible with VaR or Greeks models.
        Includes spot, returns, covariance, and horizon.
        """
        prices = self.load_prices(asof_date=asof_date)
        returns = self.load_returns(asof_date=asof_date)

        if estimation_window_days:
            returns = returns.tail(estimation_window_days)

        latest_prices = prices.iloc[-1]
        spot = {k: float(v) for k, v in latest_prices.to_dict().items()}

        cov = returns.cov()

        market_data: Dict[str, Any] = {
            "spot": spot,
            "returns": returns,
            "cov": cov,
            "horizon": horizon,
        }

        return market_data
