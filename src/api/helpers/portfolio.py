#api/helpers/portfolio.py
from typing import List, Dict, Any

from var_engine.portfolio.portfolio import Portfolio
# from var_engine.portfolio.products.base import Product
from var_engine.portfolio.product_factory import ProductFactory

def build_portfolio_from_request(products: List[Dict]) -> Portfolio:
    """
    Build a Portfolio from raw product input dictionaries.

    This function is intentionally market-data agnostic.
    All valuation must be performed via scenarios.

    Args:
        products: List of product input dicts
                  (e.g. from Pydantic model `.model_dump()`)

    Returns:
        Portfolio instance
    """
    print("Building portfolio from request.")
    product_objs = [
        ProductFactory.create_product(product_input=p)
        for p in products
    ]

    return Portfolio(product_objs)