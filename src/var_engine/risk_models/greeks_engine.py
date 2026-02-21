from datetime import datetime
from typing import Dict, Any, List

from var_engine.portfolio.portfolio import Portfolio
from var_engine.scenarios.scenario import Scenario


class GreeksEngine:
    """
    Computes portfolio and position-level dollar Greeks.

    Designed to:
        - Support multi-currency extension
        - Support historical time-series
        - Remain independent from VaR logic
    """

    def __init__(
        self,
        portfolio: Portfolio,
        scenario: Scenario,
        base_currency: str = "USD",
    ):
        self.portfolio = portfolio
        self.scenario = scenario
        self.base_currency = base_currency

    # ==========================================================
    # Public API
    # ==========================================================

    def run(self) -> Dict[str, Any]:
        """
        Execute full Greek-based risk calculation.

        Returns:
            Dictionary matching RiskReportResponse schema.
        """

        position_data = self._compute_position_greeks()
        portfolio_totals = self._aggregate_portfolio_greeks(position_data)
        factor_exposures = self._compute_factor_exposures()

        return {
            "as_of_date": getattr(self.scenario, "as_of_date", None),
            "base_currency": self.base_currency,
            "portfolio_risk": {
                "currency": self.base_currency,
                "greeks": portfolio_totals,
            },
            "positions": position_data,
            "factor_exposures": factor_exposures,
            "metadata": {
                "pricing_datetime": datetime.utcnow(),
                "scenario_description": "Base market scenario",
                "model": "GreeksEngine",
                "notes": None,
            },
        }

    # ==========================================================
    # Internal Helpers
    # ==========================================================

    def _compute_position_greeks(self) -> List[Dict[str, Any]]:
        """
        Collect per-position Greeks from portfolio.
        """
        positions = []

        for product in self.portfolio.products:

            if not hasattr(product, "get_dollar_greeks"):
                continue

            raw_greeks = product.get_dollar_greeks(self.scenario)

            normalized = self._normalize_greeks(raw_greeks)

            positions.append({
                "product_id": product.product_id,
                "product_type": product.__class__.__name__,
                "currency": self.base_currency,
                "greeks": normalized,
            })

        return positions

    def _aggregate_portfolio_greeks(
        self,
        positions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Sum Greeks across positions.
        """

        totals = {
            "delta": 0.0,
            "gamma": 0.0,
            "vega": 0.0,
            "theta": 0.0,
            "rho": 0.0,
        }

        for position in positions:
            greeks = position["greeks"]

            for k in totals:
                totals[k] += greeks.get(k, 0.0)

        return totals

    def _compute_factor_exposures(self) -> List[Dict[str, Any]]:
        """
        Use product-level sensitivities to compute factor exposures.
        """

        totals = self.portfolio.get_sensitivities(self.scenario)

        exposures = []

        for factor, value in totals.items():
            exposures.append({
                "factor": factor,
                "exposure": float(value),
                "currency": self.base_currency,
            })

        return exposures

    # ==========================================================
    # Utility
    # ==========================================================

    @staticmethod
    def _normalize_greeks(raw: Dict[str, float]) -> Dict[str, float]:
        """
        Convert:
            dollar_delta → delta
            dollar_gamma → gamma
        etc.
        """

        mapping = {
            "dollar_delta": "delta",
            "dollar_gamma": "gamma",
            "dollar_vega": "vega",
            "dollar_theta": "theta",
            "dollar_rho": "rho",
        }

        normalized = {
            "delta": 0.0,
            "gamma": 0.0,
            "vega": 0.0,
            "theta": 0.0,
            "rho": 0.0,
        }

        for raw_key, value in raw.items():
            clean_key = mapping.get(raw_key)
            if clean_key:
                normalized[clean_key] = float(value)

        return normalized
