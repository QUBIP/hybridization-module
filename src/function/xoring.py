#kdfix/funtion/xoring.py
from utils import resize, validate

import base64

def xoring_kdf(key1, key2, chunk_size=None):
    """
    Derives a key using XOR operation between two input keys.
    
    Args:
        key1 (str or bytes): The first input key.
        key2 (str or bytes): The second input key.
    
    Returns:
        bytes: The derived key resulting from the XOR operation.
    
    Raises:
        ValueError: If the keys are not of the same length.
    """
    # Validate and convert keys to bytes
    key1_bytes, key2_bytes = validate.key_to_bytes(key1, key2)
    
    # If chunk_size is provided, enforce key size
    if chunk_size:
        key1_bytes = resize.enforce_key_size(key1_bytes, chunk_size)
        key2_bytes = resize.enforce_key_size(key2_bytes, chunk_size)
    else:
        # Ensure both keys have the same length
        if len(key1_bytes) != len(key2_bytes):
            raise ValueError("Keys must have the same length for XOR operation.")
    
    # Perform XOR
    derived_key = bytes(a ^ b for a, b in zip(key1_bytes, key2_bytes))
    
    return derived_key


def xoring_kdf_dict(key_dict: dict, chunk_size=None):
    """
    Derives a key by applying XOR operation between a dictionary of keys.
    
    Args:
        key_dict (dict): A dictionary of keys where the keys are the names of the keys and the values are the keys themselves.
    
    Returns:
        bytes: The derived key resulting from the XOR operation between all the keys.
    
    Raises:
        ValueError: If the keys dictionary is empty.
    """
    
    # Ensure the dictionary is not empty.
    if not key_dict:
        raise ValueError("The key dictionary must contain at least one key.")
    
    all_keys = []

    for keys in key_dict.values():
        # Skip empty list of keys
        if not keys:
            continue

        # Combine the keys using XOR operation
        derived_key = keys[0]
        for key in keys[1:]:
            derived_key = xoring_kdf(derived_key, key, chunk_size)

        # Add the combined result for this list to the final list of all keys
        all_keys.append(derived_key)
        
    # Ensure we have keys to combine.
    if not all_keys:
        raise ValueError("No valid keys found in the dictionary for XOR operation.")
    
    # Combine all the derived keys into a single derived key.
    final_derived_key = all_keys[0]
    for key in all_keys[1:]:
        final_derived_key = xoring_kdf(final_derived_key, key, chunk_size)
    
    return final_derived_key
