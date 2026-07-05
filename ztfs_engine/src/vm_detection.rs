// vm_detection.rs — Virtual Machine / Hypervisor Detection
//
// Detects if ZeroTraceFW is running inside a VM.
// Detection: CPUID hypervisor bit, registry keys, MAC OUI, manufacturer strings.

use pyo3::prelude::*;

/// Check the CPUID hypervisor present bit.
fn check_cpuid_hypervisor() -> bool {
    #[cfg(any(target_arch = "x86", target_arch = "x86_64"))]
    {
        // CPUID leaf 1, ECX bit 31 = hypervisor present
        // rbx is reserved by LLVM, so we save/restore it via a temp register
        let result: u32;
        unsafe {
            std::arch::asm!(
                "push rbx",
                "cpuid",
                "pop rbx",
                inout("eax") 1u32 => _,
                out("ecx") result,
                out("edx") _,
            );
        }
        (result >> 31) & 1 == 1
    }

    #[cfg(not(any(target_arch = "x86", target_arch = "x86_64")))]
    {
        false
    }
}

/// Check Windows registry for known VM artifacts.
fn check_registry_vm_keys() -> Vec<String> {
    let mut indicators = Vec::new();

    #[cfg(windows)]
    {
        use windows::Win32::System::Registry::*;
        use windows::core::HSTRING;

        let vm_keys = [
            (r"SOFTWARE\VMware, Inc.\VMware Tools", "VMware Tools"),
            (r"SOFTWARE\Oracle\VirtualBox Guest Additions", "VirtualBox GA"),
            (r"SYSTEM\CurrentControlSet\Services\vmci", "VMware VMCI"),
            (r"SYSTEM\CurrentControlSet\Services\VBoxGuest", "VirtualBox Guest"),
        ];

        for (key_path, name) in &vm_keys {
            let hstring = HSTRING::from(*key_path);
            let mut hkey = HKEY::default();
            let result = unsafe {
                RegOpenKeyExW(HKEY_LOCAL_MACHINE, &hstring, 0, KEY_READ, &mut hkey)
            };
            if result.is_ok() {
                indicators.push(name.to_string());
                unsafe { let _ = RegCloseKey(hkey); }
            }
        }
    }

    indicators
}

/// Check MAC addresses for known VM vendor OUI prefixes.
fn check_mac_addresses() -> Vec<String> {
    let vm_ouis = [
        ("00:05:69", "VMware"), ("00:0C:29", "VMware"), ("00:1C:14", "VMware"),
        ("00:50:56", "VMware"), ("08:00:27", "VirtualBox"), ("00:15:5D", "Hyper-V"),
        ("52:54:00", "QEMU/KVM"),
    ];

    let mut indicators = Vec::new();

    #[cfg(windows)]
    {
        if let Ok(output) = std::process::Command::new("getmac")
            .args(["/FO", "CSV", "/NH"]).output()
        {
            let stdout = String::from_utf8_lossy(&output.stdout).to_uppercase();
            for (oui, name) in &vm_ouis {
                let oui_dashed = oui.replace(':', "-").to_uppercase();
                if stdout.contains(&oui_dashed) {
                    indicators.push(format!("MAC:{name}"));
                }
            }
        }
    }

    indicators
}

/// Check system manufacturer strings.
fn check_system_manufacturer() -> Vec<String> {
    let mut indicators = Vec::new();

    #[cfg(windows)]
    {
        if let Ok(output) = std::process::Command::new("wmic")
            .args(["computersystem", "get", "manufacturer,model"]).output()
        {
            let text = String::from_utf8_lossy(&output.stdout).to_lowercase();
            let vm_strings = [
                ("vmware", "VMware"), ("virtualbox", "VirtualBox"),
                ("virtual machine", "Hyper-V"), ("qemu", "QEMU"),
                ("xen", "Xen"), ("parallels", "Parallels"),
            ];
            for (pattern, name) in &vm_strings {
                if text.contains(pattern) {
                    indicators.push(format!("Manufacturer:{name}"));
                }
            }
        }
    }

    indicators
}

/// Quick boolean check: is the process running inside any virtual machine?
#[pyfunction]
pub fn is_virtual_machine() -> bool {
    check_cpuid_hypervisor()
        || !check_registry_vm_keys().is_empty()
        || !check_mac_addresses().is_empty()
        || !check_system_manufacturer().is_empty()
}

/// Detailed VM indicator report as JSON string.
#[pyfunction]
pub fn get_vm_indicators() -> String {
    let cpuid = check_cpuid_hypervisor();
    let registry = check_registry_vm_keys();
    let mac = check_mac_addresses();
    let mfg = check_system_manufacturer();
    let is_vm = cpuid || !registry.is_empty() || !mac.is_empty() || !mfg.is_empty();

    serde_json::json!({
        "is_vm": is_vm,
        "cpuid_hypervisor": cpuid,
        "registry_indicators": registry,
        "mac_indicators": mac,
        "manufacturer_indicators": mfg,
    }).to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_vm_returns_bool() {
        let _result = is_virtual_machine();
    }

    #[test]
    fn test_get_vm_indicators_json() {
        let json = get_vm_indicators();
        let parsed: serde_json::Value = serde_json::from_str(&json).unwrap();
        assert!(parsed.get("is_vm").is_some());
    }
}
