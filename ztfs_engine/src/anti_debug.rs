// anti_debug.rs — Debugger Detection
//
// Detects if a debugger is attached to the ZeroTraceFW process.
// On Windows: IsDebuggerPresent, CheckRemoteDebuggerPresent
// On Linux:   /proc/self/status TracerPid check

use pyo3::prelude::*;

/// Check if a local debugger is attached to this process.
#[pyfunction]
pub fn is_debugger_attached() -> bool {
    #[cfg(windows)]
    {
        use windows::Win32::System::Diagnostics::Debug::IsDebuggerPresent;
        unsafe { IsDebuggerPresent().as_bool() }
    }

    #[cfg(unix)]
    {
        if let Ok(status) = std::fs::read_to_string("/proc/self/status") {
            for line in status.lines() {
                if line.starts_with("TracerPid:") {
                    let pid_str = line.split(':').nth(1).unwrap_or("0").trim();
                    if let Ok(pid) = pid_str.parse::<u64>() {
                        return pid != 0;
                    }
                }
            }
        }
        false
    }

    #[cfg(not(any(windows, unix)))]
    {
        false
    }
}

/// Check if a remote debugger is attached (Windows-specific).
#[pyfunction]
pub fn check_remote_debugger() -> bool {
    #[cfg(windows)]
    {
        use windows::Win32::System::Diagnostics::Debug::CheckRemoteDebuggerPresent;
        use windows::Win32::System::Threading::GetCurrentProcess;
        use windows::Win32::Foundation::BOOL;

        let mut debugger_present = BOOL::from(false);
        let result = unsafe {
            CheckRemoteDebuggerPresent(GetCurrentProcess(), &mut debugger_present)
        };
        result.is_ok() && debugger_present.as_bool()
    }

    #[cfg(not(windows))]
    {
        false
    }
}

/// Comprehensive debug check — returns JSON string with all results.
#[pyfunction]
pub fn full_debug_check() -> String {
    let local = is_debugger_attached();
    let remote = check_remote_debugger();

    let methods: Vec<&str> = {
        let mut m = vec!["IsDebuggerPresent"];
        #[cfg(windows)]
        m.push("CheckRemoteDebuggerPresent");
        #[cfg(unix)]
        m.push("proc_self_status");
        m
    };

    serde_json::json!({
        "debugger_attached": local || remote,
        "local_debugger": local,
        "remote_debugger": remote,
        "methods_checked": methods,
    }).to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_debugger_check_returns_bool() {
        let _result = is_debugger_attached();
    }

    #[test]
    fn test_remote_debugger_check() {
        let _result = check_remote_debugger();
    }

    #[test]
    fn test_full_check_returns_json() {
        let json = full_debug_check();
        let parsed: serde_json::Value = serde_json::from_str(&json).unwrap();
        assert!(parsed.get("debugger_attached").is_some());
    }
}
