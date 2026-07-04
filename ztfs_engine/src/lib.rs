// ztfs_engine — ZeroTraceFW Rust Security Engine
// PyO3 module entry point: exposes all Rust security primitives to Python.
//
// Architecture:
//   Python (gui_app.py / zerotracefs/) <-- PyO3 FFI --> Rust (this crate)
//
// Modules:
//   crypto          — AES-256-GCM authenticated encryption
//   key_derivation  — PBKDF2-HMAC-SHA256 key stretching
//   secure_memory   — mlock, zeroize, SecureBuffer
//   anti_debug      — debugger detection (Windows: IsDebuggerPresent, NtQuery)
//   vm_detection    — hypervisor/VM detection (CPUID, registry, MAC, SMBIOS)
//   os_integrity    — secure boot verification, driver enumeration
//   tamper_detection— binary self-hash, import table checks, timing anomalies
//   session         — cryptographic session tokens with hardware binding

mod crypto;
mod key_derivation;
mod secure_memory;
mod anti_debug;
mod vm_detection;
mod os_integrity;
mod tamper_detection;
mod session;

use pyo3::prelude::*;

/// ZeroTraceFW Rust Security Engine.
/// Import as: `import ztfs_engine`
#[pymodule]
fn ztfs_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // ── Crypto ──────────────────────────────────────────────
    m.add_function(wrap_pyfunction!(crypto::encrypt_aes256gcm, m)?)?;
    m.add_function(wrap_pyfunction!(crypto::decrypt_aes256gcm, m)?)?;
    m.add_function(wrap_pyfunction!(crypto::generate_key, m)?)?;
    m.add_function(wrap_pyfunction!(crypto::generate_nonce, m)?)?;

    // ── Key Derivation ──────────────────────────────────────
    m.add_function(wrap_pyfunction!(key_derivation::derive_key_pbkdf2, m)?)?;
    m.add_function(wrap_pyfunction!(key_derivation::generate_salt, m)?)?;
    m.add_function(wrap_pyfunction!(key_derivation::hash_password, m)?)?;
    m.add_function(wrap_pyfunction!(key_derivation::verify_password, m)?)?;

    // ── Secure Memory ───────────────────────────────────────
    m.add_function(wrap_pyfunction!(secure_memory::secure_wipe_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(secure_memory::lock_memory_page, m)?)?;
    m.add_function(wrap_pyfunction!(secure_memory::unlock_memory_page, m)?)?;

    // ── Anti-Debug ──────────────────────────────────────────
    m.add_function(wrap_pyfunction!(anti_debug::is_debugger_attached, m)?)?;
    m.add_function(wrap_pyfunction!(anti_debug::check_remote_debugger, m)?)?;
    m.add_function(wrap_pyfunction!(anti_debug::full_debug_check, m)?)?;

    // ── VM Detection ────────────────────────────────────────
    m.add_function(wrap_pyfunction!(vm_detection::is_virtual_machine, m)?)?;
    m.add_function(wrap_pyfunction!(vm_detection::get_vm_indicators, m)?)?;

    // ── OS Integrity ────────────────────────────────────────
    m.add_function(wrap_pyfunction!(os_integrity::check_os_integrity, m)?)?;
    m.add_function(wrap_pyfunction!(os_integrity::is_secure_boot_enabled, m)?)?;

    // ── Tamper Detection ────────────────────────────────────
    m.add_function(wrap_pyfunction!(tamper_detection::check_tamper, m)?)?;
    m.add_function(wrap_pyfunction!(tamper_detection::compute_self_hash, m)?)?;

    // ── Session Management ──────────────────────────────────
    m.add_function(wrap_pyfunction!(session::create_session, m)?)?;
    m.add_function(wrap_pyfunction!(session::validate_session, m)?)?;
    m.add_function(wrap_pyfunction!(session::destroy_session, m)?)?;
    m.add_function(wrap_pyfunction!(session::get_hardware_fingerprint, m)?)?;

    Ok(())
}
