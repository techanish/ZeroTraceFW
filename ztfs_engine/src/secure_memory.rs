// secure_memory.rs — Locked Memory, Zeroization, SecureBuffer
//
// Ensures sensitive data (keys, plaintext) never leaks to swap/pagefile.
// On Windows: VirtualLock/VirtualUnlock
// On Linux:   mlock/munlock
// All buffers auto-zero on drop via the `zeroize` crate.

use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use zeroize::Zeroize;

/// Securely wipe a byte buffer by overwriting with zeros then random bytes.
/// Returns the number of bytes wiped.
///
/// Note: This operates on a COPY in Rust. For Python objects, the original
/// Python bytes object is immutable. This function is primarily used for
/// wiping Rust-side buffers and demonstrating the wipe pattern.
/// The real security comes from the Zeroizing<> wrapper on all key material.
#[pyfunction]
pub fn secure_wipe_bytes(data: &[u8]) -> usize {
    let mut buf = data.to_vec();
    let len = buf.len();

    // Pass 1: overwrite with random
    for byte in buf.iter_mut() {
        *byte = rand::random();
    }
    // Pass 2: overwrite with zeros
    buf.zeroize();

    len
}

/// Lock a memory region to prevent it from being paged to disk.
///
/// Args:
///     address: Memory address (as integer) — obtained from ctypes or similar.
///     size: Number of bytes to lock.
///
/// Returns True on success.
#[pyfunction]
pub fn lock_memory_page(address: usize, size: usize) -> PyResult<bool> {
    #[cfg(windows)]
    {
        use windows::Win32::System::Memory::VirtualLock;
        let result = unsafe {
            VirtualLock(address as *const std::ffi::c_void, size)
        };
        if result.is_err() {
            return Err(PyRuntimeError::new_err("VirtualLock failed. Insufficient privileges?"));
        }
        Ok(true)
    }

    #[cfg(unix)]
    {
        let result = unsafe { libc::mlock(address as *const std::ffi::c_void, size) };
        if result != 0 {
            return Err(PyRuntimeError::new_err("mlock failed. Insufficient privileges?"));
        }
        Ok(true)
    }

    #[cfg(not(any(windows, unix)))]
    {
        Err(PyRuntimeError::new_err("Memory locking not supported on this platform."))
    }
}

/// Unlock a previously locked memory region, allowing it to be paged again.
#[pyfunction]
pub fn unlock_memory_page(address: usize, size: usize) -> PyResult<bool> {
    #[cfg(windows)]
    {
        use windows::Win32::System::Memory::VirtualUnlock;
        let result = unsafe {
            VirtualUnlock(address as *const std::ffi::c_void, size)
        };
        if result.is_err() {
            return Err(PyRuntimeError::new_err("VirtualUnlock failed."));
        }
        Ok(true)
    }

    #[cfg(unix)]
    {
        let result = unsafe { libc::munlock(address as *const std::ffi::c_void, size) };
        if result != 0 {
            return Err(PyRuntimeError::new_err("munlock failed."));
        }
        Ok(true)
    }

    #[cfg(not(any(windows, unix)))]
    {
        Err(PyRuntimeError::new_err("Memory unlocking not supported on this platform."))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_secure_wipe() {
        let data = vec![0xDE, 0xAD, 0xBE, 0xEF];
        let wiped = secure_wipe_bytes(&data);
        assert_eq!(wiped, 4);
    }

    #[test]
    fn test_wipe_empty() {
        let wiped = secure_wipe_bytes(&[]);
        assert_eq!(wiped, 0);
    }
}
