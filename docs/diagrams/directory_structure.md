```mermaid
graph TD
    var_backend["var-backend/src/var_engine"]
    methods["methods/variance_covariance"]
    api["api"]
    routers["api/routers"]
    schemas["api/schemas"]

    var_backend --> methods
    var_backend --> api

    api --> routers
    api --> schemas

    methods --> model_py["model.py (VarianceCovarianceVaR class)"]
    methods --> diagnostics_py["diagnostics.py"]
    methods --> assumptions_md["assumptions.md"]

    routers --> var_covar_py["var_covar.py (API endpoints)"]
    schemas --> var_covar_py_schema["var_covar.py (Pydantic schemas)"]
