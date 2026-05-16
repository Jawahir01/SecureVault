"""Utility helpers for the SecureVault application."""

from __future__ import annotations

import base64
import hashlib
import os
from typing import Optional

__all__ = ["hash_password", "generate_token", "safe_encode", "safe_decode"]


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """Hash a password with an optional salt."""
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${digest.hex()}"


def generate_token(length: int = 32) -> str:
    """Generate a URL-safe random token."""
    token = base64.urlsafe_b64encode(os.urandom(length)).rstrip(b"=")
    return token.decode("ascii")


def safe_encode(value: str) -> bytes:
    """Encode a string value to UTF-8 bytes."""
    return value.encode("utf-8")


def safe_decode(value: bytes) -> str:
    """Decode UTF-8 bytes to a string."""
    return value.decode("utf-8")
