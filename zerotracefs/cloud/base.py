from abc import ABC, abstractmethod
from typing import List


class CloudBackend(ABC):
    """Abstract interface for ZeroTraceFW cloud storage backends."""

    @abstractmethod
    def upload(self, remote_path: str, data: bytes) -> bool:
        """Uploads encrypted data to the cloud."""
        pass

    @abstractmethod
    def download(self, remote_path: str) -> bytes:
        """Downloads encrypted data from the cloud."""
        pass

    @abstractmethod
    def delete(self, remote_path: str) -> bool:
        """Deletes a file from the cloud."""
        pass

    @abstractmethod
    def list_files(self) -> List[str]:
        """Lists all files available in the cloud vault."""
        pass

    @abstractmethod
    def get_version(self, remote_path: str) -> str:
        """Returns a version or hash to detect changes."""
        pass
