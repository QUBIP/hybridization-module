from .xoring import xoring_kdf
from .hmac import hmac_kdf
from utils.validate import key_to_bytes

def xorhmac_kdf(key1: bytes, key2: bytes, salt: bytes, chunk_size=None) -> bytes:
    """
    Derives a key by first applying XOR and then HMAC with SHA-256.
    
    Args:
        key1 (bytes): The first input key.
        key2 (bytes): The second input key.
        salt (bytes): The salt to add randomness to the key derivation.
    
    Returns:
        bytes: The derived key using the combination of XOR and HMAC.
    
    Raises:
        ValueError: If the keys are not of the same length for XOR.
    """

    # Perform XOR derivation using the existing xoring function
    xor_result = xoring_kdf(key1, key2, chunk_size)
    
    # Use the existing hmac_kdf function to apply HMAC
    derived_key = hmac_kdf(xor_result, b'', salt)
    
    return derived_key


def xorhmac_kdf_dict(key_dict: dict, salt: bytes, chunk_size=None):
    """
    Derives a key by applying XOR and then HMAC with SHA-256 to a dictionary of keys.
    
    Args:
        key_dict (dict): A dictionary of keys where the keys are the names of the keys and the values are the keys themselves.
        salt (bytes): The salt to add randomness to the key derivation.
    
    Returns:
        bytes: The derived key using the combination of XOR and HMAC.

    Raises:
        ValueError: If the keys dictionary is empty.
    """
    # Ensure the dictionary is not empty
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
            derived_key = xorhmac_kdf(derived_key, key, salt, chunk_size)
        
        # Add the combined result for this list to the final list of all keys
        all_keys.append(derived_key)

    # Ensure we have keys to combine
    if not all_keys:
        raise ValueError("No valid keys found in the dictionary for XOR and HMAC operation.")

    # Combine all the derived keys into a single derived key.
    final_derived_key = all_keys[0]
    for key in all_keys[1:]:
        final_derived_key = xorhmac_kdf(final_derived_key, key, salt)

    return final_derived_key