```mermaid
graph TD
    A["Frontend (React)"] -->|API Requests| B["Backend API (FastAPI)"]
    B --> C[Var Engine]
    C --> D[Portfolio Class]
    C --> E[VarianceCovarianceVaR Class]
    D -->|Uses returns data| F["Data Loader (CSVPriceLoader)"]
