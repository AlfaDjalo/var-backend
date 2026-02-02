from abc import ABC, abstractmethod

class OptionPricingModel(ABC):
    """
    Abstract base class for option pricing models.
    """    

    def __init__(self):
    # def __init__(self, initial_vol: float, initial_rate: float):
        """
        Parameters
        ----------
        initial_vol : float
            Volatility used for initial pricing.
        initial_rate : float
            Risk-free rate used for initial pricing.
        """
        # self.initial_vol = float(initial_vol)
        # self.initial_rate = float(initial_rate)
        pass

    @abstractmethod
    def price(
        self,
        spot: float,
        strike: float,
        maturity: float,
        vol: float,
        rate: float,
        option_type: str,
    ) -> float:
        """
        Price an option.

        Parameters
        ----------
        spot : float
            Underlying spot price.
        strike : float
            Option strike.
        maturity : float
            Time to maturity in years.
        vol : float
            Volatility.
        rate : float
            Risk-free rate.
        option_type : str
            "call" or "put".

        Returns
        -------
        float
            Option price.
        """
        raise NotImplementedError
        