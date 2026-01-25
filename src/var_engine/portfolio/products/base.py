from abc import ABC, abstractmethod

class Product(ABC):
    """
    Base class for all financial products.
    """
    def __init__(self, product_id: str, market_value: float):
        self.product_id = product_id
        self.market_value = float(market_value)

    @abstractmethod
    def revalue(self, scenario):
        """
        Revalue the product under a given scenario

        Args:
            scenario: dict-like or Series containing scenario data

        Returns:
            New market value under the scenario
        """
        pass

