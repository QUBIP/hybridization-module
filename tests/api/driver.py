import socket
import json
import os

# Constants
BUFFER_SIZE = 65057
CONFIG_FILE = 'config.json'
OPEN_CONNECT_REQUEST_FILE = 'open_connect_request.json'

def load_config():
    """
    Load the configuration file (config.json).
    """
    config_path = os.path.join(CONFIG_FILE)
    with open(config_path, 'r') as file:
        return json.load(file)

def load_request(filename):
    """
    Load a JSON request from a file.
    """
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'r') as file:
        return json.load(file)

def send_request(socket_conn, request):
    """
    Send a JSON request via the socket and return the response.
    """
    socket_conn.sendall(json.dumps(request).encode("utf8"))
    while True:
        response_bytes = socket_conn.recv(BUFFER_SIZE)
        if response_bytes:
            response = json.loads(response_bytes.decode("utf8"))
            return response

def request_key(request_data):
    """
    Main function for the driver.
    """
    # Load configuration
    config = load_config()
    local_node = config["local_node"]

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as kdfix_socket:
            # Connect to the Hybridization Module
            hybridization_address = tuple(local_node["hybridization_address"])
            kdfix_socket.connect(hybridization_address)
            print(f"Driver connected to KDFix server at {hybridization_address}")

            #  OPEN_CONNECT
            print("\n--- OPEN_CONNECT ---")
            try:
                json_data = request_data.dict()
                print("Processing hybrid key request with:", json_data)
            except TypeError as e:
                print("JSON serialization failed:", e)
            oc_response = send_request(kdfix_socket, json_data)
            print("OPEN_CONNECT response:", oc_response)

            # Ensure session establishment
            if oc_response.get("status") != 0:
                print("Failed to open connection. Exiting...")
                return

            # Record key_stream_id to continue the standar 004 process
            key_stream_id = oc_response["key_stream_id"]

            #  GET_KEY
            print("\n--- GET_KEY ---")
            gk_request = {
                "command": "GET_KEY",
                "data": {
                    "key_stream_id": key_stream_id,
                    "index": 0,
                    "metadata": {
                        "size": 46,
                        "buffer": "The metadata field is not used for the moment."
                    }
                }
            }

            gk_response = send_request(kdfix_socket, gk_request)
            print("GET_KEY response:", gk_response)

            #  CLOSE
            print("\n--- CLOSE ---")
            cl_request = {
                "command": "CLOSE",
                "data": {
                    "key_stream_id": key_stream_id
                }
            }

            cl_response = send_request(kdfix_socket, cl_request)
            print("CLOSE response:", cl_response)

            # Return gk_response
            return {
                "status": gk_response.get("status", 0),
                "key_material": gk_response.get("key_buffer"),
                "key_stream_id": key_stream_id
            }

    except ConnectionError as e:
        print(f"Connection error: {e}")
        return {"status": -1, "error": "Connection failed", "message": str(e)}

    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"status": -1, "error": "Unexpected error", "message": str(e)}

    finally:
        print("Driver execution completed.")

if __name__ == "__main__":
    request_key()