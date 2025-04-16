#kdfix/utils/validate_key.py
import base64

def key_to_bytes(*keys):
    validated_keys = []
    
    for key in keys:
        if isinstance(key, bytes):
            validated_keys.append(key)
        elif isinstance(key, str):
            # Detect base64 or hex strings
            try:
                validated_keys.append(base64.b64decode(key))
            except Exception:
                try:
                    validated_keys.append(bytes.fromhex(key))
                except Exception:
                    validated_keys.append(key.encode('utf-8'))
        elif isinstance(key, int):
            # Convert integer to bytes
            validated_keys.append(key.to_bytes((key.bit_length() + 7) // 8, 'big') or b'\0')
        elif isinstance(key, list):
            # Convert a list of integers to bytes
            if all(isinstance(i, int) for i in key):
                validated_keys.append(bytes(key))
            else:
                raise ValueError(f"Unsupported list element type in key: {key}")
        else:
            raise ValueError(f"Unsupported key type: {type(key)}. Expected str, bytes, int, or list of integers.")
    
    return validated_keys
