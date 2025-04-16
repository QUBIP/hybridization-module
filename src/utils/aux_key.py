import hashlib

def generate_deterministic_aux_key(seed: str, key_length: int) -> list:
    """
    Generates a deterministic auxiliary key based on a shared seed.

    Args:
        seed (str): A shared seed known to all nodes.
        key_length (int): The desired length of the auxiliary key.

    Returns:
        list: A deterministic auxiliary key as a list of integers.
    """
    # Hash the seed to generate a byte sequence
    hash_bytes = hashlib.sha256(seed.encode()).digest()

    # Repeat the hash output if needed to match the desired length
    while len(hash_bytes) < key_length:
        hash_bytes += hashlib.sha256(hash_bytes).digest()

    # Truncate to the desired length and return as a list of integers
    return list(hash_bytes[:key_length])
