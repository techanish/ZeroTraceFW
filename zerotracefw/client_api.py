import requests
import hashlib
from typing import Optional, Dict, Any

class ServerClient:
    def __init__(self, server_url: str = "http://127.0.0.1:8000"):
        self.server_url = server_url.rstrip("/")
        self.session_token: Optional[str] = None
        self.key_block: Optional[str] = None

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def setup_vault(self, vault_id: str, master_password: str, duress_password: str, global_ttl_seconds: Optional[int] = None) -> bool:
        master_hash = self.hash_password(master_password)
        duress_hash = self.hash_password(duress_password)
        
        payload = {
            "vault_id": vault_id,
            "master_hash": master_hash,
            "duress_hash": duress_hash,
            "key_block": "ENCRYPTED_KEY_BLOCK_PLACEHOLDER", # In reality this would be an encrypted symmetric key
            "global_ttl_seconds": global_ttl_seconds
        }
        resp = requests.post(f"{self.server_url}/api/v1/vault/setup", json=payload)
        if resp.status_code == 200:
            return True
        raise Exception(resp.json().get("detail", "Failed to setup vault"))

    def authenticate(self, vault_id: str, password: str, hardware_fingerprint: str = "local_machine") -> Dict[str, Any]:
        password_hash = self.hash_password(password)
        payload = {
            "vault_id": vault_id,
            "password_hash": password_hash,
            "hardware_fingerprint": hardware_fingerprint
        }
        resp = requests.post(f"{self.server_url}/api/v1/vault/auth", json=payload)
        
        if resp.status_code == 200:
            data = resp.json()
            if data["status"] == "granted":
                self.session_token = data["session_token"]
                self.key_block = data["key_block"]
            return data
        elif resp.status_code == 403:
            return {"status": "lockout", "detail": resp.json().get("detail")}
        else:
            return {"status": "denied", "detail": resp.json().get("detail")}

    def heartbeat(self) -> Dict[str, Any]:
        if not self.session_token:
            return {"status": "error", "detail": "No active session"}
            
        payload = {"session_token": self.session_token}
        resp = requests.post(f"{self.server_url}/api/v1/vault/heartbeat", json=payload)
        
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 403:
            return {"status": "lockout", "detail": resp.json().get("detail")}
        else:
            self.session_token = None
            return {"status": "expired", "detail": resp.json().get("detail")}
