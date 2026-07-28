import sqlite3
import time
import secrets
import logging
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ztfs_server")

app = FastAPI(title="ZeroTraceFW Central Command")

DB_PATH = "central_vault.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vaults (
                vault_id TEXT PRIMARY KEY,
                master_hash TEXT NOT NULL,
                duress_hash TEXT NOT NULL,
                key_block TEXT NOT NULL,
                failed_attempts INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 5,
                is_locked BOOLEAN DEFAULT FALSE,
                global_ttl_seconds INTEGER,
                system_start_time REAL,
                last_heartbeat REAL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_token TEXT PRIMARY KEY,
                vault_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                hardware_fingerprint TEXT,
                ip_address TEXT
            )
        ''')

init_db()

class SetupRequest(BaseModel):
    vault_id: str
    master_hash: str
    duress_hash: str
    key_block: str
    max_attempts: int = 5
    global_ttl_seconds: Optional[int] = None

class AuthRequest(BaseModel):
    vault_id: str
    password_hash: str
    hardware_fingerprint: str

class HeartbeatRequest(BaseModel):
    session_token: str

@app.post("/api/v1/vault/setup")
def setup_vault(req: SetupRequest):
    with get_db() as conn:
        cur = conn.execute("SELECT vault_id FROM vaults WHERE vault_id = ?", (req.vault_id,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Vault already exists")
        
        now = time.time()
        conn.execute('''
            INSERT INTO vaults 
            (vault_id, master_hash, duress_hash, key_block, max_attempts, global_ttl_seconds, system_start_time, last_heartbeat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (req.vault_id, req.master_hash, req.duress_hash, req.key_block, req.max_attempts, req.global_ttl_seconds, now, now))
    return {"status": "success", "vault_id": req.vault_id}

@app.post("/api/v1/vault/auth")
def auth_vault(req: AuthRequest, request: Request):
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM vaults WHERE vault_id = ?", (req.vault_id,))
        vault = cur.fetchone()
        if not vault:
            raise HTTPException(status_code=404, detail="Vault not found")

        if vault['is_locked']:
            raise HTTPException(status_code=403, detail="Vault is locked due to security policy")

        now = time.time()
        
        # Check global TTL
        if vault['global_ttl_seconds']:
            uptime = now - vault['system_start_time']
            if uptime > vault['global_ttl_seconds']:
                conn.execute("UPDATE vaults SET is_locked = TRUE WHERE vault_id = ?", (req.vault_id,))
                logger.warning(f"Vault {req.vault_id} globally expired")
                raise HTTPException(status_code=403, detail="Global vault TTL expired")

        # Master Auth
        if req.password_hash == vault['master_hash']:
            conn.execute("UPDATE vaults SET failed_attempts = 0, last_heartbeat = ? WHERE vault_id = ?", (now, req.vault_id))
            session_token = secrets.token_hex(32)
            expires_at = now + 3600 # 1 hour session
            conn.execute('''
                INSERT INTO sessions (session_token, vault_id, created_at, expires_at, hardware_fingerprint, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_token, req.vault_id, now, expires_at, req.hardware_fingerprint, request.client.host))
            logger.info(f"Vault {req.vault_id} authenticated successfully")
            return {
                "status": "granted",
                "session_token": session_token,
                "key_block": vault['key_block']
            }
        
        # Duress Auth
        if req.password_hash == vault['duress_hash']:
            # Simulates success to adversary, but effectively burns the vault on the server
            conn.execute("UPDATE vaults SET key_block = 'DURESS_WIPED', is_locked = TRUE WHERE vault_id = ?", (req.vault_id,))
            logger.critical(f"DURESS TRIGGERED on Vault {req.vault_id}")
            return {"status": "duress"}

        # Failed attempt
        failed_attempts = vault['failed_attempts'] + 1
        is_locked = failed_attempts >= vault['max_attempts']
        conn.execute("UPDATE vaults SET failed_attempts = ?, is_locked = ? WHERE vault_id = ?", 
                    (failed_attempts, is_locked, req.vault_id))
        
        if is_locked:
            logger.warning(f"Vault {req.vault_id} LOCKED due to brute force")
            raise HTTPException(status_code=403, detail="Lockout triggered")
        else:
            logger.info(f"Failed auth on Vault {req.vault_id}")
            raise HTTPException(status_code=401, detail="Authentication failed")

@app.post("/api/v1/vault/heartbeat")
def heartbeat(req: HeartbeatRequest):
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM sessions WHERE session_token = ?", (req.session_token,))
        session = cur.fetchone()
        if not session:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        now = time.time()
        if now > session['expires_at']:
            conn.execute("DELETE FROM sessions WHERE session_token = ?", (req.session_token,))
            raise HTTPException(status_code=401, detail="Session expired")
            
        cur = conn.execute("SELECT * FROM vaults WHERE vault_id = ?", (session['vault_id'],))
        vault = cur.fetchone()
        if vault['is_locked']:
            raise HTTPException(status_code=403, detail="Vault is locked")

        if vault['global_ttl_seconds']:
            uptime = now - vault['system_start_time']
            if uptime > vault['global_ttl_seconds']:
                conn.execute("UPDATE vaults SET is_locked = TRUE WHERE vault_id = ?", (vault['vault_id'],))
                raise HTTPException(status_code=403, detail="Global vault TTL expired")
                
        conn.execute("UPDATE vaults SET last_heartbeat = ? WHERE vault_id = ?", (now, session['vault_id']))
        return {"status": "active", "server_time": now}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
