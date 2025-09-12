#kdfix/key/qkd_source.py

import json
import logging
import socket
from uuid import uuid4

from hybridization_module.key_generation.key_source_interface import KeySource
from hybridization_module.model.exceptions import QkdError, check_status
from hybridization_module.model.requests import (
    OpenConnectQos,
    OpenConnectRequest,
    OpenConnectUriParameters,
)
from hybridization_module.model.shared_enums import KeyType
from hybridization_module.model.shared_types import NetworkAddress
from hybridization_module.utils.key_formatting import key_to_bytes

log = logging.getLogger(__name__)

class QKDSource(KeySource):
    def __init__(self,
        uri_params: OpenConnectUriParameters,
        qkd_node_address: NetworkAddress,
        mock_qkd: bool = False
    ) -> None:
        """Initialize the QKD KMS connection using the node IP from the provided configuration.

        Args:
            hybrid_oc_request (OpenConnectRequest): The OPEN_CONNECT request the hybrid module originally received.
            uri_params (OpenConnectUriParameters): The parameters extracted from the uris of the open connect
            qkd_node_address (NetworkAddress): The network address of the sever that will provide qkd key.
            mock_qkd (bool, optional): Whether to use a mock QKD module. Defaults to False.
        """
        self.id: str = f"{self.get_key_type()}-{uuid4()}"
        log.debug("Initializing QKD source with id: %s", self.id)


        self.kms_socket = None
        self.qkd_node_address: NetworkAddress = qkd_node_address
        self.mock_qkd: bool = mock_qkd
        self.qkd_ksid: str = ""
        log.debug("Configuration loaded:")

        self.source = f"qkd://Application1@{uri_params.source_uuid}"
        self.destination = f"qkd://Application4@{uri_params.destination_uuid}"

        log.debug("mock_qkd=%s", self.mock_qkd)
        if self.mock_qkd:
            from hybridization_module.key_generation.key_emulation import MockQKDStack
            self.mock_kms_stack = MockQKDStack()
        else:
            log.debug("node_address=%s", self.qkd_node_address)

    @classmethod
    def get_key_type(cls) -> KeyType:
        return KeyType.QKD

    def get_id(self) -> str:
        return self.id

    def _connect_socket_kms(self) -> bool:
        """
        Connect the socket connection to the KMS node.

        Returns:
            bool: True if the connection is established successfully, False otherwise.
        """

        try:
            self.kms_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.kms_socket.connect(self.qkd_node_address.to_tuple())
            log.debug("Connected with QKD socket.")
            return True
        except Exception as e:
            log.error("Error with connection to QKD socket: %s", e)
            return False

    def _close_socket(self) -> None:
        """
        Close the current KMS socket connection.
        """

        # Close the socket connection if it exists
        if self.kms_socket:
            self.kms_socket.close()

    def open_connect(self, hybrid_ksid: str, qos: OpenConnectQos, timeout: int = 10) -> None:
        """
        Connects to the KMS node and sends a request to open a connection.

        Args:
            hybrid_ksid (str) : The key_stream_id of the connection between hybridization modules.
            qos (OpenConnectQos): The quality of service the source has to meet.
            timeout (int): Maximum number of seconds can be functioning before giving a timeout error.

        Returns:
            str: The 'key_stream_id' received from the KMS.

        Raises:
            ValueError: If the connection to the KMS is not established successfully.

        """
        if self.mock_qkd:
            # Use the mock QKD stack
            try:
                log.debug("Mocking OPEN CONNECT")
                self.qkd_ksid = self.mock_kms_stack.open_connect(qos.key_chunk_size)
            except Exception as e:
                log.error("Error mocking OPEN CONNECT: %s", e)
                raise e

        # Step 1: Open socket connection
        if not self._connect_socket_kms():
            raise QkdError("Unable to establish connection to the KMS node.")

        # Step 2: Prepare the OPEN_CONNECT request

        qkd_request = OpenConnectRequest(
            source=self.source,
            destination=self.destination,
            qos=qos.model_copy(deep=True)
        )

        open_connect_request = {
            "command": "OPEN_CONNECT",
            "data": qkd_request.model_dump()
        }
        log.debug("Built OPEN CONNECT Request for QKD stack: %s", open_connect_request)

        try:
            # Step 3: Send OPEN_CONNECT request to the node
            self.kms_socket.sendall(json.dumps(open_connect_request).encode("utf8"))

            # Step 4: Receive response from
            response = self.kms_socket.recv(65057)

            if not response:
                raise QkdError("Received empty response from QKD stack.")

            response_data = json.loads(response.decode("utf8"))
            log.info("Received OPEN CONNECT response from QKD stack: %s", response_data)

        except json.JSONDecodeError as e:
            log.error("Failed to decode JSON response from QKD stack: %s", e)
            raise QkdError("Failed to decode JSON response") from e
        except Exception as e:
            log.error("Error during QKD OPEN CONNECT request: %s", e)
            raise QkdError("Error during QKD request") from e
        finally:
            # Step 5: Ensure the socket is closed
            self._close_socket()

        # Step 6: Check the status in the response
        status = response_data.get('status', -1)
        if status != 0:
            # Handle the error based on the status code
            check_status(status)

        # Step 7: Extract the key_stream_id from the response
        self.qkd_ksid = response_data.get('key_stream_id', None)
        if not self.qkd_ksid:
            raise QkdError("ERROR in the OPEN_CONNECT response: No key_stream_id found")

        log.debug("OPEN CONNECT completed. Obtained qkd ksid: %s", self.qkd_ksid)

    def get_key(self, retries: int = 5, timeout: int = 10) -> bytes:
        """
        Makes a GET_KEY request to the QKD node to obtain a key.

        Args:
            retries (int): Number of retries in the case of errors (Timeout errors do not count).
            timeout (int): Maximum number of seconds this method can be functioning before giving a timeout error.
        Returns:
            bytes: The qkd key

        Raises:
            ValueError: Si no se puede obtener la clave.
        """
        if self.mock_qkd:
            # Use the mock QKD stack
            try:
                log.debug("Mocking GET KEY")
                return self.mock_kms_stack.get_key(self.qkd_ksid)
            except Exception as e:
                log.debug("Error mocking GET KEY: %s", e)
                raise e

        # Step 1: Open socket connection
        if not self._connect_socket_kms():
            raise QkdError("Unable to establish connection to the KMS node.")

        # Step 2: Prepare the GET_KEY request
        get_key_request = {
            "command": "GET_KEY",
            "data": {
                "key_stream_id": self.qkd_ksid,
                "index": 0,
                "metadata": {
                    "size": 46,  # Adjust this size based on actual metadata requirements
                    "buffer": "The metadata field is not used for the moment."
                }
            }
        }

        # Step 4: Send GET_KEY request to the node
        log.debug("Built GET KEY request for QKD Stack: %s", get_key_request)
        self.kms_socket.sendall(json.dumps(get_key_request).encode("utf8"))

        # Step 5: Receive response from the node
        response = self.kms_socket.recv(65057)
        response_data = json.loads(response.decode("utf8"))
        log.debug("Received GET KEY response from QKD stack.")

        # Step 6: close the socket connection
        self._close_socket()

        # Step 7: Check the status in the response
        status = response_data.get('status', -1)
        if status != 0:
            # Handle the error based on the status code
            check_status(status)  # This will raise the corresponding exception

        # Step 8: Extract the key buffer from the response
        key_buffer = response_data.get('key_buffer', None)
        if not key_buffer:
            raise QkdError("ERROR in the GET_KEY response: No key_buffer found")

        log.debug("GET KEY completed. Key Buffer: %s", key_buffer)
        return key_to_bytes(key_buffer)

    def close(self) -> None:
        """
        Close the socket connection to the KMS node

        Raises:
            QKDException: If there is any failure during the connection or closing.
        """
        if self.mock_qkd:
            # Use the mock QKD stack
            try:
                log.debug("Mocking close QKD module.")
                self.mock_kms_stack.close_connection(self.qkd_ksid)
                return
            except Exception as e:
                log.error("Error mocking CLOSE: %s", e)
                raise e


        # Step 1: Open socket connection
        if not self._connect_socket_kms():
            raise QkdError("Unable to establish connection to the KMS node.")

        # Step 2: Create the close request
        close_request = {
            "command": "CLOSE",
            "data": {
                "key_stream_id": self.qkd_ksid
            }
        }
        log.debug("Built CLOSE request for QKD Stack: %s", close_request)

        try:
            # Step 3: Send CLOSE request to the node
            self.kms_socket.sendall(json.dumps(close_request).replace("'", '"').encode("utf8"))

            # Step 4: Receive response from the node
            response = self.kms_socket.recv(65057)
            response_data = json.loads(response.decode("utf8"))
            log.debug("Received CLOSE response from QKD stack: %s", response_data)

            # Step 5: Close the socket connection
            self._close_socket()

            # Step 6: Check the status in the response
            status = response_data.get('status', -1)
            if status != 0:
                # Handle the error based on the status code
                check_status(status)  # This will raise the corresponding exception
            log.debug("CLOSE Completed for qkd KSID: %s", self.qkd_ksid)
        except Exception as e:
            raise QkdError(f"Failed to close connection to QKD KMS node: {e}")
