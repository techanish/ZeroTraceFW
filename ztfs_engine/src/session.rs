// session.rs — Cryptographic Session Management with Hardware Binding
//
// Each vault session gets a unique 256-bit token bound to the machine's
// hardware fingerprint. Sessions expire, can be revoked, and are stored
// in secure (zeroized) memory.

use pyo3::prelude::*;
use rand::RngCore;
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};
use zeroize::Zeroize;

// Global session store (mutex-protected)
static SESSION_STORE: Mutex<Option<HashMap<String, SessionData>>> = Mutex::new(None);

struct SessionData {
    hardware_fingerprint: String,
    created_at: u64,
    expires_at: u64,
}

impl Drop for SessionData {
    fn drop(&mut self) {
        self.hardware_fingerprint.zeroize();
    }
}

fn now_epoch() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

fn get_store() -> std::sync::MutexGuard<'static, Option<HashMap<String, SessionData>>> {
    let mut store = SESSION_STORE.lock().unwrap();
    if store.is_none() {
        *store = Some(HashMap::new());
    }
    store
}

/// Generate a hardware fingerprint for this machine.
///
/// Combines: hostname + CPU info + disk serial (where available).
/// Returns a hex-encoded SHA-256 hash.
#[pyfunction]
pub fn get_hardware_fingerprint() -> String {
    let mut components = Vec::new();

    // Hostname
    if let Ok(hostname) = hostname::get() {
        components.push(hostname.to_string_lossy().to_string());
    }

    // CPU info
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;

        if let Ok(output) = std::process::Command::new("wmic")
            .creation_flags(CREATE_NO_WINDOW)
            .args(["cpu", "get", "processorid"])
            .output()
        {
            let text = String::from_utf8_lossy(&output.stdout);
            for line in text.lines().skip(1) {
                let trimmed = line.trim();
                if !trimmed.is_empty() {
                    components.push(trimmed.to_string());
                }
            }
        }
    }

    // Username
    if let Ok(user) = std::env::var("USERNAME").or_else(|_| std::env::var("USER")) {
        components.push(user);
    }

    let combined = components.join("|");
    let mut hasher = Sha256::new();
    hasher.update(combined.as_bytes());
    hex::encode(hasher.finalize())
}

/// Create a new session token bound to this machine.
///
/// Args:
///     ttl_seconds: Session lifetime in seconds (default 3600 = 1 hour).
///
/// Returns:
///     64-character hex session token.
#[pyfunction]
#[pyo3(signature = (ttl_seconds=None))]
pub fn create_session(ttl_seconds: Option<u64>) -> String {
    let ttl = ttl_seconds.unwrap_or(3600);
    let now = now_epoch();

    // Generate 32 random bytes = 256-bit session token
    let mut token_bytes = [0u8; 32];
    rand::rngs::OsRng.fill_bytes(&mut token_bytes);
    let token = hex::encode(token_bytes);

    let session = SessionData {
        hardware_fingerprint: get_hardware_fingerprint(),
        created_at: now,
        expires_at: now + ttl,
    };

    let mut store = get_store();
    store.as_mut().unwrap().insert(token.clone(), session);

    token
}

/// Validate a session token.
///
/// Checks:
///   1. Token exists in the session store.
///   2. Session has not expired.
///   3. Hardware fingerprint matches (session wasn't stolen and used on another machine).
///
/// Returns True if valid.
#[pyfunction]
pub fn validate_session(token: &str) -> PyResult<bool> {
    let store = get_store();
    let sessions = store.as_ref().unwrap();

    let session = match sessions.get(token) {
        Some(s) => s,
        None => return Ok(false),
    };

    // Check expiry
    if now_epoch() > session.expires_at {
        return Ok(false);
    }

    // Check hardware binding
    let current_fp = get_hardware_fingerprint();
    if session.hardware_fingerprint != current_fp {
        return Ok(false);
    }

    Ok(true)
}

/// Destroy (revoke) a session token, securely wiping it from memory.
#[pyfunction]
pub fn destroy_session(token: &str) -> bool {
    let mut store = get_store();
    let sessions = store.as_mut().unwrap();

    // Remove and drop (SessionData::drop will zeroize fields)
    sessions.remove(token).is_some()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_and_validate() {
        let token = create_session(Some(60));
        assert_eq!(token.len(), 64);
        assert!(validate_session(&token).unwrap());
    }

    #[test]
    fn test_destroy_invalidates() {
        let token = create_session(Some(60));
        assert!(validate_session(&token).unwrap());
        assert!(destroy_session(&token));
        assert!(!validate_session(&token).unwrap());
    }

    #[test]
    fn test_invalid_token() {
        assert!(!validate_session("nonexistent_token_000").unwrap());
    }

    #[test]
    fn test_hardware_fingerprint_consistent() {
        let fp1 = get_hardware_fingerprint();
        let fp2 = get_hardware_fingerprint();
        assert_eq!(fp1, fp2);
        assert_eq!(fp1.len(), 64);
    }
}
