# kdfix/funtion/hmac.py
import hashlib
import hmac


def hmac_kdf(keys: list[bytes]) -> bytes:
    """
    Derives a key using HMAC with SHA-256, one of the keys is the message to hash
    and the other is the HMAC key.

    Args:
        keys (list[bytes]): An list with all the keys to hybridize.

    Returns:
        bytes: The derived key using HMAC.

    Raises:
        ValueError: If the salt is empty.
    """

    salt = keys[0]

    derived_key = hmac.new(salt, b''.join(keys[1:]), hashlib.sha256).digest()

    return derived_key

