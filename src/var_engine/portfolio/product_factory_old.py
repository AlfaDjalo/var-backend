from typing import Dict, Any, Optional
from var_engine.portfolio.products.base import Product
from var_engine.portfolio.products.equity import StockProduct
from var_engine.portfolio.products.option import OptionProduct
# from var_engine.portfolio.products.bond import BondProduct  # placeholder import
from var_engine.models.option_pricing.black_scholes import BlackScholesModel

class ProductFactory:
    """
    Factory class to create Product instances from input dictionaries.
    """

    @staticmethod
    def create_product(
        product_input: Dict[str, Any],
        spot_prices: Optional[Dict[str, float]] = None,
        position_input_type: Optional[str] = None,
        ) -> Product:
        """
        Create a Product instance based on input dict and optional context.

        Args:
            product_input: Dictionary with product input fields.
            spot_prices: Optional dict of spot prices keyed by ticker.
            position_input_type: Optional; either "quantity" or "market_value" to interpret input quantities.

        Returns:
            Product instance of appropriate subclass.

        Raises:
            ValueError if required fields are missing or unsupported product type.
        """
        product_type = product_input.get("product_type")
        if not product_type:
            raise ValueError("Product input missing 'Product_type' field")

        product_type = product_type.lower()

        if product_type == "stock":
            required_fields = {"product_id", "quantity", "spot"}
            missing = required_fields - product_input.keys()
            if missing:
                raise ValueError(f"Missing fields for StockProduct: {missing}")

            return StockProduct(
                product_id=product_input["product_id"],
                quantity=float(product_input["quantity"]),
                spot=float(product_input["spot"]),
            )

        elif product_type == "equity_option":
            required_fields = {
                "product_id",
                "underlying_id",
                "strike",
                "maturity",
                "option_type",
                "quantity",
            }
            missing = required_fields - product_input.keys()
            if missing:
                raise ValueError(f"Missing fields for OptionProduct: {missing}")

            underlying_ticker = product_input["underlying_ticker"]

            if spot_prices is None:
                raise ValueError("spot_prices required to create OptionProduct")

            initial_spot = spot_prices.get(underlying_ticker)
            if initial_spot is None:
                raise ValueError(f"Spot price not found for underlying ticker {underlying_ticker}")

            pricing_model_key = product_input.get("pricing_model", "black_scholes")

            # For now, use a default pricing model instance. You can extend this later.
            pricing_model = BlackScholesModel()

            return OptionProduct(
                product_id=product_input["product_id"],
                underlying_id=underlying_ticker,
                strike=float(product_input["strike"]),
                maturity=float(product_input["maturity"]),
                option_type=product_input["option_type"],
                quantity=float(product_input["quantity"]),
                pricing_model=pricing_model,
                initial_spot=initial_spot,
            )

        elif product_type == "bond":
            # Placeholder: Implement BondProduct constructor here
            raise NotImplementedError("Bond product creation not implemented yet")

        else:
            raise ValueError(f"Unsupported product type: {product_type}")
