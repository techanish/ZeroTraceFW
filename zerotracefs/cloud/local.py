import os
import shutil
from pathlib import Path
from typing import List

from .base import CloudBackend


class LocalBackend(CloudBackend):
    """Local simulation of a cloud backend. Syncs to a separate directory."""
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def upload(self, remote_path: str, data: bytes) -> bool:
        dest = self.storage_path / remote_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True

    def download(self, remote_path: str) -> bytes:
        src = self.storage_path / remote_path
        if not src.exists():
            raise FileNotFoundError(f"Remote file not found: {remote_path}")
        return src.read_bytes()

    def delete(self, remote_path: str) -> bool:
        src = self.storage_path / remote_path
        if src.exists():
            src.unlink()
            return True
        return False

    def list_files(self) -> List[str]:
        return [f.name for f in self.storage_path.glob("*") if f.is_file()]

    def get_version(self, remote_path: str) -> str:
        src = self.storage_path / remote_path
        if not src.exists():
            return ""
        return str(src.stat().st_mtime)
