# KDFix.py

import os
import socket
import json
import sys
import signal
from interface.interface_etsi004 import ETSI004
from utils.colorlog import color_log

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
CONFIG_FILE = 'config.json'
node_config = {}

def load_config():
    """
    Load the configuration file for each node (config.json).
    """
    global node_config
    config_file = os.getenv("CFGFILE")
    try:
        with open(config_file, "r") as f:
            color_log("KDFIX", "INFO", f"Loaded configuration from {config_file}")
            node_config = json.load(f)
    except FileNotFoundError as e:
        color_log("KDFIX", "ERROR", f"Configuration file {config_file} not found")
        exit(1)

# Initialize global variables
server_socket = None
current_interface = None
node_id = None

# Create the socket server
def start_server(hybridization_address):
    """
    Start the hybridization server on the given address.
    Args:
        hybridization_address (tuple): A tuple containing the host and port.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(hybridization_address)
        server_socket.listen()
        color_log("KDFIX", "INFO", f"Server listening on {hybridization_address}", to_console=True)

        while True:
            try:
                conn, addr = server_socket.accept()
                with conn:
                    load_config()
                    color_log("KDFIX", "OK", f"Connection established with AGENT at {addr}")
                    while True:
                        data = conn.recv(65057)
                        if not data:
                            color_log("KDFIX", "OK", f"Connection closed by AGENT at {addr}")
                            break
                        global node_id  # Use global to persist Node_ID

                        # Handle the received data (assuming JSON requests)
                        try:
                            request = json.loads(data.decode('utf-8'))
                            response = handle_request(request)
                        except json.JSONDecodeError:
                            response = {"error": "Invalid JSON received"}

                        # Send the response back to the client
                        conn.sendall(json.dumps(response).encode('utf-8'))

                    color_log("KDFIX", "INFO", "\nRequest flow complete. Awaiting new incoming requests.\n\n\n", indent="",
                              to_console=True)

            except KeyboardInterrupt:
                signal_handler(signal.SIGINT, None)


# Handle incoming requests
def handle_request(request):
    """
    Handles incoming requests and routes them to the appropriate interface.

    Args:
        request (dict): The incoming request as a dictionary.

    Returns:
        dict: The response from the appropriate handler or an error message.
    """
    global current_interface  # Use global to persist the selected interface

    command = request.get("command")
    data = request.get("data", {})  # Get the data block, default to an empty dictionary

    color_log("KDFIX", "INFO", f"Received request {command}")

    if command == "OPEN_CONNECT":
        # Determine the interface
        current_interface = ETSI004(node_config)
        color_log("KDFIX", "INFO", f"Routing to {'ETSI004'} interface")
        return current_interface.OPEN_CONNECT(data)

    elif command == "GET_KEY":
        # Use the previously selected interface
        if current_interface is None:
            return {"status": "error", "message": "No interface selected. OPEN_CONNECT must be called first."}
        color_log("KDFIX", "INFO", f"Routing GET_KEY to {'ETSI004'} interface")
        return current_interface.GET_KEY(data)

    elif command == "CLOSE":
        # Use the previously selected interface
        if current_interface is None:
            return {"status": "error", "message": "No interface selected. OPEN_CONNECT must be called first."}
        color_log("KDFIX", "INFO", f"Routing CLOSE to {'ETSI004'} interface")
        return current_interface.CLOSE(data)
    else:
        return {"status": "error", "message": "Unknown command"}


def signal_handler(sig, frame):
    """Gracefully shuts down the server when a termination signal is received."""
    global server_socket
    if server_socket:
        color_log("KDFIX", "INFO", "Shutting down server gracefully...")
        server_socket.close()
    sys.exit(0)


# Register the signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

