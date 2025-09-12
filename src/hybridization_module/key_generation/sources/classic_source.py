#kdfix/key/classic_source.py

class ClassicSource:
    def fetch_key(self) -> bytes:
        """
        Mocks fetching a classic cryptographic key.
        
        Returns:
            bytes: A mock classic key.
        """
        # Mocked classic key, replace with real fetching logic later
        return b"classic_mock_key"

    def fetch_dict(self) -> dict:
        """
        Mocks fetching a dictionary of classic keys.
        
        Returns:
            dict: A dictionary of classic keys.
        """
        # Mocked classic keys, replace with real fetching logic later
        return {"classic": ["010011", "111010", "111101"]}
