from abc import ABC
from typing import Optional, Sequence, List, Dict, Any
import pandas as pd
import numpy as np

from .base import VaRResult, ScenarioSet
from var_engine.scenarios.scenario import Scenario

class VaRModel(ABC):
    """
    Abstract base class for VaR risk models.

    A VaRModel:
    - Accepts a Portfolio and a ScenarioSet
    - Values the portfolio under scenarios
    - Computes VaR from the resulting P&L distribution    
    """

    def __init__(
            self,
            confidence_level: float,
            enable_attribution: bool = True,
            n_tail: int = 20,
            n_var_near: int = 10,
            ):
        if not 0 < confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        self.confidence_level = confidence_level
        self.enable_attribution = enable_attribution
        self.n_tail = n_tail
        self.n_var_near = n_var_near

    def run(self, portfolio, base_scenario: ScenarioSet = None, scenarios: Optional[Sequence[ScenarioSet]] = None) -> VaRResult:
        """
        High-entry point for VaR calculation.
        This flow should remain consistent across all VaR models.
        """
        portfolio_value = portfolio.revalue(base_scenario)

        if portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive")
        
        # ---------------------------
        # Revaluation loop
        # ---------------------------        
        scenario_values = []
        pnls = []

        for s in scenarios:
            v = portfolio.revalue(s)
            scenario_values.append(v)
            pnls.append(v - portfolio_value)

        pnl = pd.Series(pnls)

        # ---------------------------
        # VaR / ES
        # ---------------------------
        var_dol = self.compute_var(pnl)
        es = self.compute_es(pnl)
        var_pct = var_dol / portfolio_value

        # ---------------------------
        # Scenario selection
        # ---------------------------
        selected = self._select_var_scenarios(
            pnl=pnl,
            scenarios=scenarios,
        )        

        # ---------------------------
        # Attribution
        # ---------------------------
        attribution = None

        if self.enable_attribution:
            attribution = self._compute_attribution(
                portfolio=portfolio,
                base_scenario=base_scenario,
                selected=selected,
            )

        # ---------------------------
        # Diagnostics
        # ---------------------------            

        # scenario_values = pd.Series(
        #     [portfolio.revalue(s) for s in scenarios]
        # )
        # pnl = scenario_values - portfolio_value        
        # self._pnl_dist = pnl.tolist()
        
        # var_dol = self.compute_var(pnl=pnl)
        # es = self.compute_es(pnl)
        
        # var_pct = var_dol / portfolio_value if portfolio_value != 0 else 0.0

        diagnostics = self._compute_diagnostics(
        # diagnostics_core = self._compute_diagnostics(
            pnl=pnl,
            var=var_dol,
            es=es,
            attribution=attribution,
            selected=selected,
            # scenario_values=scenario_values.tolist(),
        )

        # meta = self.model_metadata()

        # diagnostics = {
        #     "metadata": meta,
        #     **diagnostics_core,
        # }
        # meta.update(diagnostics)

        return VaRResult(
            portfolio_value=float(portfolio_value),
            var_dollar=float(var_dol),
            var_percent=float(var_pct),
            confidence_level=self.confidence_level,
            metadata=diagnostics,
        )
    
    def revalue_portfolio(self, portfolio, scenarios: ScenarioSet) -> pd.Series:
        """
        Default full revaluation logic using the portfolio.
        Subclasses may override if needed.
        """
        return scenarios.scenarios.apply(
            lambda row: portfolio.revalue(row),
            axis=1
        )
    
    # def compute_var(self, pnl: pd.Series) -> float:
    #     if pnl is None or pnl.empty:
    #         raise ValueError("Valid P&L required")

    #     q = np.quantile(pnl, self.confidence_level)
    #     return float(-q)
    
    #     # return float(
    #     #     -np.quantile(
    #     #         pnl,
    #     #         self.confidence_level,
    #     #     )
    #     # )


    # def compute_es(self, pnl: pd.Series) -> float:
    #     if pnl is None or pnl.empty:
    #         raise ValueError("Valid P&L required")

    #     q = np.quantile(pnl, self.confidence_level)
    #     tail = pnl[pnl <= q]
    #     return float(-tail.mean())


    # =====================================================
    # Diagnostics
    # =====================================================
    def _compute_diagnostics(
        self,
        pnl: pd.Series,
        var: float,
        es: float,
        attribution = None,
        selected = [],
    ) -> dict:

        diag = {
            "pnls": pnl.tolist(),
            "distribution": {
                "mean": float(pnl.mean()),
                "std": float(pnl.std(ddof=1)),
                "min": float(pnl.min()),
                "max": float(pnl.max()),
                "skew": float(pnl.skew()),
                "kurtosis": float(pnl.kurtosis()),
            },
            "tail": {
                "var": float(var),
                "es": float(es),
            },
            "scenarios": {
                "n_total": int(len(pnl)),
                "n_selected": len(selected),
            },
            "model": self.__class__.__name__,
        }

        if attribution:
            diag["attribution"] = attribution

        # optional drilldown
        diag["selected_scenarios"] = [
                {"pnl": s["pnl"]} for s in selected
        ]

        return diag


    # =====================================================
    # Risk measures
    # =====================================================

    def compute_var(self, pnl: pd.Series) -> float:
        q = np.quantile(pnl, self.confidence_level)
        return float(-q)

    def compute_es(self, pnl: pd.Series) -> float:
        q = np.quantile(pnl, self.confidence_level)
        tail = pnl[pnl <= q]
        return float(-tail.mean())


    # =====================================================
    # Scenario selection around VaR
    # =====================================================
    def _select_var_scenarios(
            self,
            pnl: pd.Series,
            scenarios: Sequence[Scenario],
    ) -> List[Dict[str, Any]]:
        
        q = np.quantile(pnl, self.confidence_level)

        df = pd.DataFrame({
            "pnl": pnl,
            "idx": np.arange(len(pnl)),
        }).sort_values("pnl")

        # tail (worse than Var)
        tail = df[pnl <= q].head(self.n_tail)

        # near-VaR above threshold
        near = df[df.pnl > q].head(self.n_var_near)

        selected = pd.concat([tail, near])

        result = []

        for _, r in selected.iterrows():
            i = int(r.idx)
            result.append({
                "scenario": scenarios[i],
                "pnl": float(r.pnl),
            })
            
        return result
    
    # =====================================================
    # Attribution
    # =====================================================

    def _compute_attribution(
            self,
            portfolio,
            base_scenario: Scenario,
            selected: List[Dict],
    ):
        
        pos_totals = {}
        factor_totals = {}

        for item in selected:
            s = item["scenario"]

            attr = portfolio.attribute_scenario(
                scenario=s,
                base_scenario=base_scenario,
            )

            print("Attr: ", attr)

            # Extract position totals
            for k, pos_attr in attr.get("positions", {}).items():
                total_pnl = pos_attr.get("total", 0.0)
                pos_totals[k] = pos_totals.get(k, 0.0) + total_pnl

            # Extract factor totals from portfolio-level factors
            for k, v in attr.get("portfolio", {}).get("factors", {}).items():
                factor_totals[k] = factor_totals.get(k, 0.0) + v
  
            # for k, v in attr.get("positions", {}).items():
            #     pos_totals[k] = pos_totals.get(k, 0.0) + v

            # for k, v in attr.get("factors", {}).items():
            #     factor_totals[k] = factor_totals.get(k, 0.0) + v

        n = len(selected)

        if n == 0:
            return None
        
        pos_avg = {k: v / n for k, v in pos_totals.items()}
        fac_avg = {k: v / n for k, v in factor_totals.items()}

        return {
            "component_var_positions": pos_avg,
            "component_var_factors": fac_avg,
            "n_scenarios": n,
        }



    def model_metadata(self) -> dict:
        """
        Optional metadata describing the model.
        Subclasses can extend this.
        """
        return {
            "model": self.__class__.__name__,
            # "confidence_level": self.confidence_level
        }