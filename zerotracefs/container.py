from __future__ import annotations

import pickle
from pathlib import Path

from .utils import utcnow
from .cloud.base import CloudBackend


class ContainerManager:
    def __init__(self, container_path: str | Path = Path("data") / "container.pkl", cloud_backend: CloudBackend = None) -> None:
        self.container_path = Path(container_path).resolve()
        self.container_path.parent.mkdir(parents=True, exist_ok=True)
        self.cloud_backend = cloud_backend
        self.revision = 0

    def save_state(self, vfs, auth, triggers, audit) -> None:
        self.revision += 1
        payload = {
            "vfs_data": vfs.serialize(),
            "auth_data": auth.serialize(),
            "trigger_data": triggers.serialize(),
            "audit_data": audit.serialize(),
            "version": "1.0.0",
            "revision": self.revision,
            "created_at": utcnow().isoformat(),
        }
        with self.container_path.open("wb") as fh:
            pickle.dump(payload, fh)

    def load_state(self, container_path: str | Path | None = None) -> dict:
        path = Path(container_path).resolve() if container_path else self.container_path
        if not path.exists():
            raise FileNotFoundError(f"Container file not found: {path}")

        with path.open("rb") as fh:
            state = pickle.load(fh)

        required = {"vfs_data", "auth_data", "trigger_data", "audit_data"}
        missing = sorted(required.difference(state.keys()))
        if missing:
            raise ValueError(f"Container state is missing fields: {', '.join(missing)}")
            
        self.revision = state.get("revision", 0)
        return state

    def push_to_cloud(self):
        """Uploads the container file to the cloud backend."""
        if not self.cloud_backend or not self.container_path.exists():
            return False
        
        try:
            data = self.container_path.read_bytes()
            # Note: For production, we should encrypt this data with the master password 
            # before uploading, as it contains file metadata (even though file content is encrypted).
            return self.cloud_backend.upload(self.container_path.name, data)
        except Exception as e:
            print(f"Cloud push failed: {e}")
            return False

    def pull_from_cloud(self):
        """Downloads the container file from the cloud backend if it's newer."""
        if not self.cloud_backend:
            return False
            
        try:
            remote_data = self.cloud_backend.download(self.container_path.name)
            
            # Simple conflict resolution: load remote state and compare revisions
            import pickle
            remote_state = pickle.loads(remote_data)
            remote_revision = remote_state.get("revision", 0)
            
            if remote_revision > self.revision:
                self.container_path.write_bytes(remote_data)
                self.revision = remote_revision
                print(f"Pulled newer vault state from cloud (Rev {remote_revision})")
                return True
            return False
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Cloud pull failed: {e}")
            return False

    def container_exists(self) -> bool:
        return self.container_path.exists()

    def destroy_container(self) -> bool:
        if not self.container_path.exists():
            return True
        try:
            self.container_path.unlink()
            return not self.container_path.exists()
        except Exception:
            return False
