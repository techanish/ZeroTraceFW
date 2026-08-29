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
        """Logs security events without triggering OS desktop notifications."""
        logger.info(f"NOTIFICATION [{level.upper()}]: {title} - {message}")
        # Desktop notification toasts disabled per configuration
        return True

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
