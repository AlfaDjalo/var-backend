import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

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
        """
        Load prices from CSV file into pandas DataFrame.

        Args:
            asof_date: Optional date string to filter data up to this date.

        Returns:
            DataFrame indexed by date with asset prices as columns.
        """
        try:
            df = pd.read_csv(self.path)
        except Exception as e:
            raise DataLoaderError(f"Failed to read CSV: {e}")

        if self.date_column not in df.columns:
            raise DataLoaderError(
                f"Date column '{self.date_column}' not found in CSV"
            )

        df[self.date_column] = pd.to_datetime(df[self.date_column])
        df = df.set_index(self.date_column).sort_index()

        # Use method argument if provided, else instance property
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
        """
        Calculate asset log returns from price data.

        Args:
            asof_date: Optional date string to filter data up to this date.

        Returns:
            DataFrame indexed by datetime with log returns.
        """
        prices = self.load_prices(asof_date=asof_date)

        returns = np.log(prices / prices.shift(1)).dropna()

        if returns.empty:
            raise DataLoaderError("Return DataFrame is empty after processing")

        return returns
