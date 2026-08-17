from __future__ import annotations

import logging
from typing import Literal

try:
    from plyer import notification
    _HAS_PLYER = True
except ImportError:
    _HAS_PLYER = False

logger = logging.getLogger(__name__)

NotificationLevel = Literal["info", "warning", "critical"]


class NotificationEngine:
    def __init__(self, app_name: str = "ZeroTraceFW") -> None:
        self.app_name = app_name

    def notify(self, title: str, message: str, level: NotificationLevel = "info") -> bool:
        """Sends a desktop notification to the document owner."""
        logger.info(f"NOTIFICATION [{level.upper()}]: {title} - {message}")
        
        if not _HAS_PLYER:
            logger.warning("Plyer not installed. Cannot send desktop notification.")
            return False

        # Timeout in seconds based on severity
        timeout = {
            "info": 5,
            "warning": 10,
            "critical": 20
        }.get(level, 5)

        try:
            from pathlib import Path
            import sys
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent.resolve()
            else:
                base_dir = Path(__file__).parent.parent.resolve()
            logo = base_dir / "logo.png"
            icon_arg = str(logo) if logo.exists() else None

            notification.notify(
                title=f"{self.app_name} - {title}",
                message=message,
                app_name=self.app_name,
                app_icon=icon_arg,
                timeout=timeout,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send desktop notification: {e}")
            return False

    def notify_security_event(self, event_type: str, details: str) -> bool:
        """Helper for high-priority security alerts (e.g. debugger detected, duress)."""
        return self.notify(
            title=f"Security Alert: {event_type}",
            message=details,
            level="critical"
        )

    def notify_policy_violation(self, document_name: str, reason: str) -> bool:
        """Helper for access policy violations."""
        return self.notify(
            title="Access Denied",
            message=f"Access to '{document_name}' blocked: {reason}",
            level="warning"
        )
