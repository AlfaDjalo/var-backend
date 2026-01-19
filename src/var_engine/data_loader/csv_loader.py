import pandas as pd
import numpy as np
from pathlib import Path

class DataLoaderError(Exception):
    pass


class CSVPriceLoader:
    def __init__(self, path:str | Path, date_column: str="Date"):
        self.path = Path(path)
        self.date_column = date_column

        if not self.path.exists():
            raise DataLoaderError(f"CSV file not found: {self.path}")
        
    def load_prices(self) -> pd.DataFrame:
        """
        Load prices from csv file into pandas dataframe.

        Returns:
            Dataframe with columns:
              - 'Date': Datetime. This is the index.
              - Tickers: Tickers for each asset.
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
        df = df.set_index(self.date_column)
        df = df.sort_index()

        if not all(np.issubdtype(dtype, np.number) for dtype in df.dtypes):
            raise DataLoaderError("All price columns must be numeric")
        
        return df
    
    def load_returns(self) -> pd.DataFrame:
        """
        Calculate asset log returns from price data.

        Returns:
            Dataframe index by datetome, with one column per asset ticker,
            containing log returns.
        """
        prices = self.load_prices()

        # log returns
        returns = np.log(prices / prices.shift(1))
        returns = returns.dropna()

        if returns.empty:
            raise DataLoaderError("Return DataFrame is empty after processing")
        
        return returns