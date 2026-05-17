
"""Test package for SecureVault.

This module provides lightweight helpers used by the test suite.
"""

from pathlib import Path
from typing import Iterator


def project_root() -> Path:
	"""Return the project root path (two levels up from this file)."""
	return Path(__file__).resolve().parent.parent


def tests_root() -> Path:
	"""Return the tests package root path."""
	return Path(__file__).resolve().parent


def iter_test_files(pattern: str = "*.py") -> Iterator[Path]:
	"""Yield test files in the tests package matching pattern."""
	for p in tests_root().rglob(pattern):
		yield p


__all__ = ["project_root", "tests_root", "iter_test_files"]
