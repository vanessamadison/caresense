"""Immutable compliance and audit trail helpers."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from caresense.config import get_settings
from caresense.utils.logging import get_logger

log = get_logger(__name__)


class ComplianceTrail:
    """Append-only audit logging with Ed25519 signatures."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._log_path = self._settings.audit_log_path
        self._key_path = self._log_path.with_suffix(".ed25519")
        self._ensure_keys()

    def _ensure_keys(self) -> None:
        if self._key_path.exists():
            private_bytes = self._key_path.read_bytes()
            self._private_key = Ed25519PrivateKey.from_private_bytes(private_bytes)
        else:
            self._private_key = Ed25519PrivateKey.generate()
            private_bytes = self._private_key.private_bytes(
                Encoding.Raw, PrivateFormat.Raw, NoEncryption()
            )
            self._key_path.write_bytes(private_bytes)
            log.info("compliance_key_generated", path=str(self._key_path))

        self._public_key = self._private_key.public_key()

    def public_key_pem(self) -> bytes:
        return self._public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo,
        )

    def log_event(self, payload: Dict[str, Any]) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        normalized = {
            "timestamp": timestamp,
            "payload": payload,
        }
        serialized = json.dumps(normalized, sort_keys=True).encode("utf-8")

        signature = self._private_key.sign(serialized)
        record = {
            **normalized,
            "signature": signature.hex(),
        }

        with self._log_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(record) + os.linesep)

        log.debug("compliance_event_logged", path=str(self._log_path))
        return record["signature"]
