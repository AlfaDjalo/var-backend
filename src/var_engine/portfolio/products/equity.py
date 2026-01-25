from .base import Product

class StockProduct(Product):
    """
    Linear equity product.
    """
    def revalue(self, scenario):
        """
        Scenario is expected to contain a return for this equity.
        """
        r = scenario[self.product_id]
        return self.market_value * (1.0 + r)