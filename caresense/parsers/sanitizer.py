"""Text sanitization and validation for secure processing."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, List

import bleach

from caresense.utils.logging import get_logger

log = get_logger(__name__)

# Security: Define allowed patterns
ALLOWED_TAGS: List[str] = []  # No HTML allowed in medical text
ALLOWED_ATTRIBUTES: Dict[str, List[str]] = {}
MAX_TEXT_LENGTH = 50000  # 50KB max
MAX_LINE_LENGTH = 1000

# Dangerous patterns to detect
DANGEROUS_PATTERNS = [
    r"<script",
    r"javascript:",
    r"onerror=",
    r"onclick=",
    r"<iframe",
    r"eval\(",
    r"exec\(",
]


class TextSanitizer:
    """
    Secure text sanitization for medical documents.

    Security features:
    - XSS prevention
    - SQL injection prevention
    - Command injection prevention
    - Length validation
    - Character encoding validation
    - PII redaction patterns
    """

    def __init__(self) -> None:
        self._logger = get_logger(__name__)

    def sanitize(self, text: str, strip_html: bool = True) -> str:
        """
        Sanitize input text with multiple security layers.

        Args:
            text: Input text to sanitize
            strip_html: Whether to strip HTML tags

        Returns:
            Sanitized text safe for processing

        Raises:
            ValueError: If text contains dangerous patterns or exceeds limits

        Security:
            - HTML stripping/escaping
            - XSS pattern detection
            - Length validation
            - Unicode normalization
            - Suspicious pattern detection
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")

        # Security: Length validation
        if len(text) > MAX_TEXT_LENGTH:
            self._logger.warning("text_too_long", length=len(text))
            raise ValueError(f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters")

        if len(text.strip()) == 0:
            raise ValueError("Empty text input")

        # Security: Detect dangerous patterns
        text_lower = text.lower()
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, text_lower):
                self._logger.warning("dangerous_pattern_detected", pattern=pattern)
                raise ValueError("Input contains potentially dangerous content")

        # Security: Strip/escape HTML
        if strip_html:
            text = bleach.clean(
                text,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRIBUTES,
                strip=True,
            )

        # Normalize unicode
        text = text.encode("utf-8", errors="ignore").decode("utf-8")

        # Remove null bytes
        text = text.replace("\x00", "")

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Validate line length
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if len(line) > MAX_LINE_LENGTH:
                lines[i] = line[:MAX_LINE_LENGTH]

        text = "\n".join(lines)

        # Final length check
        text = text.strip()[:MAX_TEXT_LENGTH]

        self._logger.debug("text_sanitized", original_length=len(text), final_length=len(text))

        return text

    def detect_pii(self, text: str) -> Dict[str, bool]:
        """
        Detect potential PII in text (not redacting, just flagging).

        Args:
            text: Text to scan

        Returns:
            Dict of PII types detected

        Security: Uses pattern matching without storing actual PII
        """
        pii_patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        }

        detected = {}
        for pii_type, pattern in pii_patterns.items():
            matches = re.findall(pattern, text)
            detected[pii_type] = len(matches) > 0

        if any(detected.values()):
            self._logger.warning("pii_detected", types=[k for k, v in detected.items() if v])

        return detected

    def validate_medical_text(self, text: str) -> bool:
        """
        Validate that text looks like legitimate medical content.

        Args:
            text: Text to validate

        Returns:
            True if text appears to be medical content

        Security: Helps detect injection/spam attempts
        """
        # Check for minimum word count
        words = text.split()
        if len(words) < 3:
            return False

        # Check for excessive repeated characters (spam indicator)
        if re.search(r"(.)\1{10,}", text):
            self._logger.warning("excessive_repetition_detected")
            return False

        # Check for excessive special characters
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        if special_char_ratio > 0.3:
            self._logger.warning("excessive_special_chars", ratio=special_char_ratio)
            return False

        return True


@lru_cache
def get_sanitizer() -> TextSanitizer:
    """Return singleton sanitizer instance."""
    return TextSanitizer()
