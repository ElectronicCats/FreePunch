"""Configuration management for Checador."""

import os
from pathlib import Path
from typing import Optional

import toml
from pydantic import Field
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """Application settings."""
    device_id: str = "CHECADOR-001"
    data_dir: Path = Path("/var/lib/checador")
    host: str = "0.0.0.0"
    port: int = 8000


class CameraConfig(BaseSettings):
    """Camera settings."""
    device: str = "/dev/video0"
    width: int = 640
    height: int = 480
    fps: int = 30
    roi_x: int = 0
    roi_y: int = 0
    roi_width: int = 640
    roi_height: int = 480


class FingerprintConfig(BaseSettings):
    """Fingerprint processing settings."""
    nbis_mindtct: str = "/usr/local/bin/mindtct"
    nbis_bozorth3: str = "/usr/local/bin/bozorth3"
    match_threshold: int = 40
    enrollment_samples: int = 3
    min_quality_score: int = 20


class TimeclockConfig(BaseSettings):
    """Time clock logic settings."""
    antibounce_seconds: int = 10


class AdminConfig(BaseSettings):
    """Admin authentication settings."""
    password_hash: str


class ServerConfig(BaseSettings):
    """Server sync settings."""
    enabled: bool = False
    url: str = ""
    api_key: str = ""
    sync_interval_seconds: int = 300
    retry_max_attempts: int = 5
    retry_backoff_base: int = 2


class Config:
    """Master configuration class."""
    
    def __init__(self, config_path: str = "/etc/checador/config.toml"):
        self.config_path = Path(config_path)
        self._load_config()
    
    def _load_config(self):
        """Load configuration from TOML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Copy config.example.toml to {self.config_path}"
            )
        
        data = toml.load(self.config_path)
        
        self.app = AppConfig(**data.get("app", {}))
        self.camera = CameraConfig(**data.get("camera", {}))
        self.fingerprint = FingerprintConfig(**data.get("fingerprint", {}))
        self.timeclock = TimeclockConfig(**data.get("timeclock", {}))
        self.admin = AdminConfig(**data.get("admin", {}))
        self.server = ServerConfig(**data.get("server", {}))
        
        # Ensure data directories exist
        self.app.data_dir.mkdir(parents=True, exist_ok=True)
        (self.app.data_dir / "templates").mkdir(exist_ok=True)
        (self.app.data_dir / "temp").mkdir(exist_ok=True)
    
    def save(self):
        """Save current configuration back to file."""
        data = {
            "app": self.app.model_dump(),
            "camera": self.camera.model_dump(),
            "fingerprint": self.fingerprint.model_dump(),
            "timeclock": self.timeclock.model_dump(),
            "admin": self.admin.model_dump(),
            "server": self.server.model_dump(),
        }
        
        # Convert Path objects to strings
        for section in data.values():
            for key, value in section.items():
                if isinstance(value, Path):
                    section[key] = str(value)
        
        with open(self.config_path, "w") as f:
            toml.dump(data, f)
    
    @property
    def template_dir(self) -> Path:
        """Get template storage directory."""
        return self.app.data_dir / "templates"
    
    @property
    def temp_dir(self) -> Path:
        """Get temporary file directory."""
        return self.app.data_dir / "temp"
    
    @property
    def database_path(self) -> Path:
        """Get database file path."""
        return self.app.data_dir / "checador.db"


# Global config instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global config
    if config is None:
        config = Config()
    return config