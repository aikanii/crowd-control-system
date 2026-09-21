"""
Configuration - Modern config management with env vars, yaml, and dataclass
"""
import os
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    # Email alerts
    MAIL: str = ""  # recipient email
    EMAIL_SENDER: str = ""  # sender email
    EMAIL_PASSWORD: str = ""  # app password
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    ALERT: bool = False
    ALERT_COOLDOWN: int = 60  # seconds between alerts

    # Camera / Video
    url: str = ""  # ip camera url
    camera_id: int = 0  # webcam id
    input_path: Optional[str] = None
    output_path: Optional[str] = None

    # Counting logic
    Threshold: int = 10
    max_disappeared: int = 40
    max_distance: int = 50
    confidence: float = 0.4
    skip_frames: int = 30
    line_position_ratio: float = 0.5  # 0.5 = middle of frame

    # Features
    Thread: bool = True  # Enable threading by default now
    Log: bool = True
    Scheduler: bool = False
    Timer: bool = False
    timer_seconds: int = 28800  # 8 hours
    schedule_time: str = "09:00"

    # Detection
    prototxt: Optional[str] = None
    model: Optional[str] = None
    detector_type: str = "mobilenet"  # mobilenet, hog, yolo
    use_dlib: bool = True  # try dlib if available

    # Web UI
    web_enabled: bool = True
    web_host: str = "0.0.0.0"
    web_port: int = 5000
    web_debug: bool = False

    # Logging
    log_file: str = "Log.csv"
    log_json: str = "occupancy_log.json"
    verbose: bool = True

    # Advanced
    webhook_url: str = ""  # optional webhook for alerts
    occupancy_history_size: int = 1000

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        # Filter only known fields
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load config from environment variables"""
        cfg = cls()
        # Map env vars
        env_map = {
            "MAIL": "MAIL",
            "EMAIL_SENDER": "EMAIL_SENDER",
            "EMAIL_PASSWORD": "EMAIL_PASSWORD",
            "CROWD_THRESHOLD": "Threshold",
            "CROWD_CAMERA_URL": "url",
            "CROWD_ALERT": "ALERT",
            "CROWD_WEB_PORT": "web_port",
            "CROWD_INPUT": "input_path",
            "CROWD_OUTPUT": "output_path",
        }
        for env_key, attr in env_map.items():
            if env_key in os.environ:
                val = os.environ[env_key]
                # Try to cast to original type
                orig_type = type(getattr(cfg, attr))
                try:
                    if orig_type == bool:
                        setattr(cfg, attr, val.lower() in ("1", "true", "yes"))
                    elif orig_type == int:
                        setattr(cfg, attr, int(val))
                    elif orig_type == float:
                        setattr(cfg, attr, float(val))
                    else:
                        setattr(cfg, attr, val)
                except Exception as e:
                    logger.warning(f"Failed to parse env {env_key}: {e}")
        return cfg

    def save_json(self, path: str = "config.json"):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, path: str = "config.json") -> "AppConfig":
        if not os.path.exists(path):
            return cls()
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load config from {path}: {e}")
            return cls()


# Global default config instance (for backward compatibility with old code that does `import config`)
_default_config = AppConfig.from_env()

# Expose attributes at module level for backward compatibility
# So `config.MAIL`, `config.Threshold` etc work
MAIL = _default_config.MAIL
url = _default_config.url
ALERT = _default_config.ALERT
Threshold = _default_config.Threshold
Thread = _default_config.Thread
Log = _default_config.Log
Scheduler = _default_config.Scheduler
Timer = _default_config.Timer

def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load config from file + env, env takes precedence"""
    cfg = AppConfig()
    if config_path and os.path.exists(config_path):
        if config_path.endswith(".json"):
            cfg = AppConfig.load_json(config_path)
        else:
            # Try json anyway
            try:
                cfg = AppConfig.load_json(config_path)
            except:
                pass
    # Override with env
    env_cfg = AppConfig.from_env()
    # Merge env over file where env has non-default? Simpler: just use env values if set
    for key in os.environ:
        # already handled in from_env, but we need to merge
        pass

    # For simplicity, if env var exists, use env_cfg
    # Actually load again and merge
    final_cfg = AppConfig.from_dict({**cfg.to_dict(), **env_cfg.to_dict()}) if os.environ else cfg

    # Also check for config.json in cwd
    if not config_path and os.path.exists("config.json"):
        try:
            file_cfg = AppConfig.load_json("config.json")
            # Merge file_cfg with env
            merged = {**file_cfg.to_dict(), **AppConfig.from_env().to_dict()}
            # But only override file if env var was actually set
            # So we need smarter: only env vars that were set
            # For now, just use file_cfg as base and override with env if env var present
            final_cfg = file_cfg
            for env_key in ["MAIL", "EMAIL_SENDER", "EMAIL_PASSWORD", "CROWD_THRESHOLD", "CROWD_CAMERA_URL", "CROWD_ALERT", "CROWD_WEB_PORT", "CROWD_INPUT", "CROWD_OUTPUT"]:
                if env_key in os.environ:
                    # re-parse that single env
                    attr_map = {
                        "MAIL": "MAIL",
                        "EMAIL_SENDER": "EMAIL_SENDER",
                        "EMAIL_PASSWORD": "EMAIL_PASSWORD",
                        "CROWD_THRESHOLD": "Threshold",
                        "CROWD_CAMERA_URL": "url",
                        "CROWD_ALERT": "ALERT",
                        "CROWD_WEB_PORT": "web_port",
                        "CROWD_INPUT": "input_path",
                        "CROWD_OUTPUT": "output_path",
                    }
                    attr = attr_map[env_key]
                    setattr(final_cfg, attr, getattr(env_cfg, attr))
        except Exception:
            pass

    return final_cfg

def get_config() -> AppConfig:
    return load_config()
