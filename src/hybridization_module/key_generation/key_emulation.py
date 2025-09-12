import hashlib
import logging
import random

from hybridization_module.utils.key_formatting import key_to_bytes

log = logging.getLogger(__name__)

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


class MockQKDStack:
    def __init__(self) -> None:
        self.mock_key_store = {}

    def open_connect(self, chunk_size: int) -> str:
        """
        Mocks the OPEN_CONNECT request to the QKD node.
        Returns a mock key_stream_id.
        """
        key_stream_id = f"{random.randint(1000, 9999)}-mock"
        print(f"Connection opened with key_stream_id: {key_stream_id}")
        self.mock_key_store[key_stream_id] = {"chunk_size": chunk_size}

        log.info("Open connect mocked: key_stream_id=%s", key_stream_id)
        return key_stream_id

    def get_key(self, key_stream_id: str) -> bytes:
        """
        Mocks the GET_KEY request to the QKD node and returns a simulated key.
        """
        if key_stream_id not in self.mock_key_store:
            raise Exception("Invalid key_stream_id")
        print(f"Sending GET_KEY request for key_stream_id: {key_stream_id}")
        chunk_size = self.mock_key_store[key_stream_id]["chunk_size"]
        simulated_key = [random.randint(0, 255) for _ in range(chunk_size)]
        log.info("Key buffer mocked: %s", simulated_key)
        return key_to_bytes(simulated_key)

    def close_connection(self, key_stream_id: str) -> None:
        """
        Mocks the CLOSE request to the QKD node.
        """
        if key_stream_id in self.mock_key_store:
            del self.mock_key_store[key_stream_id]
        else:
            raise Exception("Invalid key_stream_id")