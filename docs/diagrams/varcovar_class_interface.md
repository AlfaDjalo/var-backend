```mermaid
classDiagram
    class VarianceCovarianceVaR {
        - float confidence_level = 0.01
        - int cov_window_days = 252
        - Callable cov_estimator
        + __init__(confidence_level, cov_window_days, cov_estimator)
        + calculate_var(portfolio) Dict
    }

    class Portfolio {
        - pd.DataFrame returns
        - pd.Series exposures
        + __init__(returns, weights)
        + calculate_exposures()
    }

    VarianceCovarianceVaR ..> Portfolio : uses
