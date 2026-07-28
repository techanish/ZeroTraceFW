from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from .rbac import AccessControl, UserContext, Role

logger = logging.getLogger(__name__)


@dataclass
class PolicyDecision:
    granted: bool
    reason: str
    risk_score: int
    require_mfa: bool = False


class PolicyEngine:
    def __init__(self, rbac: AccessControl):
        self.rbac = rbac

    def _check_time_policy(self, rules: dict) -> bool:
        if "allowed_hours" not in rules:
            return True
        allowed = rules["allowed_hours"]  # e.g. ["09:00-17:00"]
        now = datetime.now(timezone.utc)
        current_time_str = now.strftime("%H:%M")
        
        for time_range in allowed:
            start_str, end_str = time_range.split("-")
            if start_str <= current_time_str <= end_str:
                return True
        return False
        
    def _check_geo_fencing(self, rules: dict, user_context: UserContext) -> bool:
        if "geo_fence" not in rules or not rules["geo_fence"]:
            return True
            
        allowed_locations = rules["geo_fence"]
        if not user_context.geo_location:
            return False # Block if we require geo and none provided
            
        return user_context.geo_location in allowed_locations

    def evaluate(self, document_metadata: dict, user_context: UserContext, action: str = "read") -> PolicyDecision:
        filename = document_metadata.get("filename", "unknown")
        
        # 1. Base RBAC Check
        if not self.rbac.can_perform_action(filename, user_context.user_id, action):
            return PolicyDecision(granted=False, reason="Insufficient role permissions", risk_score=80)
            
        # 2. Advanced Policy Checks
        access_policy = document_metadata.get("access_policy", {})
        
        if not self._check_time_policy(access_policy):
            return PolicyDecision(granted=False, reason="Access denied by time-of-day restrictions", risk_score=50)
            
        if not self._check_geo_fencing(access_policy, user_context):
            return PolicyDecision(granted=False, reason="Access denied by geo-fencing restrictions", risk_score=60)
            
        # 3. Dynamic Risk Scoring
        risk_score = 0
        if document_metadata.get("classification_level") == "secret":
            risk_score += 30
        if user_context.ip_address and not user_context.ip_address.startswith("10.") and not user_context.ip_address.startswith("192.168."):
            risk_score += 20 # External IP
            
        require_mfa = False
        if risk_score >= 50 or access_policy.get("require_mfa", False):
            require_mfa = True
            
        return PolicyDecision(granted=True, reason="Policy checks passed", risk_score=risk_score, require_mfa=require_mfa)
