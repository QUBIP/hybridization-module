import random
import json

class MockQKDStack:
    def __init__(self):
        self.mock_key_store = {}

    def open_connect(self, chunk_size):
        """
        Mocks the OPEN_CONNECT request to the QKD node.
        Returns a mock key_stream_id.
        """
        key_stream_id = f"{random.randint(1000, 9999)}-mock"
        print(f"Connection opened with key_stream_id: {key_stream_id}")
        self.mock_key_store[key_stream_id] = {"chunk_size": chunk_size}
        return key_stream_id

    def get_key(self, key_stream_id):
        """
        Mocks the GET_KEY request to the QKD node and returns a simulated key.
        """
        if key_stream_id not in self.mock_key_store:
            raise Exception("Invalid key_stream_id")
        print(f"Sending GET_KEY request for key_stream_id: {key_stream_id}")
        chunk_size = self.mock_key_store[key_stream_id]["chunk_size"]
        simulated_key = [random.randint(0, 255) for _ in range(chunk_size)]
        return simulated_key

    def close_connection(self, key_stream_id):
        """
        Mocks the CLOSE request to the QKD node.
        """
        if key_stream_id in self.mock_key_store:
            del self.mock_key_store[key_stream_id]
        else:
            raise Exception("Invalid key_stream_id")
