// key_derivation.rs — PBKDF2-HMAC-SHA256 Key Stretching
//
// Derives cryptographic keys from human-memorable passwords.
// Default: 600,000 iterations (OWASP 2024 recommendation).
// All derived keys wrapped in Zeroizing<> — wiped on drop.

use hmac::Hmac;
use pbkdf2::pbkdf2;
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use rand::RngCore;
use sha2::Sha256;
use subtle::ConstantTimeEq;
use zeroize::Zeroizing;

type HmacSha256 = Hmac<Sha256>;

const DEFAULT_ITERATIONS: u32 = 600_000;
const KEY_LENGTH: usize = 32;
const SALT_LENGTH: usize = 32;

/// Derive a 32-byte key from a password using PBKDF2-HMAC-SHA256.
///
/// Args:
///     password: UTF-8 password string.
///     salt: Random salt bytes (32 bytes recommended).
///     iterations: Number of PBKDF2 rounds (default 600,000).
///
/// Returns:
///     32-byte derived key.
#[pyfunction]
#[pyo3(signature = (password, salt, iterations=None))]
pub fn derive_key_pbkdf2(
    password: &str,
    salt: &[u8],
    iterations: Option<u32>,
) -> PyResult<Vec<u8>> {
    if password.is_empty() {
        return Err(PyValueError::new_err("Password must not be empty."));
    }
    if salt.is_empty() {
        return Err(PyValueError::new_err("Salt must not be empty."));
    }

    let iters = iterations.unwrap_or(DEFAULT_ITERATIONS);
    if iters == 0 {
        return Err(PyValueError::new_err("Iterations must be positive."));
    }

    let mut derived = Zeroizing::new([0u8; KEY_LENGTH]);
    pbkdf2::<HmacSha256>(password.as_bytes(), salt, iters, derived.as_mut())
        .map_err(|e| PyValueError::new_err(format!("PBKDF2 failed: {e}")))?;

    Ok(derived.to_vec())
}

/// Generate a cryptographically secure 32-byte salt.
#[pyfunction]
pub fn generate_salt() -> Vec<u8> {
    let mut salt = [0u8; SALT_LENGTH];
    rand::rngs::OsRng.fill_bytes(&mut salt);
    salt.to_vec()
}

/// Hash a password with SHA-256 for storage comparison.
/// Returns hex-encoded hash string.
#[pyfunction]
pub fn hash_password(password: &str) -> String {
    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(password.as_bytes());
    hex::encode(hasher.finalize())
}

/// Verify a password against a stored hex-encoded SHA-256 hash.
/// Uses constant-time comparison to prevent timing attacks.
#[pyfunction]
pub fn verify_password(password: &str, stored_hash: &str) -> bool {
    let candidate = hash_password(password);
    let candidate_bytes = candidate.as_bytes();
    let stored_bytes = stored_hash.as_bytes();

    if candidate_bytes.len() != stored_bytes.len() {
        return false;
    }

    candidate_bytes.ct_eq(stored_bytes).into()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_derive_key_deterministic() {
        let salt = generate_salt();
        let key1 = derive_key_pbkdf2("hunter2", &salt, Some(1000)).unwrap();
        let key2 = derive_key_pbkdf2("hunter2", &salt, Some(1000)).unwrap();
        assert_eq!(key1, key2);
    }

    #[test]
    fn test_different_passwords_different_keys() {
        let salt = generate_salt();
        let key1 = derive_key_pbkdf2("password1", &salt, Some(1000)).unwrap();
        let key2 = derive_key_pbkdf2("password2", &salt, Some(1000)).unwrap();
        assert_ne!(key1, key2);
    }

    #[test]
    fn test_different_salts_different_keys() {
        let salt1 = generate_salt();
        let salt2 = generate_salt();
        let key1 = derive_key_pbkdf2("same_pass", &salt1, Some(1000)).unwrap();
        let key2 = derive_key_pbkdf2("same_pass", &salt2, Some(1000)).unwrap();
        assert_ne!(key1, key2);
    }

    #[test]
    fn test_hash_and_verify() {
        let hash = hash_password("s3cret!");
        assert!(verify_password("s3cret!", &hash));
        assert!(!verify_password("wrong", &hash));
    }

    #[test]
    fn test_key_length() {
        let salt = generate_salt();
        let key = derive_key_pbkdf2("test", &salt, Some(1000)).unwrap();
        assert_eq!(key.len(), 32);
    }

    #[test]
    fn test_empty_password_rejected() {
        let salt = generate_salt();
        assert!(derive_key_pbkdf2("", &salt, Some(1000)).is_err());
    }
}
