# kdfix/funtion/xoring.py

from hybridization_module.utils import key_formatting


def xoring_kdf(keys: list[bytes], chunk_size: int) -> bytes:
    """
    Derives a key using XOR operation between two input keys.

    Args:
        keys (list[bytes]): An list with all the keys to hybridize.

    Returns:
        bytes: The derived key resulting from the XOR operation.

    Raises:
        ValueError: If the keys are not of the same length.
    """

    derived_key: bytes = key_formatting.enforce_key_size(keys[0], chunk_size)

    for key in keys[1:]:
        key_formatted = key_formatting.enforce_key_size(key, chunk_size)

        derived_key = bytes(a ^ b for a, b in zip(derived_key, key_formatted))

    return derived_key
