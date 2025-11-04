"""Encrypted secret and payload storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet

from caresense.config import get_settings
from caresense.utils.logging import get_logger

log = get_logger(__name__)


class SecureStore:
    """Simple encrypted file-backed key-value store."""

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        settings = get_settings()
        self._storage_dir = storage_dir or settings.encrypted_storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._key_path = self._storage_dir / ".master.key"
        self._fernet = Fernet(self._load_or_create_key())

    def _load_or_create_key(self) -> bytes:
        if self._key_path.exists():
            return self._key_path.read_bytes()

        key = Fernet.generate_key()
        self._key_path.write_bytes(key)
        log.info("secure_store_created_key", path=str(self._key_path))
        return key

    def _path_for(self, name: str) -> Path:
        return self._storage_dir / f"{name}.bin"

    def write(self, name: str, payload: Any) -> Path:
        """Encrypt and persist payload."""
        data = json.dumps(payload).encode("utf-8")
        token = self._fernet.encrypt(data)
        path = self._path_for(name)
        path.write_bytes(token)
        log.info("secure_store_write", name=name, bytes=len(token))
        return path

    def read(self, name: str) -> Optional[Any]:
        """Load and decrypt payload."""
        path = self._path_for(name)
        if not path.exists():
            return None

        token = path.read_bytes()
        payload = json.loads(self._fernet.decrypt(token))
        log.debug("secure_store_read", name=name)
        return payload


_STORE = SecureStore()


def get_store() -> SecureStore:
    return _STORE
