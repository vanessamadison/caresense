"""CareSense secure triage platform."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("caresense")
except PackageNotFoundError:  # pragma: no cover - local dev fallback
    __version__ = "0.2.0-dev"

__all__ = ["__version__"]
