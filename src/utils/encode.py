#kdfix/utils/encode.py
import base64

class EncodeUtils:
    @staticmethod
    def encode_key(key: bytes) -> str:
        """
        Encodes a given key in bytes to a base64 string.
        
        Args:
            key (bytes): The key to encode.
        
        Returns:
            str: The base64 encoded key.
        """
        return base64.b64encode(key).decode('utf-8')

    @staticmethod
    def decode_key(encoded_key: str) -> bytes:
        """
        Decodes a base64 string back to bytes, handling missing padding if necessary.
        
        Args:
            encoded_key (str): The base64 encoded key.
        
        Returns:
            bytes: The decoded key in bytes.
        """
        # Add padding if necessary (Base64 strings must be a multiple of 4)
        if len(encoded_key) % 4 != 0:
            encoded_key += '=' * (4 - len(encoded_key) % 4)

        try:
            return base64.b64decode(encoded_key)
        except base64.binascii.Error:
            raise ValueError(f"Invalid base64 encoded key: {encoded_key}")
        
    @staticmethod
    def normalize_key(key) -> bytes:
        """
        Ensures that the input key is normalized to bytes, decoding if necessary.

        Args:
            key (str | bytes): The key, either as a base64 string or bytes.

        Returns:
            bytes: The normalized key in bytes.
        """
        if isinstance(key, str):
            # Handle base64 string and ensure proper decoding
            return EncodeUtils.decode_key(key)
        elif isinstance(key, bytes):
            return key
        else:
            raise ValueError(f"Unsupported key type: {type(key)}. Expected str or bytes.")