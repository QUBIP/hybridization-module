

import json
import os
import socket
import sys
import threading

# Constants
BUFFER_SIZE = 65057

# Default number of drivers
NUM_DRIVERS = 10

# Check if a file name was passed as argument
if len(sys.argv) > 1:
    NUM_DRIVERS = int(sys.argv[1])


def load_config() -> dict:
    """
    Load the configuration file for each node (config.json).
    """
    config_file = os.getenv("CFGFILE")
    try:
        with open(config_file, "r") as f:
            print(f"Loaded configuration from {config_file}")
            return json.load(f)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        exit(1)


def send_request(socket_conn: socket.socket, request: dict) -> dict:
    """
    Send a JSON request via the socket and return the response.
    """
    socket_conn.sendall(json.dumps(request).encode("utf8"))
    while True:
        response_bytes = socket_conn.recv(BUFFER_SIZE)
        if response_bytes:
            response = json.loads(response_bytes.decode("utf8"))
            return response

def create_open_connect_request(driver_id: int) -> dict:
    return {
        "command": "OPEN_CONNECT",
        "data": {
            "source": f"hybrid://SPI_{driver_id}@aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa?hybridization=xoring&kem_mec=ML-KEM-512",
            "destination": f"hybrid://SPI_{driver_id}@bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb?hybridization=xoring&kem_mec=ML-KEM-512",
            "qos": {
                "key_chunk_size": 32,
                "max_bps": 32,
                "min_bps": 32,
                "jitter": 0,
                "priority": 0,
                "timeout": 0,
                "ttl": 0,
                "metadata_mimetype": "application/json"
            }
        }
    }



def do_full_connection_cicle(driver_id: int, hm_address: dict) -> None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as kdfix_socket:
            # Connect to the Hybridization Module
            kdfix_socket.connect((hm_address["host"], hm_address["port"]))

            #  OPEN_CONNECT
            oc_request = create_open_connect_request(driver_id)
            oc_response = send_request(kdfix_socket, oc_request)
            print(f"Driver {driver_id} OPEN_CONNECT response:", oc_response)

            # Ensure session establishment
            if oc_response.get("status") != 0:
                print("Failed to open connection. Exiting...")
                return

            # Record key_stream_id to continue the standar 004 process
            key_stream_id = oc_response["key_stream_id"]

            #  GET_KEY
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
            print(f"Driver {driver_id} GET_KEY response:", gk_response)

            #  CLOSE
            cl_request = {
                "command": "CLOSE",
                "data": {
                    "key_stream_id": key_stream_id
                }
            }

            cl_response = send_request(kdfix_socket, cl_request)
            print(f"Driver {driver_id} CLOSE response:", cl_response)

    except ConnectionError as e:
        print(f"Driver {driver_id} connection error: {e}")
    except Exception as e:
        print(f"Driver {driver_id} unexpected error: {e}")
    finally:
        print(f"Driver {driver_id} execution completed.")

def run_driver() -> None:
    """
    Main function for the driver.
    """
    # Load configuration
    config = load_config()
    hm_address = config["hybridization_server_address"]
    thread_list: list[threading.Thread] = []

    for i in range(NUM_DRIVERS):
        new_thread = threading.Thread(target=do_full_connection_cicle, args=(i, hm_address))
        new_thread.start()
        thread_list.append(new_thread)

    for thread in thread_list:
        thread.join()


if __name__ == "__main__":
    run_driver()