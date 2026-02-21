from abc import ABC, abstractmethod
from typing import Dict
from var_engine.scenarios.scenario import Scenario

class Product(ABC):
    """
    Base class for all financial products.
    """
    def __init__(self, product_id: str):
        self.product_id = product_id

    @abstractmethod
    def revalue(self, scenario: Scenario) -> float:
        """
        Revalue the product under a given scenario

        Args:
            scenario: dict-like or Series containing scenario data

        Returns:
            New market value under the scenario
        """
        pass

    @abstractmethod
    def get_sensitivities(self, scenario: Scenario) -> Dict[str, float]:
        """
        Return factor exposures in currency units.

        Mapping:
            factor_id -> dV/d(return_factor)
        """
        pass

    def factor_pnl(self, scenario, base_scenario):
        """
        Optional exact factor decomposition.
        Default: None (portfolio will fallback to Greeks).
        """
        return None
        
    # @property
    # def market_value(self):
    #     raise NotImplementedError("Use revalue(scenario) to get market value")

