from __future__ import annotations

from pathlib import Path


def initialize_project_dirs(base_path: str = ".") -> dict:
    base = Path(base_path).resolve()
    # Test if base directory is writable (e.g. not Program Files)
    try:
        test_file = base / ".perm_test"
        test_file.touch()
        test_file.unlink()
    except (PermissionError, OSError):
        base = Path.home() / ".zerotracefw"

    mount_path = base / "mount"
    data_path = base / "data"
    control_path = base / ".zerotracefw"
    commands_path = control_path / "commands"
    processed_path = control_path / "processed"

    for path in (mount_path, data_path, control_path, commands_path, processed_path):
        path.mkdir(parents=True, exist_ok=True)

    return {
        "mount_path": mount_path,
        "data_path": data_path,
        "container_path": data_path / "container.pkl",
        "control_path": control_path,
        "commands_path": commands_path,
        "processed_commands_path": processed_path,
    }


def run_setup(base_path: str = ".") -> dict:
    return initialize_project_dirs(base_path)
