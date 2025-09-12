from hybridization_module.hybridization_functions.hmac import hmac_kdf
from hybridization_module.hybridization_functions.xoring import xoring_kdf


def xorhmac_kdf(keys: list[bytes], chunk_size: int) -> bytes:
    """
    Derives a key by first applying hmac both ways and then applies xor with the hashes.

    Args:
        keys (list[bytes]): An list with all the keys to hybridize.

    Returns:
        bytes: The derived key using the combination of XOR and HMAC.

    Raises:
        ValueError: If the keys are not of the same length for XOR.
    """

    # Use the existing hmac_kdf function to apply HMAC
    hmac_results = []

    copied_keys = keys.copy() # We don't want to change the order of the original list
    hmac_results.append(hmac_kdf(copied_keys))

    copied_keys.reverse()
    hmac_results.append(hmac_kdf(copied_keys))

    # Perform XOR derivation using the existing xoring function
    derived_key = xoring_kdf(hmac_results, chunk_size)

    return derived_key