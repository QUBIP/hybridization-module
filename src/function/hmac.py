#kdfix/funtion/hmac.py
import hmac
import hashlib
import os
from utils.validate import key_to_bytes

def generate_random_salt(size: int = 16) -> bytes:
    """
    Generates a random salt of the specified size.

    Args:
        size (int): The size of the salt in bytes (default: 16).
    
    Returns:
        bytes: A random salt.
    """
    return os.urandom(size)

def hmac_kdf(key1, key2, salt):
    """
    Derives a key using HMAC with SHA-256 combining two input keys and a salt.
    
    Args:
        key1 (bytes): The first input key.
        key2 (bytes): The second input key.
        salt (bytes): The salt to add randomness to the key derivation.
    
    Returns:
        bytes: The derived key using HMAC.
    
    Raises:
        ValueError: If the salt is empty.
    """
    # Validate and convert keys to bytes.
    key1_bytes, key2_bytes, salt_bytes = key_to_bytes(key1, key2, salt)

    # Validate the salt
    if not salt:
        raise ValueError("Salt must not be empty.")
    
    # Combine the keys to form a message.
    message = key1_bytes + key2_bytes
    
    # Create the HMAC using SHA-256.
    derived_key = hmac.new(salt_bytes, message, hashlib.sha256).digest()
    
    return derived_key.hex()

def hmac_kdf_dict(key_dict: dict, salt: bytes = None) -> bytes:
    """
    Derives a key by applying HMAC with SHA-256 to a dictionary of keys.
    
    Args:
        key_dict (dict): A dictionary of keys where the keys are the names of the keys and the values are the keys themselves.
        salt (bytes): The salt to add randomness to the key derivation.
    
    Returns:
        bytes: The derived key using HMAC.

    Raises:
        ValueError: If the keys dictionary is empty.
    """
    
    # Ensure the dictionary is not empty.
    if not key_dict:
        raise ValueError("The key dictionary must contain at least one key.")
    
    # If no salt is provided, generate a random one
    if salt is None:
        salt = generate_random_salt()

    all_keys = []

    for keys in key_dict.values():

        # Skip empty list of keys
        if not keys:
            continue

        # Combine the keys using HMAC operation
        derived_key = keys[0]
        for key in keys[1:]:
            derived_key = hmac_kdf(derived_key, key, salt)

        # Add the combined result for this list to the final list of all keys
        all_keys.append(derived_key)

    # Ensure we have keys to combine.
    if not all_keys:
        raise ValueError("No valid keys found in the dictionary for HMAC operation.")
    
    # Combine all the derived keys into a single derived key.
    final_derived_key = all_keys[0]
    for key in all_keys[1:]:
        final_derived_key = hmac_kdf(final_derived_key, key, salt)
    
    return final_derived_key


