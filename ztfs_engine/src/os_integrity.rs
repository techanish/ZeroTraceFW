// os_integrity.rs — Operating System Integrity Verification
//
// Checks: Secure Boot, suspicious processes, integrity scoring.

use pyo3::prelude::*;

/// Check if Secure Boot is enabled (Windows only).
#[pyfunction]
pub fn is_secure_boot_enabled() -> bool {
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;

        if let Ok(output) = std::process::Command::new("powershell")
            .creation_flags(CREATE_NO_WINDOW)
            .args(["-NoProfile", "-Command", "Confirm-SecureBootUEFI"])
            .output()
        {
            let stdout = String::from_utf8_lossy(&output.stdout).trim().to_lowercase();
            return stdout == "true";
        }
        false
    }

    #[cfg(not(windows))]
    {
        false
    }
}

/// Check for known suspicious/forensic processes.
fn check_suspicious_processes() -> Vec<String> {
    let suspicious = [
        "wireshark", "fiddler", "procmon", "procexp", "x64dbg", "x32dbg",
        "ollydbg", "windbg", "ida64", "ida", "ghidra", "cheatengine",
        "processhacker", "apimonitor", "regshot", "autoruns",
        "tcpdump", "strace", "ltrace", "gdb",
    ];

    let mut found = Vec::new();

    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;

        if let Ok(output) = std::process::Command::new("tasklist")
            .creation_flags(CREATE_NO_WINDOW)
            .args(["/FO", "CSV", "/NH"]).output()
        {
            let text = String::from_utf8_lossy(&output.stdout).to_lowercase();
            for proc_name in &suspicious {
                if text.contains(proc_name) {
                    found.push(proc_name.to_string());
                }
            }
        }
    }

    #[cfg(unix)]
    {
        if let Ok(output) = std::process::Command::new("ps").args(["aux"]).output() {
            let text = String::from_utf8_lossy(&output.stdout).to_lowercase();
            for proc_name in &suspicious {
                if text.contains(proc_name) {
                    found.push(proc_name.to_string());
                }
            }
        }
    }

    found
}

/// Comprehensive OS integrity check — returns JSON string.
#[pyfunction]
pub fn check_os_integrity() -> String {
    let secure_boot = is_secure_boot_enabled();
    let suspicious = check_suspicious_processes();

    let mut warnings = Vec::new();
    let mut score: i32 = 100;

    if !secure_boot {
        warnings.push("Secure Boot is not enabled or not detectable.".to_string());
        score -= 15;
    }

    for proc in &suspicious {
        warnings.push(format!("Suspicious process detected: {proc}"));
        score -= 20;
    }

    score = score.max(0);

    serde_json::json!({
        "secure_boot": secure_boot,
        "suspicious_processes": suspicious,
        "integrity_score": score,
        "warnings": warnings,
    }).to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_check_os_integrity_json() {
        let json = check_os_integrity();
        let parsed: serde_json::Value = serde_json::from_str(&json).unwrap();
        assert!(parsed.get("integrity_score").is_some());
    }
}
