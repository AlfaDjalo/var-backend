```mermaid
graph TD
    A[ConfigLoader] --> B[CSVPriceLoader]
    B --> C["Load CSV file (path)"]
    C --> D[Return DataFrame of prices]
    D --> E[Calculate log returns DataFrame]
    E --> F[Return returns DataFrame]
