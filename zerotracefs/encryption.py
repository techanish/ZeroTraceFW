from __future__ import annotations

import os
from pathlib import Path

try:
    import ztfs_engine
    _HAS_ZTFS_ENGINE = True
except ImportError:
    _HAS_ZTFS_ENGINE = False
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionEngine:
    def encrypt(self, plaintext: bytes, key: bytes, iv: bytes = b"") -> bytes:
        # Ignore `iv` as AES-GCM uses internally generated nonce in ztfs_engine or here
        self._validate_key(key)
        
        if _HAS_ZTFS_ENGINE:
            # Returns nonce(12) || ciphertext || tag(16)
            return ztfs_engine.encrypt_aes256gcm(plaintext, key)
        else:
            aesgcm = AESGCM(key)
            nonce = os.urandom(12)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            return nonce + ciphertext

    def decrypt(self, ciphertext: bytes, key: bytes, iv: bytes = b"") -> bytes:
        self._validate_key(key)
        
        if len(ciphertext) < 28:
            raise ValueError("Sealed data too short — must contain at least nonce (12B) + tag (16B).")
            
        if _HAS_ZTFS_ENGINE:
            try:
                return bytes(ztfs_engine.decrypt_aes256gcm(ciphertext, key))
            except Exception as e:
                if "Authentication failed" in str(e) or "invalid key" in str(e).lower() or "decryption failed" in str(e).lower():
                    raise ValueError("Invalid file password or corrupted data.") from e
                raise
        else:
            nonce = ciphertext[:12]
            actual_ciphertext = ciphertext[12:]
            aesgcm = AESGCM(key)
            try:
                return aesgcm.decrypt(nonce, actual_ciphertext, None)
            except Exception as e:
                raise ValueError("Invalid file password or corrupted data.") from e

    @staticmethod
    def generate_iv() -> bytes:
        # Kept for compatibility with filesystem.py, though unused in GCM
        return b""

    @staticmethod
    def generate_key() -> bytes:
        if _HAS_ZTFS_ENGINE:
            return bytes(ztfs_engine.generate_key())
        return os.urandom(32)

    def encrypt_file(self, file_path: str | Path, key: bytes) -> dict[str, bytes]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(str(path))
        plaintext = path.read_bytes()
        ciphertext = self.encrypt(plaintext, key)
        return {"ciphertext": ciphertext, "iv": b""}

    def decrypt_to_file(self, ciphertext: bytes, key: bytes, iv: bytes, output_path: str | Path) -> Path:
        plaintext = self.decrypt(ciphertext, key, iv)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(plaintext)
        return path

    @staticmethod
    def _validate_key(key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256-GCM.")
