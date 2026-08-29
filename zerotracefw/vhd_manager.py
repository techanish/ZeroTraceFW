import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class VHDManager:
    """Manages creation, mounting, and dismounting of dynamic zfs.vhd virtual hard disks."""

    def __init__(self, vhd_path: Optional[Path] = None, drive_letter: str = "Z"):
        if vhd_path is None:
            vhd_path = Path.cwd() / ".zerotracefw" / "zfs.vhd"
        self.vhd_path = Path(vhd_path).resolve()
        self.drive_letter = drive_letter

    def _run_diskpart_script(self, script_content: str) -> Tuple[bool, str]:
        """Runs a diskpart script via a temporary file."""
        import tempfile
        try:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
                tf.write(script_content)
                script_file = tf.name

            # Run diskpart with script
            cmd = f'diskpart /s "{script_file}"'
            result = subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", f'Start-Process diskpart -ArgumentList "/s `"{script_file}`"" -Verb RunAs -Wait -WindowStyle Hidden'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )

            # Cleanup temp script
            try:
                os.remove(script_file)
            except Exception:
                pass

            return True, "Diskpart executed successfully."
        except Exception as e:
            logger.error(f"VHD operation failed: {e}")
            return False, str(e)

    def exists(self) -> bool:
        return self.vhd_path.exists()

    def create_vhd(self, size_mb: int = 5120) -> Tuple[bool, str]:
        """Creates a dynamic expandable zfs.vhd disk up to size_mb (default 5GB)."""
        self.vhd_path.parent.mkdir(parents=True, exist_ok=True)
        if self.exists():
            return True, f"VHD already exists at {self.vhd_path}"

        script = f"""create vdisk file="{self.vhd_path}" maximum={size_mb} type=expandable
select vdisk file="{self.vhd_path}"
attach vdisk
create partition primary
format fs=ntfs label="ZeroTraceFS" quick
assign letter={self.drive_letter}
"""
        logger.info(f"Creating dynamic VHD at {self.vhd_path} ({size_mb} MB max)...")
        success, msg = self._run_diskpart_script(script)
        if success:
            logger.info(f"Successfully created and mounted VHD at {self.drive_letter}:\\")
            return True, f"Created {self.vhd_path.name} ({size_mb}MB max) mounted at {self.drive_letter}:\\"
        return False, msg

    def mount_vhd(self) -> Tuple[bool, str]:
        """Mounts an existing zfs.vhd disk to the configured drive letter."""
        if not self.exists():
            return False, f"VHD file does not exist at {self.vhd_path}. Create it first."

        script = f"""select vdisk file="{self.vhd_path}"
attach vdisk
assign letter={self.drive_letter}
"""
        logger.info(f"Mounting VHD {self.vhd_path} to {self.drive_letter}:\\...")
        success, msg = self._run_diskpart_script(script)
        if success:
            return True, f"Mounted {self.vhd_path.name} to {self.drive_letter}:\\"
        return False, msg

    def dismount_vhd(self) -> Tuple[bool, str]:
        """Dismounts/detaches the zfs.vhd disk."""
        if not self.exists():
            return True, "VHD file does not exist."

        script = f"""select vdisk file="{self.vhd_path}"
detach vdisk
"""
        logger.info(f"Dismounting VHD {self.vhd_path}...")
        success, msg = self._run_diskpart_script(script)
        if success:
            return True, f"Dismounted {self.vhd_path.name} cleanly."
        return False, msg
