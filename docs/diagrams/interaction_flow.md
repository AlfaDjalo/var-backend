```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend

    User->>Frontend: Select data file, adjust config
    Frontend->>Backend: Request available datasets/config (optional)
    Backend-->>Frontend: Send datasets/config options

    User->>Frontend: Trigger VaR calculation with selected options
    Frontend->>Backend: POST /var-covar/calculate (dataset, weights, config)
    Backend->>Backend: Load data, calculate VaR
    Backend-->>Frontend: Return VaR results JSON

    Frontend->>User: Display VaR results and diagnostics
