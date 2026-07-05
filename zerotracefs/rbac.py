from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

logger = logging.getLogger(__name__)


class Role(Enum):
    OWNER = "OWNER"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"
    AUDITOR = "AUDITOR"


@dataclass
class UserContext:
    user_id: str
    role: Role
    hardware_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    geo_location: Optional[str] = None


class AccessControl:
    """Manages User to Document permissions mapping. (v1: Local Single/Multi-User Simulation)"""
    def __init__(self):
        # Maps filename -> {user_id -> Role}
        self._document_permissions: dict[str, dict[str, Role]] = {}
        
        # Maps user_id -> UserContext (simulated user database)
        self._users: dict[str, UserContext] = {
            "admin": UserContext("admin", Role.OWNER),
            "guest": UserContext("guest", Role.VIEWER),
        }
        
    def add_user(self, user: UserContext):
        self._users[user.user_id] = user

    def get_user(self, user_id: str) -> Optional[UserContext]:
        return self._users.get(user_id)

    def set_permission(self, filename: str, user_id: str, role: Role):
        if filename not in self._document_permissions:
            self._document_permissions[filename] = {}
        self._document_permissions[filename][user_id] = role

    def get_user_role_for_document(self, filename: str, user_id: str) -> Optional[Role]:
        """Gets the explicit role for a user on a document. Falls back to their global role if OWNER."""
        user = self.get_user(user_id)
        if user and user.role == Role.OWNER:
            return Role.OWNER
            
        doc_perms = self._document_permissions.get(filename, {})
        return doc_perms.get(user_id, user.role if user else None)

    def can_perform_action(self, filename: str, user_id: str, action: str) -> bool:
        """
        Check if user's role permits the action.
        Actions: 'read', 'write', 'delete', 'manage_permissions', 'audit'
        """
        role = self.get_user_role_for_document(filename, user_id)
        if not role:
            return False
            
        permissions_matrix = {
            Role.OWNER: ["read", "write", "delete", "manage_permissions", "audit"],
            Role.EDITOR: ["read", "write"],
            Role.VIEWER: ["read"],
            Role.AUDITOR: ["read", "audit"],
        }
        
        return action in permissions_matrix.get(role, [])
