from pathlib import Path
import os
import yaml

# -------------------------------------------------
# Resolve config path
# -------------------------------------------------

# Priority:
# 1. VAR_CONFIG_PATH env var (tests)
# 2. backend/config.yaml (normal runtime)

BACKEND_ROOT = Path(__file__).resolve().parents[1]

ENV_CONFIG_PATH = os.getenv("VAR_CONFIG_PATH")
DEFAULT_CONFIG_PATH = BACKEND_ROOT / "config" / "settings.yaml"
# DEFAULT_CONFIG_PATH = BACKEND_ROOT / "config.yaml"

CONFIG_PATH = Path(ENV_CONFIG_PATH) if ENV_CONFIG_PATH else DEFAULT_CONFIG_PATH

# -------------------------------------------------
# Load config (safe for tests)
# -------------------------------------------------

_config = {}

if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r") as f:
        _config = yaml.safe_load(f) or {}

# -------------------------------------------------
# Data config (safe defaults)
# -------------------------------------------------

DATA_CONFIG = _config.get("data", {})

DATA_SOURCE = DATA_CONFIG.get("source", "csv")

# IMPORTANT: DATA_PATH must ALWAYS be defined
_data_path = DATA_CONFIG.get("path")

DATA_PATH = (
    Path(_data_path)
    if _data_path is not None
    else None
)

DATE_COLUMN = DATA_CONFIG.get("date_column", "Date")
