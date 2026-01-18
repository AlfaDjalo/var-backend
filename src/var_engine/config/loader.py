import yaml
from pathlib import Path

class ConfigError(Exception):
    pass

class ConfigLoader:
    def __init__(self, config_path:str | Path):
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise ConfigError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, "r") as f:
            self._config = yaml.safe_load(f)

    @property
    def data_config(self) -> dict:
        if "data" not in self._config:
            raise ConfigError("Missing 'data' section in config")
        
        return self._config["data"]