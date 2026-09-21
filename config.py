"""
Backward compatibility config - now uses modern AppConfig
"""
from crowd_control.config import AppConfig, load_config, get_config, MAIL, url, ALERT, Threshold, Thread, Log, Scheduler, Timer

# For old code that does `import config` and accesses config.MAIL etc, we expose via module
# The actual values are loaded from AppConfig
import crowd_control.config as _modern
_cfg = _modern.load_config()

# Ensure module-level vars reflect loaded config
MAIL = _cfg.MAIL
url = _cfg.url
ALERT = _cfg.ALERT
Threshold = _cfg.Threshold
Thread = _cfg.Thread
Log = _cfg.Log
Scheduler = _cfg.Scheduler
Timer = _cfg.Timer

# Additional modern fields accessible
EMAIL_SENDER = _cfg.EMAIL_SENDER
EMAIL_PASSWORD = _cfg.EMAIL_PASSWORD
web_enabled = _cfg.web_enabled
web_port = _cfg.web_port
