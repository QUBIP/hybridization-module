# KDFix.py

import json
import logging
import socket
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

from hybridization_module.model.config import GeneralConfiguration, PeerInfo
from hybridization_module.model.requests import CloseRequest, GetKeyRequest, OpenConnectRequest
from hybridization_module.model.shared_types import NetworkAddress
from hybridization_module.peer_connector.connector_interface import PeerConnectionManager
from hybridization_module.peer_connector.peer_to_peer_connector import PeerToPeerConnectionManager
from hybridization_module.sessions.etsi004_session import Etsi004Session

log = logging.getLogger(__name__)

# Initialize global variables
class Etsi004Server():

    def __init__(self, config: GeneralConfiguration, peers_info: dict[str, PeerInfo]) -> None:
        self.config: GeneralConfiguration = config
        self.peers_info: dict[str, PeerInfo] = peers_info

        self.sessions_dicts_lock: threading.Lock = threading.Lock()
        self.open_sessions: dict[str, Etsi004Session] = {}
        self.sessions_locks: dict[str, threading.Lock] = {}

        ## Initialize the peer connector
        self.peer_manager: PeerConnectionManager = PeerToPeerConnectionManager(self.config.peer_local_address, config.certificate_config)


    def _process_request(self, request: dict) -> dict:
        """
        Handles incoming requests and routes them to the appropriate interface.

        Args:
            request (dict): The incoming request as a dictionary.

        Returns:
            dict: The response from the appropriate handler or an error message.
        """

        command = request.get("command")
        data = request.get("data", {})  # Get the data block, default to an empty dictionary

        log.info("Received request %s", command)

        if command == "OPEN_CONNECT":
            oc_request = OpenConnectRequest.model_validate(data)
            uri_params = oc_request.get_uri_parameters()

            # Determine the interface
            try:
                session = Etsi004Session(self.config, self.peers_info, self.peer_manager, uri_params)
                log.info("Initializing new Etsi 004 session")
                response = session.open_connect(oc_request)
            except Exception as e:
                log.error("Exception during OPEN_CONNECT: %s", e)
                return {"status": 1, "message": "Fatal error during OPEN_CONNECT."}

            if response["status"] == 0:
                with self.sessions_dicts_lock:
                    self.open_sessions[response["key_stream_id"]] = session
                    self.sessions_locks[response["key_stream_id"]] = threading.Lock()

            log.info("OPEN_CONNECT finished with response: %s", response)
            return response

        elif command == "GET_KEY":
            gk_request = GetKeyRequest.model_validate(data)

            # Use the previously selected interface
            with self.sessions_dicts_lock:
                if gk_request.key_stream_id not in self.open_sessions:
                    return {"status": 1, "message": "No interface selected. OPEN_CONNECT must be called first."}

                session = self.open_sessions[gk_request.key_stream_id]
                session_lock = self.sessions_locks[gk_request.key_stream_id]

            log.info("Routing GET_KEY to %s interface.", gk_request.key_stream_id)
            try:
                with session_lock:
                    return session.get_key(gk_request)

            except Exception as e:
                log.error("Exception during %s GET_KEY: %s", gk_request.key_stream_id, e)
                return {"status": 1, "message": "Fatal error during GET_KEY."}

        elif command == "CLOSE":
            cl_request = CloseRequest.model_validate(data)

            # Use the previously selected interface
            with self.sessions_dicts_lock:
                if cl_request.key_stream_id not in self.open_sessions:
                    return {"status": 1, "message": "No interface selected. OPEN_CONNECT must be called first."}

                session = self.open_sessions.pop(cl_request.key_stream_id)
                session_lock = self.sessions_locks.pop(cl_request.key_stream_id)

            log.info("Routing CLOSE to %s interface.", cl_request.key_stream_id)
            try:
                with session_lock:
                    return session.close(cl_request)

            except Exception as e:
                log.error("Exception during %s CLOSE: %s", cl_request.key_stream_id, e)
                return {"status": 1, "message": "Fatal error during CLOSE."}

        else:
            return {"status": "error", "message": "Unknown command"}

    def _handle_connection(self, connection_socket: socket.socket, addr: NetworkAddress) -> None:

        with connection_socket:
            log.info("Connection established with AGENT at %s", addr)
            while True:
                data = connection_socket.recv(65057)
                if not data:
                    log.info("Connection closed by AGENT at %s", addr)
                    break

                # Handle the received data (assuming JSON requests)
                try:
                    request = json.loads(data.decode('utf-8'))
                    response = self._process_request(request)
                except json.JSONDecodeError:
                    response = {"status" : "error", "message" : "Invalid JSON received"}

                if "status" in response:
                    log.info("Sending response to %s. Status=%s", addr, response["status"])
                else:
                    log.warning("Sending response without status to %s.", addr)

                # Send the response back to the client
                log.debug("Response: %s", response)
                connection_socket.sendall(json.dumps(response).encode('utf-8'))

        log.info("Request flow with AGENT %s completed.", addr)


    def start_server(self) -> None:
        self.peer_manager.start_listening()
        thread_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="request")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(self.config.hybridization_server_address.to_tuple())
            server_socket.listen()
            log.info("Server listening on %s", self.config.hybridization_server_address)

            try:
                while True:
                    conn, addr = server_socket.accept()
                    thread_pool.submit(self._handle_connection, conn, NetworkAddress.from_tuple(addr))

            except KeyboardInterrupt:
                thread_pool.shutdown(wait=True)
                self.peer_manager.stop_listening()
                log.info("Shutting down server gracefully...")
                sys.exit(0)


