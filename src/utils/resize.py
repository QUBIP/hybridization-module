
def enforce_key_size(key: bytes, size: int) -> bytes:
    if len(key) > size:
        # Truncate the key if it's too long
        return key[:size]
    elif len(key) < size:
        # Pad the key with zeros if it's too short
        return key.ljust(size, b'\0')
    return key
