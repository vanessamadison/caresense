"""Biometric authentication orchestration."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Any

from functools import lru_cache

try:
    from pyfhel import PyCtxt  # type: ignore[import-untyped]
except Exception:  # pragma: no cover - optional dependency
    PyCtxt = Any  # type: ignore[assignment]
    _PYFHEL_AVAILABLE = False
else:
    _PYFHEL_AVAILABLE = True

from fastapi import HTTPException, status

from caresense.config import get_settings
from caresense.crypto.fhe import get_fhe
from caresense.crypto.secure_store import get_store
from caresense.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class BiometricToken:
    token_id: str
    ciphertext: str


class BiometricAuthService:
    """Zero-knowledge style biometric attestation using homomorphic encryption."""

    def __init__(self) -> None:
        self._fhe = get_fhe()
        self._store = get_store()

    def enrol(self, biometric_vector: list[float]) -> BiometricToken:
        """Encrypt and persist a biometric vector."""
        ciphertext = self._fhe.encrypt_vector(biometric_vector)
        token_id = base64.urlsafe_b64encode(os.urandom(18)).decode("utf-8")

        self._store.write(
            f"biometric_{token_id}",
            {
                "ciphertext": ciphertext.to_bytes().hex(),
            },
        )
        log.info("biometric_enrolled", token_id=token_id, vector_len=len(biometric_vector))
        return BiometricToken(token_id=token_id, ciphertext=ciphertext.to_bytes().hex())

    def verify(self, token_id: str, presented_vector: list[float], tolerance: float = 0.1) -> bool:
        """Compare encrypted baseline with presented biometric vector."""
        record = self._store.read(f"biometric_{token_id}")
        if not record:
            log.warning("biometric_missing_token", token_id=token_id)
            return False

        ciphertext_bytes = bytes.fromhex(record["ciphertext"])
        ciphertext = PyCtxt(pyfhel=self._fhe.he, bytestring=ciphertext_bytes)

        baseline_vector = self._fhe.decrypt_vector(ciphertext)
        if len(baseline_vector) != len(presented_vector):
            log.warning("biometric_length_mismatch", token_id=token_id)
            return False

        distance = sum(
            abs(base - presented) for base, presented in zip(baseline_vector, presented_vector)
        ) / len(baseline_vector)
        log.debug("biometric_distance", token_id=token_id, distance=distance)
        return distance <= tolerance


class DisabledBiometricAuthService:
    """Fallback when FHE is disabled or unavailable."""

    def _raise_unavailable(self) -> None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Biometric verification is disabled on this deployment.",
        )

    def enrol(self, biometric_vector: list[float]) -> BiometricToken:  # noqa: ARG002
        self._raise_unavailable()

    def verify(self, token_id: str, presented_vector: list[float], tolerance: float = 0.1) -> bool:  # noqa: ARG002,E501
        self._raise_unavailable()


@lru_cache
def get_biometric_service() -> BiometricAuthService | DisabledBiometricAuthService:
    settings = get_settings()
    if not settings.enable_fhe or not _PYFHEL_AVAILABLE:
        return DisabledBiometricAuthService()
    return BiometricAuthService()
