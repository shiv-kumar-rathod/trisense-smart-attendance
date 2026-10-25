from __future__ import annotations

import hashlib
import hmac
import secrets


_ITERATIONS = 600_000
_SALT_BYTES = 16
_HASH_NAME = "sha256"


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password must not be empty.")

    salt = secrets.token_bytes(_SALT_BYTES)

    derived_key = hashlib.pbkdf2_hmac(
        _HASH_NAME,
        password.encode("utf-8"),
        salt,
        _ITERATIONS,
    )

    return (
        f"pbkdf2_sha256${_ITERATIONS}$"
        f"{salt.hex()}${derived_key.hex()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its stored PBKDF2 hash."""
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False

    try:
        algorithm, iterations_text, salt_hex, expected_hex = (
            stored_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_text)

        if not 1 <= iterations <= 2_000_000:
            return False

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(expected_hex)

        if len(salt) != _SALT_BYTES or len(expected_hash) != 32:
            return False

        actual_hash = hashlib.pbkdf2_hmac(
            _HASH_NAME,
            password.encode("utf-8"),
            salt,
            iterations,
        )

        return hmac.compare_digest(actual_hash, expected_hash)

    except (ValueError, TypeError):
        return False
