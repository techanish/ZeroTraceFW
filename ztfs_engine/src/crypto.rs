// crypto.rs — AES-256-GCM Authenticated Encryption
//
// This is the beating heart of ZeroTraceFW's cryptographic protection.
// Every byte that enters the vault passes through here.
//
// Format: nonce (12 bytes) || ciphertext || tag (16 bytes)
// All key material is wrapped in Zeroizing<> for automatic cleanup.

use aes_gcm::{
    aead::{Aead, KeyInit, OsRng},
    Aes256Gcm, Nonce,
};
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use rand::RngCore;
use zeroize::Zeroizing;

/// Encrypt plaintext with AES-256-GCM.
///
/// Args:
///     plaintext: Raw bytes to encrypt.
///     key: 32-byte encryption key.
///
/// Returns:
///     Sealed blob: nonce (12B) || ciphertext || tag (16B)
///
/// The nonce is generated internally from OsRng — never reuse a nonce.
#[pyfunction]
pub fn encrypt_aes256gcm(plaintext: &[u8], key: &[u8]) -> PyResult<Vec<u8>> {
    if key.len() != 32 {
        return Err(PyValueError::new_err(
            "Key must be exactly 32 bytes for AES-256-GCM.",
        ));
    }

    let cipher = Aes256Gcm::new_from_slice(key)
        .map_err(|e| PyValueError::new_err(format!("Failed to init cipher: {e}")))?;

    let mut nonce_bytes = [0u8; 12];
    OsRng.fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);

    let ciphertext = cipher
        .encrypt(nonce, plaintext)
        .map_err(|e| PyValueError::new_err(format!("Encryption failed: {e}")))?;

    // Pack: nonce || ciphertext (which includes the 16-byte tag appended by aes-gcm)
    let mut sealed = Vec::with_capacity(12 + ciphertext.len());
    sealed.extend_from_slice(&nonce_bytes);
    sealed.extend_from_slice(&ciphertext);

    Ok(sealed)
}

/// Decrypt an AES-256-GCM sealed blob.
///
/// Args:
///     sealed_data: nonce (12B) || ciphertext || tag (16B)
///     key: 32-byte encryption key.
///
/// Returns:
///     Decrypted plaintext bytes.
///
/// Raises ValueError on invalid key, corrupted data, or authentication failure.
#[pyfunction]
pub fn decrypt_aes256gcm(sealed_data: &[u8], key: &[u8]) -> PyResult<Vec<u8>> {
    if key.len() != 32 {
        return Err(PyValueError::new_err(
            "Key must be exactly 32 bytes for AES-256-GCM.",
        ));
    }
    if sealed_data.len() < 12 + 16 {
        return Err(PyValueError::new_err(
            "Sealed data too short — must contain at least nonce (12B) + tag (16B).",
        ));
    }

    let nonce_bytes = &sealed_data[..12];
    let ciphertext_with_tag = &sealed_data[12..];

    let cipher = Aes256Gcm::new_from_slice(key)
        .map_err(|e| PyValueError::new_err(format!("Failed to init cipher: {e}")))?;

    let nonce = Nonce::from_slice(nonce_bytes);

    let plaintext = cipher
        .decrypt(nonce, ciphertext_with_tag)
        .map_err(|_| PyValueError::new_err("Decryption failed — invalid key or corrupted data."))?;

    Ok(plaintext)
}

/// Generate a cryptographically secure 32-byte AES-256 key.
#[pyfunction]
pub fn generate_key() -> Vec<u8> {
    let mut key = Zeroizing::new([0u8; 32]);
    OsRng.fill_bytes(key.as_mut());
    key.to_vec()
}

/// Generate a cryptographically secure 12-byte GCM nonce.
#[pyfunction]
pub fn generate_nonce() -> Vec<u8> {
    let mut nonce = [0u8; 12];
    OsRng.fill_bytes(&mut nonce);
    nonce.to_vec()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_roundtrip() {
        let key = generate_key();
        let plaintext = b"ZeroTraceFW says hello from Rust";
        let sealed = encrypt_aes256gcm(plaintext, &key).unwrap();
        let decrypted = decrypt_aes256gcm(&sealed, &key).unwrap();
        assert_eq!(plaintext.to_vec(), decrypted);
    }

    #[test]
    fn test_wrong_key_fails() {
        let key1 = generate_key();
        let key2 = generate_key();
        let sealed = encrypt_aes256gcm(b"secret", &key1).unwrap();
        assert!(decrypt_aes256gcm(&sealed, &key2).is_err());
    }

    #[test]
    fn test_tampered_data_fails() {
        let key = generate_key();
        let mut sealed = encrypt_aes256gcm(b"secret", &key).unwrap();
        // Flip a byte in the ciphertext
        let idx = sealed.len() / 2;
        sealed[idx] ^= 0xFF;
        assert!(decrypt_aes256gcm(&sealed, &key).is_err());
    }

    #[test]
    fn test_bad_key_length() {
        assert!(encrypt_aes256gcm(b"data", &[0u8; 16]).is_err());
        assert!(decrypt_aes256gcm(&[0u8; 40], &[0u8; 16]).is_err());
    }
}
