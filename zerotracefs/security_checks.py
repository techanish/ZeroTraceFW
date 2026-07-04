from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Literal

try:
    import ztfs_engine
    _HAS_ZTFS_ENGINE = True
except ImportError:
    _HAS_ZTFS_ENGINE = False


logger = logging.getLogger(__name__)

PolicyAction = Literal["warn", "block", "destroy"]


@dataclass
class SecurityReport:
    is_secure: bool
    debugger_detected: bool
    vm_detected: bool
    os_integrity_score: int
    tamper_score: int
    warnings: list[str]


class EnvironmentVerifier:
    def __init__(self, policy: PolicyAction = "warn") -> None:
        self.policy: PolicyAction = policy

    def verify_environment(self) -> SecurityReport:
        if not _HAS_ZTFS_ENGINE:
            logger.warning("Rust security engine not available. Environment verification is limited.")
            return SecurityReport(
                is_secure=True,
                debugger_detected=False,
                vm_detected=False,
                os_integrity_score=100,
                tamper_score=0,
                warnings=["Rust security engine missing."]
            )

        warnings = []
        is_secure = True

        # Debugger Check
        try:
            debug_info = json.loads(ztfs_engine.full_debug_check())
            debugger_detected = debug_info.get("debugger_attached", False)
            if debugger_detected:
                warnings.append("Debugger detected!")
                is_secure = False
        except Exception as e:
            logger.error(f"Debugger check failed: {e}")
            debugger_detected = False
            warnings.append("Failed to perform debugger check.")
            is_secure = False

        # VM Check
        try:
            vm_info = json.loads(ztfs_engine.get_vm_indicators())
            vm_detected = vm_info.get("is_vm", False)
            if vm_detected:
                warnings.append("Virtual Machine environment detected.")
                is_secure = False
        except Exception as e:
            logger.error(f"VM check failed: {e}")
            vm_detected = False
            warnings.append("Failed to perform VM check.")
            is_secure = False

        # OS Integrity
        try:
            os_info = json.loads(ztfs_engine.check_os_integrity())
            os_integrity_score = os_info.get("integrity_score", 100)
            if os_integrity_score < 70:
                is_secure = False
            warnings.extend(os_info.get("warnings", []))
        except Exception as e:
            logger.error(f"OS integrity check failed: {e}")
            os_integrity_score = 0
            warnings.append("Failed to perform OS integrity check.")
            is_secure = False

        # Tamper Detection
        try:
            tamper_info = json.loads(ztfs_engine.check_tamper())
            tamper_score = tamper_info.get("tamper_score", 0)
            if tamper_score > 30:
                is_secure = False
            warnings.extend(tamper_info.get("warnings", []))
        except Exception as e:
            logger.error(f"Tamper check failed: {e}")
            tamper_score = 100
            warnings.append("Failed to perform tamper check.")
            is_secure = False

        return SecurityReport(
            is_secure=is_secure,
            debugger_detected=debugger_detected,
            vm_detected=vm_detected,
            os_integrity_score=os_integrity_score,
            tamper_score=tamper_score,
            warnings=warnings
        )
