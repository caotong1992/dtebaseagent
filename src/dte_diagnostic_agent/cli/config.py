"""Configuration management for dte-diag CLI tool."""

import os
from pathlib import Path
from typing import Any

import yaml

from pydantic import BaseModel, Field


class APIConfig(BaseModel):
    url: str = "http://localhost:8080"
    key: str | None = None
    timeout: int = 300


class DefaultsConfig(BaseModel):
    cluster: str | None = None
    service: str = "DTEBaseService"
    output: str = "table"
    priority: str = "medium"


class AuthConfig(BaseModel):
    ssh_key_path: str | None = None
    username: str | None = None


class LoggingConfig(BaseModel):
    level: str = "info"
    file: str | None = None


class Config(BaseModel):
    api: APIConfig = Field(default_factory=APIConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


DEFAULT_CONFIG_PATH = Path.home() / ".dte-diag" / "config.yaml"


class ConfigManager:
    """Configuration manager for dte-diag CLI."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._config: Config | None = None

    def load(self) -> Config:
        if self._config is not None:
            return self._config

        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            self._config = Config(**data)
        else:
            self._config = Config()

        return self._config

    def save(self, config: Config) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(config.model_dump(exclude_none=True), f, default_flow_style=False)
        self._config = config

    def get(self, key: str) -> Any:
        config = self.load()
        keys = key.split(".")
        obj: Any = config
        for k in keys:
            if hasattr(obj, k):
                obj = getattr(obj, k)
            else:
                return None
        return obj

    def set(self, key: str, value: Any) -> None:
        config = self.load()
        keys = key.split(".")
        obj: Any = config
        for k in keys[:-1]:
            if hasattr(obj, k):
                obj = getattr(obj, k)

        final_key = keys[-1]
        if hasattr(obj, final_key):
            setattr(obj, final_key, value)
            self.save(config)

    def init_config(self, api_url: str | None = None, api_key: str | None = None) -> None:
        config = Config()
        if api_url:
            config.api.url = api_url
        if api_key:
            config.api.key = api_key
        self.save(config)

    @staticmethod
    def get_default_config_path() -> Path:
        return DEFAULT_CONFIG_PATH

    @staticmethod
    def ensure_config_dir() -> Path:
        config_dir = Path.home() / ".dte-diag"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir