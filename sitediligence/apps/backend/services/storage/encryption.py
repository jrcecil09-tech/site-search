"""At-rest encryption helpers for sensitive storage objects."""

import base64
import os

from cryptography.fernet import Fernet  # type: ignore


def generate_key() -> bytes:
    return Fernet.generate_key()


def encrypt(data: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(data)


def decrypt(token: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(token)


def key_from_env() -> bytes:
    raw = os.environ.get("ENCRYPTION_KEY", "")
    if not raw:
        raise RuntimeError("ENCRYPTION_KEY environment variable is not set")
    return base64.urlsafe_b64decode(raw.encode())
