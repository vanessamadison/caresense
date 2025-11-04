"""Homomorphic encryption helpers using Pyfhel."""

from __future__ import annotations

from pyfhel import PyCtxt, Pyfhel  # type: ignore[import-untyped]

from caresense.config import get_settings
from caresense.utils.logging import get_logger

log = get_logger(__name__)


class FHEContext:
    """Singleton-style manager for Pyfhel context."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._he = Pyfhel()
        self._initialised = False

    def _context_files_exist(self) -> bool:
        return (
            self._settings.biometric_fhe_context.exists()
            and self._settings.biometric_fhe_secret.exists()
        )

    def initialise(self) -> None:
        """Load or generate FHE context."""
        if self._initialised:
            return

        if self._context_files_exist():
            log.info("fhe_loading_context", path=str(self._settings.biometric_fhe_context))
            self._he.load_context(str(self._settings.biometric_fhe_context))
            self._he.load_secret_key(str(self._settings.biometric_fhe_secret))
        else:
            log.info("fhe_generating_context")
            self._settings.biometric_fhe_context.parent.mkdir(parents=True, exist_ok=True)
            self._he.contextGen(scheme="CKKS", n=2**15, scale=2**30, qi_sizes=[60, 40, 40, 60])
            self._he.keyGen()
            self._he.rotateKeyGen()
            self._he.save_context(str(self._settings.biometric_fhe_context))
            self._he.save_secret_key(str(self._settings.biometric_fhe_secret))

        self._initialised = True

    @property
    def he(self) -> Pyfhel:
        """Return initialised Pyfhel instance."""
        if not self._initialised:
            self.initialise()
        return self._he

    def encrypt_vector(self, values: list[float]) -> PyCtxt:
        """Encrypt a list of floats."""
        he = self.he
        ciphertext = he.encrypt(values)
        log.debug("fhe_encrypt", length=len(values))
        return ciphertext

    def decrypt_vector(self, ciphertext: PyCtxt) -> list[float]:
        """Decrypt an encrypted vector."""
        he = self.he
        plaintext = he.decrypt(ciphertext)
        log.debug("fhe_decrypt", length=len(plaintext))
        return list(plaintext)

    def encode_scalar(self, value: float) -> PyCtxt:
        """Encrypt a single float."""
        return self.encrypt_vector([value])

    def decrypt_scalar(self, ciphertext: PyCtxt) -> float:
        """Decrypt a single float value."""
        return self.decrypt_vector(ciphertext)[0]


_FHE_CONTEXT = FHEContext()


def get_fhe() -> FHEContext:
    """Return shared FHE context."""
    return _FHE_CONTEXT
