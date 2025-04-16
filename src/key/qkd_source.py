#kdfix/key/qkd_source.py

import socket 
import json
import time 
from utils.exception import check_status, QKDException
from utils.colorlog import color_log

class QKDSource:
    def __init__(self, request_oc, node, mock_qkd=False):
        """
        Initialize the QKD KMS connection using the node IP from the provided configuration.
        
        Args:
            request_oc: OPEN_CONNECT request from ETSI 004 interface
            node (tuple): IP address of the QKD node.
            mock_qkd (bool): Whether to use a mock QKD module (default: False).
        """
        color_log("QKD", "INFO", f"Connection with QKD module initialized")
        self.kms_socket = None
        self.request_oc = request_oc
        self.node = node
        self.mock_qkd = mock_qkd
        color_log("QKD", "INFO", f"Configuration loaded: ")


        if self.mock_qkd:
            from utils.mock_qkd_stack import MockQKDStack
            self.mock_kms_stack = MockQKDStack()
            color_log("QKD", "INFO", f"\t Mock QKD mode enabled", "   ├── ")

        else:
            color_log("QKD", "INFO", f"node={self.node}", "   ├── ")

    
    def connect_socket_kms(self):
        """
        Connect the socket connection to the KMS node.
        
        Returns:
            bool: True if the connection is established successfully, False otherwise.
        """
        if self.mock_qkd:
            # In mock mode, we don't need a socket connection
            return True
        
        try:
            self.kms_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.kms_socket.connect(self.node)
            return True
        except Exception as e:
            color_log("QKD", "KO", f"\t\t Error with the connection to KMS socket: {e}", "   \t├── ")

            return False
    
    def close_socket(self):
        """
        Close the current KMS socket connection.
        """
        if self.mock_qkd:
        # No socket to close in mock mode
            return
        
        # Close the socket connection if it exists
        if self.kms_socket:
            self.kms_socket.close()

    def _reset_socket_connection(self):
        """
        Helper method to reset the KMS socket connection.
        Closes the existing connection (if any) and opens a new one.
        """
        self.close_socket()
        self.connect_socket_kms()

    def fetch_key_qkd(self, chunk_size: int) -> str:
        """
        Fetch a key from the QKD node using the OPEN_CONNECT, GET_KEY, and CLOSE commands.
        
        Args:
            chunk_size (int): The size of the data chunks requested.
        
        Returns:
            str: The retrieved key from the QKD node.
        
        Raises:
            QKDException: If there is an error during the QKD operation.
        """
        if self.mock_qkd:
            # Use the mock QKD stack
            try:
                key_stream_id = self.mock_kms_stack.open_connect(chunk_size)
                time.sleep(2)  # Simulate some delay
                retrieved_key = self.mock_kms_stack.get_key(key_stream_id)
                self.mock_kms_stack.close_connection(key_stream_id)
            except Exception as e:
                color_log("QKD", "KO", f"Error during QKD mock operations: {e}", "   \t├── ")

                raise e
        else:
            # Step 1: Open socket connection
            if not self.connect_socket_kms():
                raise QKDException("Unable to establish connection to the KMS node.")

            try:
                # Step 2: Open connection (OPEN_CONNECT)
                key_stream_id = self.open_connect(chunk_size)

                # Reset socket for next operation
                self._reset_socket_connection()

                # Wait for a while to allow the connection to be established
                time.sleep(2)

                # Step 3: Get the key (GET_KEY)
                retrieved_key = self.get_key(key_stream_id)

                # Reset socket for next operation
                self._reset_socket_connection()

                # Step 4: Close the connection (CLOSE)
                self.close_connection(key_stream_id)

            except Exception as e:
                color_log("QKD", "KO", f"Error during QKD operations: {e}", "   \t├── ")

                raise e

            finally:
                # Ensure the socket is closed
                self.close_socket()
        color_log("QKD", "OK", f"Key successfully retrieved from QKDSource: {retrieved_key}", "   \t├── ")

        return retrieved_key

    def open_connect(self, chunk_size: int) -> str:
        """
        Connects to the KMS node and sends a request to open a connection.
        
        Args:
            chunk_size (int): The size of the data chunks requested.
        
        Returns:
            str: The 'key_stream_id' received from the KMS.
        
        Raises:
            ValueError: If the connection to the KMS is not established successfully.

        """
        if self.mock_qkd:
            # Use the mock QKD stack
            try:
                color_log("QKD", "INFO", "OPEN CONNECT Mocked Module", "   \t├── ")
                key_stream_id = self.mock_kms_stack.open_connect(chunk_size)
            except Exception as e:
                color_log("QKD", "KO", f"Error during OPEN CONNECT to Mocked Module: {e}", "   \t├── ")
                raise e
        else: 
            # Step 1: Open socket connection
            if not self.connect_socket_kms():
                raise QKDException("Unable to establish connection to the KMS node.")

            # Step 2: Prepare the OPEN_CONNECT request
            # Check if request_oc is a valid JSON format and not empty
            if not isinstance(self.request_oc, dict) or not self.request_oc:
                color_log("QKD", "ERROR", "Invalid or empty request_oc: Must be a non-empty dictionary", "   \t├── ")
                raise QKDException("Invalid or empty request_oc: Must be a non-empty dictionary")

            open_connect_request = self.request_oc
            color_log("QKD", "INFO", f"OPEN CONNECT Request for QKD stack:\n{json.dumps(open_connect_request, indent=2)}", "   \t├── ")

            try:
                # Step 3: Send OPEN_CONNECT resquest to the node
                self.kms_socket.sendall(json.dumps(open_connect_request).encode("utf8"))

                # Step 4: Receive response from
                response = self.kms_socket.recv(65057)

                if not response:
                    raise QKDException("Received empty response from QKD stack.")

                response_data = json.loads(response.decode("utf8"))
                color_log("QKD", "INFO", f"Response received from QKD stack:\n{json.dumps(response_data, indent=2)}",
                          "   \t├── ")
            except json.JSONDecodeError as e:
                color_log("QKD", "ERROR", f"Failed to decode JSON response: {e}", "   \t├── ")
                raise QKDException("Failed to decode JSON response") from e
            except Exception as e:
                color_log("QKD", "ERROR", f"Error during QKD request: {e}", "   \t├── ")
                raise QKDException("Error during QKD request") from e
            finally:
                # Step 5: Ensure the socket is closed
                self.close_socket()

            # Step 6: Check the status in the response
            status = response_data.get('status', -1)
            if status != 0:
                # Handle the error based on the status code
                check_status(status) 

            # Step 7: Extract the key_stream_id from the response
            key_stream_id = response_data.get('key_stream_id', None)
            if not key_stream_id:
                raise QKDException("ERROR in the OPEN_CONNECT response: No key_stream_id found")
            
        time.sleep(2)  # Simulate some delay to wait the connection before doing anything else
        color_log("QKD", "OK", f"OPEN CONNECTION achived. \n\t\t\t\t QKD Key KSID: {key_stream_id}", "   ├── ")
        return key_stream_id

    def get_key(self, key_stream_id: str): 
            """
            Makes a GET_KEY request to the QKD node to obtain a key.

            Args:
                key_stream_id (str): id of the key stream retrieved from the OPEN_CONNECT request.

            Returns:
                str: 

            Raises:
                ValueError: Si no se puede obtener la clave.
            """
            if self.mock_qkd:
                # Use the mock QKD stack
                try:
                    color_log("QKD", "INFO", "GET KEY from Mocked QKD Module", "   \t├── ")
                    key_buffer = self.mock_kms_stack.get_key(key_stream_id)
                    color_log("QKD", "OK", f"Key buffer mocked: {key_buffer}", "   ├── ")
                except Exception as e:
                    color_log("QKD", "KO", f"Error during GET KEY QKD mock operations: {e}", "   \t├── ")
                    raise e
            else: 
                # Step 1: Open socket connection
                if not self.connect_socket_kms():
                    raise QKDException("Unable to establish connection to the KMS node.")
            
                # Step 2: Prepare the GET_KEY request
                get_key_request = {
                    "command": "GET_KEY",
                    "data": {
                        "key_stream_id": key_stream_id,
                        "index": 0,
                        "metadata": {
                            "size": 46,  # Adjust this size based on actual metadata requirements
                            "buffer": "The metadata field is not used for the moment."
                        }
                    }
                }

                # Step 4: Send GET_KEY request to the node
                self.kms_socket.sendall(json.dumps(get_key_request).encode("utf8"))


                # Step 5: Receive response from the node
                response = self.kms_socket.recv(65057)
                response_data = json.loads(response.decode("utf8"))

                # Step 6: close the socket connection
                self.close_socket()    

                # Step 7: Check the status in the response
                status = response_data.get('status', -1)
                if status != 0:
                    # Handle the error based on the status code
                    check_status(status)  # This will raise the corresponding exception
                
                # Step 8: Extract the key buffer from the response
                key_buffer = response_data.get('key_buffer', None)
                if not key_buffer:
                    raise QKDException("ERROR in the GET_KEY response: No key_buffer found")
            
            color_log("QKD", "OK", f"GET KEY achived. \n\t\t\t\t QKD Key KSID: {key_stream_id}.\n\t\tKey Buffer: {key_buffer}", "   ├── ")
            return key_buffer
        
    def close_connection(self, key_stream_id: str):
        """
        Close the socket connection to the KMS node

        Args:
            key_stream_id (str): The key stream ID for which the connection needs to be closed.

        Raises:
            QKDException: If there is any failure during the connection or closing.
        """
        if self.mock_qkd:
            # Use the mock QKD stack
            try:
                self.mock_kms_stack.close_connection(key_stream_id)
                color_log("QKD", "INFO", "CLOSE from Mocked QKD Module", "   \t├── ")
            except Exception as e:
                    color_log("QKD", "KO", f"Error during CLOSE QKD mock operations: {e}", "   \t├── ")
                    raise e
        else: 
            # Step 1: Open socket connection
            if not self.connect_socket_kms():
                raise QKDException("Unable to establish connection to the KMS node.")
            
            # Step 2: Create the close request
            close_request = {
                "command": "CLOSE",
                "data": {
                    "key_stream_id": key_stream_id
                }
            }
        
            try:
                # Step 3: Send CLOSE request to the node
                self.kms_socket.sendall(json.dumps(close_request).replace("'", '"').encode("utf8"))

                # Step 4: Receive response from the node
                response = self.kms_socket.recv(65057)
                response_data = json.loads(response.decode("utf8"))

                # Step 5: Close the socket connection
                self.close_socket()    

                # Step 6: Check the status in the response
                status = response_data.get('status', -1)
                if status != 0:
                    # Handle the error based on the status code
                    check_status(status)  # This will raise the corresponding exception
                color_log("QKD", "OK", f"CLOSE achived. \n\t\t\t\t QKD Key KSID: {key_stream_id}", "   ├── ")
            except Exception as e:
                raise QKDException(f"Failed to close connection to QKD KMS node: {e}")
