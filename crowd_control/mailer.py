"""
Mailer - Robust email alert system with fallback and webhook support
"""
import smtplib
import ssl
import logging
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class Mailer:
    """
    Email alert system with cooldown and error handling
    """

    def __init__(self, email: str = "", password: str = "", smtp_server: str = "smtp.gmail.com", port: int = 465, sender: str = ""):
        # Try to load from env or config if not provided
        self.EMAIL = email or os.getenv("EMAIL_SENDER", "")
        self.PASS = password or os.getenv("EMAIL_PASSWORD", "")
        self.SENDER = sender or self.EMAIL or os.getenv("EMAIL_SENDER", "")
        self.SMTP_SERVER = smtp_server
        self.PORT = port
        self.last_sent = 0
        self.cooldown = 60  # seconds

        if not self.EMAIL:
            logger.warning("Mailer: No sender email configured. Set EMAIL_SENDER env var or pass email param.")
        if not self.PASS:
            logger.warning("Mailer: No email password configured. Email alerts will fail without it.")

    def can_send(self) -> bool:
        """Check cooldown"""
        now = time.time()
        if now - self.last_sent < self.cooldown:
            logger.info(f"Mailer: Cooldown active, {self.cooldown - (now - self.last_sent):.1f}s remaining")
            return False
        return True

    def send(self, recipient: str, subject: str = "ALERT! People limit exceeded", body: str = None, threshold: int = None, current_count: int = None) -> bool:
        """
        Send email alert
        Returns True if sent, False otherwise
        """
        if not recipient:
            logger.error("Mailer: No recipient email provided")
            return False

        if not self.EMAIL or not self.PASS:
            logger.error("Mailer: Sender email or password not configured")
            return False

        if not self.can_send():
            return False

        if body is None:
            body = f"""Alert: People limit exceeded in your building!

Threshold: {threshold if threshold is not None else 'N/A'}
Current occupancy: {current_count if current_count is not None else 'N/A'}
Time: {time.strftime('%Y-%m-%d %H:%M:%S')}

Please take necessary action.

- Crowd Control System
"""

        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = self.SENDER
            message["To"] = recipient
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.SMTP_SERVER, self.PORT, context=context) as server:
                server.login(self.EMAIL, self.PASS)
                server.sendmail(self.SENDER, recipient, message.as_string())

            self.last_sent = time.time()
            logger.info(f"Alert email sent to {recipient}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_webhook(self, webhook_url: str, data: dict) -> bool:
        """Send alert via webhook (Slack, Discord, custom)"""
        if not webhook_url:
            return False
        if not HAS_REQUESTS:
            logger.warning("requests library not available for webhook")
            return False
        try:
            resp = requests.post(webhook_url, json=data, timeout=10)
            logger.info(f"Webhook sent, status {resp.status_code}")
            return resp.status_code in (200, 201, 204)
        except Exception as e:
            logger.error(f"Webhook failed: {e}")
            return False

    def alert(self, recipient: str, current_count: int, threshold: int, webhook_url: str = "") -> bool:
        """High-level alert that tries email and webhook"""
        sent = False
        # Email
        if recipient:
            sent = self.send(recipient, current_count=current_count, threshold=threshold) or sent
        # Webhook
        if webhook_url:
            data = {
                "text": f"🚨 Crowd Alert: Occupancy {current_count} exceeded threshold {threshold}",
                "occupancy": current_count,
                "threshold": threshold,
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "alert": "people_limit_exceeded"
            }
            sent = self.send_webhook(webhook_url, data) or sent

        if not sent and not recipient and not webhook_url:
            # Fallback to console alert
            logger.warning(f"🚨 ALERT: People limit exceeded! Count: {current_count}, Threshold: {threshold}")
            print(f"\n{'='*60}\n🚨 ALERT: People limit exceeded!\nCurrent: {current_count} | Threshold: {threshold}\n{'='*60}\n")
            return True

        return sent
