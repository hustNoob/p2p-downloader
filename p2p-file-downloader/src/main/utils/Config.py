import json
import os
from typing import Any, Dict, Optional

class Config:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_default_config()
        self._load_config()

    def _load_default_config(self) -> Dict[str, Any]:
        return {
            "download": {
                "chunk_size": 1048576,
                "max_concurrent_downloads": 3,
                "timeout": 30,
                "retry_count": 3
            },
            "network": {
                "max_bandwidth": 0,
                "port": 8000,
                "heartbeat_interval": 5
            },
            "storage": {
                "download_path": "downloads",
                "temp_path": "temp"
            },
            "logging": {
                "level": "INFO",
                "file": "p2p_downloader.log",
                "max_size": 10485760,
                "backup_count": 5
            }
        }

    def _load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
        except Exception:
            self._save_config()

    def _save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config()

    def update(self, new_config: Dict[str, Any]):
        self.config.update(new_config)
        self._save_config()

    def reset(self):
        self.config = self._load_default_config()
        self._save_config()

    def get_all(self) -> Dict[str, Any]:
        return self.config.copy()
