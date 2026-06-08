"""
SecureVault security package.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Iterable

DEFAULT_ITERATIONS = 100_000
SALT_LENGTH = 16


def hash_password(password: str, salt: bytes) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256.
    """
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, DEFAULT_ITERATIONS
    ).hex()


def verify_password(password: str, salt: bytes, expected_hash: str) -> bool:
    """
    Verify a password against the expected hash.
    """
    computed_hash = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, expected_hash)


def is_strong_password(
    password: str,
    min_length: int = 12,
    required_classes: Iterable[str] = ("digit", "lower", "upper", "special"),
) -> bool:
    """
    Check whether the provided password meets basic strength criteria.
    """
    if len(password) < min_length:
        return False

    categories = {
        "digit": any(c.isdigit() for c in password),
        "lower": any(c.islower() for c in password),
        "upper": any(c.isupper() for c in password),
        "special": any(not c.isalnum() for c in password),
    }
    return all(categories.get(category, False) for category in required_classes)


__all__ = ["hash_password", "verify_password", "is_strong_password"]
