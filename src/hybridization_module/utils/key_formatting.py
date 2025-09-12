#kdfix/utils/validate_key.py
import base64


def key_to_bytes(key: bytes | list[int] | str | int) -> bytes:

    if isinstance(key, bytes):
        return key

    elif isinstance(key, str):
        # Detect base64 or hex strings
        try:
            return base64.b64decode(key)
        except Exception:
            try:
                return bytes.fromhex(key)
            except Exception:
                return key.encode('utf-8')

    elif isinstance(key, int):
        # Convert integer to bytes
        return key.to_bytes((key.bit_length() + 7) // 8, 'big') or b'\0'

    elif isinstance(key, list):
        # Convert a list of integers to bytes
        if all(isinstance(i, int) for i in key):
            return bytes(key)
        else:
            raise ValueError(f"Unsupported list element type in key: {key}")
    else:
        raise ValueError(f"Unsupported key type: {type(key)}. Expected str, bytes, int, or list of integers.")


#kdfix/utils/resize.py

def enforce_key_size(key: bytes, size: int) -> bytes:
    if len(key) > size:
        # Truncate the key if it's too long
        return key[:size]
    elif len(key) < size:
        # Pad the key with zeros if it's too short
        return key.ljust(size, b'\0')
    return key