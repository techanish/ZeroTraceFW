// tamper_detection.rs — Binary Self-Integrity & Tamper Detection
//
// Self-hash verification, timing anomaly detection, API hook scanning.

use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use sha2::{Digest, Sha256};

/// Compute the SHA-256 hash of the currently running executable.
#[pyfunction]
pub fn compute_self_hash() -> PyResult<String> {
    let exe_path = std::env::current_exe()
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to get exe path: {e}")))?;

    let data = std::fs::read(&exe_path)
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to read exe: {e}")))?;

    let mut hasher = Sha256::new();
    hasher.update(&data);
    Ok(hex::encode(hasher.finalize()))
}

/// Timing-based anomaly detection.
fn timing_anomaly_check() -> bool {
    let start = std::time::Instant::now();

    let mut accumulator: u64 = 0;
    for i in 0..100_000u64 {
        accumulator = accumulator.wrapping_add(i.wrapping_mul(7919));
    }
    std::hint::black_box(accumulator);

    let elapsed = start.elapsed();
    // Normal: ~0.1ms. Debugger single-stepping: >500ms.
    elapsed.as_millis() > 500
}

/// Check if critical Windows API functions have been hooked/detoured.
fn check_api_hooks() -> Vec<String> {
    let mut hooks_found = Vec::new();

    #[cfg(windows)]
    {
        use windows::Win32::System::LibraryLoader::{GetModuleHandleW, GetProcAddress};
        use windows::core::{HSTRING, PCSTR};

        let functions_to_check = [
            ("ntdll.dll", "NtQueryInformationProcess"),
            ("kernel32.dll", "IsDebuggerPresent"),
            ("kernel32.dll", "VirtualProtect"),
        ];

        for (module, func) in &functions_to_check {
            let module_h = HSTRING::from(*module);
            if let Ok(hmod) = unsafe { GetModuleHandleW(&module_h) } {
                let func_name = std::ffi::CString::new(*func).unwrap();
                let proc_addr = unsafe {
                    GetProcAddress(hmod, PCSTR::from_raw(func_name.as_ptr() as *const u8))
                };
                if let Some(addr) = proc_addr {
                    let addr_ptr = addr as *const u8;
                    let first_byte = unsafe { *addr_ptr };
                    if first_byte == 0xE9 {
                        hooks_found.push(format!("{module}!{func}: JMP detour (0xE9)"));
                    } else if first_byte == 0xFF {
                        let second_byte = unsafe { *addr_ptr.add(1) };
                        if second_byte == 0x25 {
                            hooks_found.push(format!("{module}!{func}: indirect JMP detour (0xFF25)"));
                        }
                    }
                }
            }
        }
    }

    hooks_found
}

/// Comprehensive tamper detection report — returns JSON string.
#[pyfunction]
pub fn check_tamper() -> String {
    let self_hash = compute_self_hash().unwrap_or_else(|_| "unknown".to_string());
    let timing = timing_anomaly_check();
    let hooks = check_api_hooks();

    let mut warnings: Vec<String> = Vec::new();
    let mut tamper_score: i32 = 0;

    if timing {
        warnings.push("Timing anomaly detected — possible debugger instrumentation.".to_string());
        tamper_score += 50;
    }

    for hook in &hooks {
        warnings.push(format!("API hook detected: {hook}"));
        tamper_score += 30;
    }

    tamper_score = tamper_score.min(100);

    serde_json::json!({
        "self_hash": self_hash,
        "timing_anomaly": timing,
        "api_hooks": hooks,
        "tamper_score": tamper_score,
        "warnings": warnings,
    }).to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_self_hash() {
        let hash = compute_self_hash().unwrap();
        assert_eq!(hash.len(), 64);
    }

    #[test]
    fn test_timing_check_normal() {
        assert!(!timing_anomaly_check(), "Timing anomaly in normal test");
    }

    #[test]
    fn test_check_tamper_json() {
        let json = check_tamper();
        let parsed: serde_json::Value = serde_json::from_str(&json).unwrap();
        assert!(parsed.get("tamper_score").is_some());
    }
}
