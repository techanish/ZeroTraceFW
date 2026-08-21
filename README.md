# ZeroTraceFW

ZeroTraceFW (formerly ZeroTraceFS) is a secure, cloud-based document management framework.
It combines client-side encryption, memory-only document access, intelligent policy enforcement, automated self-destruction, and continuous activity auditing to provide complete lifecycle protection for confidential data.

## Highlights

- **Rust Security Engine**: High-performance AES-256-GCM encryption and secure memory via PyO3.
- **Cloud Sync**: Built-in Google Drive integration for secure, encrypted state persistence across sessions.
- **Dynamic Watermarking**: CSS and image overlays identifying the user and session.
- **Policy Engine & RBAC**: Real-time evaluation of roles, geo-fencing, and time-based access restrictions.
- **AI Classification**: Local heuristic scanner to auto-tag sensitive data (PII, Financial, Secret).
- **Anti-Forensics & Tamper Detection**: Rust-level process environment verification.
- **Advanced GUI Viewer**: Memory-only Qt6 viewer blocking clipboard and print events.

## Prerequisites

- Python 3.10+
- Rust toolchain (`cargo`, `rustc`) via MSVC for building the engine
- pip

## Installation and Startup

1. Clone or extract the project into a folder named ZeroTraceFW.
2. Build the Rust engine:
```powershell
.\build_engine.bat
```
3. Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

4. Run:

```powershell
python main.py
```

Control mode behavior:

- Explorer mode is default (non-blocking), optimized for File Explorer and click controls.
- Optional terminal command mode can be enabled by setting environment variable before launch:

```powershell
$env:ZTFS_CONTROL_MODE = "terminal"
python main.py
```

## Runtime Behavior

### First Run

1. Initializes mount/ and data/.
2. Prompts to create a new vault.
3. Captures master password and duress password.
4. Captures dead man's switch interval and global vault TTL.
5. Saves initial encrypted container state to data/container.pkl.
6. Starts sync + command loop.

### Subsequent Runs

1. Loads container from data/container.pkl.
2. Prompts for password.
3. Master password unlocks vault and populates mount/.
4. Duress password triggers full destruction and exits with Vault is empty.
5. Failed attempts are tracked; lockout wipes vault.

## Commands

- status
- list
- add <filepath>
- read <filename>
- set-ttl <filename> <minutes>
- set-reads <filename> <max>
- set-deadline <filename> <YYYY-mm-dd HH:MM:SS>
- audit
- export <filename> <dest>
- destroy <filename>
- destroy-all
- lock
- change-password
- quit

## File Explorer Integration (Windows)

ZeroTraceFW can now be controlled from Windows File Explorer while main.py is running.

### Install Explorer Right-Click Menu

Run this once in PowerShell from the project root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install_explorer_menu.ps1
```

### Use Right-Click Actions

After installation, right-click files or folders and choose ZeroTraceFW actions:

- File right-click:
  - ZeroTraceFW: Import into Vault
  - ZeroTraceFW: Open Securely (Password)
  - ZeroTraceFW: Destroy in Vault
  - ZeroTraceFW: Set TTL
  - ZeroTraceFW: Set Read Limit
  - ZeroTraceFW: Set Deadline
  - ZeroTraceFW: Read Preview
  - ZeroTraceFW: Export from Vault
- Folder right-click or folder background right-click:
  - ZeroTraceFW: Destroy Entire Vault
  - ZeroTraceFW: Lock Vault
  - ZeroTraceFW: Quit Vault
  - ZeroTraceFW: Queue Status Snapshot
  - ZeroTraceFW: Queue List Files
  - ZeroTraceFW: Queue Recent Audit
  - ZeroTraceFW: Open Control Panel

### How It Works

- Explorer actions enqueue JSON commands in .zerotracefw/commands.
- Running main.py consumes these commands on each cycle.
- Results are written to .zerotracefw/processed.
- Keep main.py running in a terminal for Explorer actions to execute.
- Command launcher checks runtime heartbeat and warns when stale, but still queues commands for reliability.
- Context menu actions run with hidden PowerShell window and use dialog boxes for input when needed.

### Automatic Read Count from File Open (Best Effort)

- When files are opened directly from mount/, ZeroTraceFW attempts to detect access-time changes and increments read_count.
- This depends on OS/filesystem last-access timestamp behavior.
- Read Preview, Open Securely, and CLI read/export always increment read_count.
- If your system does not update access time for direct file double-clicks, use Open Securely (Password) for strict tracked reads.
- For password prompt + guaranteed read tracking from File Explorer, use ZeroTraceFW: Open Securely (Password).

### Click-Based Control Panel UI (Windows)

Launch the control panel:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\ztfs_control_panel.ps1
```

The panel provides clickable buttons for all core actions:

- Import File
- Destroy File
- Set TTL
- Set Read Limit
- Set Deadline
- Read Preview
- Open Securely (Password)
- Export File
- List Vault Files
- Show Audit
- Refresh Status
- Destroy Entire Vault
- Lock Vault
- Quit Vault

The panel also includes a command box for CLI-style commands in the same UI.

You can also open it from File Explorer folder context menu:

- ZeroTraceFW: Open Control Panel

Runtime status is published to:

- .zerotracefw/status.json

Processed command results are saved as JSON files in:

- .zerotracefw/processed

### Remove Explorer Menu

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\uninstall_explorer_menu.ps1
```

## Security Model

- Plaintext working files exist only in mount/ during active session.
- No plaintext is stored in data/.
- Encrypted payloads and metadata are stored in data/container.pkl.
- Every encryption uses a fresh IV.
- Per-file keys are derived from master password + unique salt.
- On destructive events, files are overwritten before deletion.
- On quit/lock, mount/ is wiped.

## Seven Destruction Triggers

1. Per-file TTL
   Example: set-ttl secret.txt 2
   Behavior: secret.txt is destroyed after 2 minutes of no access (TTL counts from latest tracked access/read).

2. Read limit
   Example: set-reads api.txt 2
   Behavior: api.txt is destroyed after allowed reads are exceeded.

3. Date deadline
   Example: set-deadline report.txt 2026-12-31 23:59:59
   Behavior: report.txt is destroyed when deadline time is reached.

4. Global vault TTL
   Configured at startup.
   Behavior: entire vault is destroyed when session lifetime exceeds global limit.

5. Failed authentication lockout
   Behavior: repeated failed logins trigger full vault destruction.

6. Duress password
   Behavior: entering duress password triggers full vault destruction immediately.

7. Dead man's switch
   Configured at startup.
   Behavior: stale heartbeat condition triggers full vault destruction.

## Architecture Diagram (ASCII)

```text
+---------------------------------------------------------------+
|                       ZeroTraceFW GUI                         |
|                     (Qt6 Viewer & Control)                    |
+------------------------------+--------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                 Core Orchestration & Policies                 |
|  AuthManager | TriggerEngine | PolicyEngine | AIClassifier    |
+------------------------------+--------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|             Rust Security Engine (ztfs_engine)                |
| AES-256-GCM | Tamper Detection | Secure Memory | Anti-Debug   |
+------------------------------+--------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|        Local Persistence & Google Drive Cloud Backend         |
+---------------------------------------------------------------+
```

## Use Cases

- Healthcare: disposable patient extracts and temporary records
- Research: controlled lifespan for sensitive datasets
- Finance: ephemeral credentials, reports, and exports
- Security teams: incident artifacts with automatic expiration
- Development: temporary secret files and local key material
- Compliance: policy-driven data retention and destruction

## Running Tests

```powershell
python run_all_tests.py
```

## Running Demo Scenario

```powershell
python demo/demo_scenario.py
```

## Limitations and Disclaimers

- This project runs at user level and does not provide kernel-level filesystem guarantees.
- File recovery resistance depends on OS, filesystem, and hardware behavior.
- Dead man's switch timing in a single-threaded terminal loop is cooperative, not hard real-time.
- Do not treat this as certified secure deletion software for regulated destruction without independent validation.
- Keep backups of non-disposable data outside ZeroTraceFW.
