import json
import logging
import socket
import ssl
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from ssl import SSLContext

from hybridization_module.model.config import CertificateConfiguration
from hybridization_module.model.exceptions import PeerNotConnectedError
from hybridization_module.model.shared_enums import ConnectionRole, PeerSessionType
from hybridization_module.model.shared_types import NetworkAddress, PeerSessionReference
from hybridization_module.peer_connector.connector_interface import PeerConnectionManager

log = logging.getLogger(__name__)

class PeerToPeerConnectionManager(PeerConnectionManager):

    def __init__(self, address: NetworkAddress, cert_config: CertificateConfiguration) -> None:

        self.address = address
        self.timeout = 10 # Seconds the receiving peer (get_data) will wait for a message until it throws an exception

        self._listening_thread: threading.Thread = None
        self._continue_listening: bool = False

        self._unclaimed_sockets: dict[PeerSessionReference, socket.socket] = {}
        self._sockets_dict_lock: threading.Lock = threading.Lock()

        self._server_ssl_context: SSLContext = self._setup_ssl_context(ssl.Purpose.CLIENT_AUTH, cert_config)
        self._client_ssl_context: SSLContext = self._setup_ssl_context(ssl.Purpose.SERVER_AUTH, cert_config)


    def _setup_ssl_context(self, ssl_purpose: ssl.Purpose, cert_config: CertificateConfiguration) -> SSLContext:
        context = ssl.create_default_context(ssl_purpose)
        context.load_cert_chain(certfile=cert_config.cert_path, keyfile=cert_config.key_path)
        context.load_verify_locations(cert_config.cert_authority_path)
        context.verify_mode = ssl.CERT_REQUIRED
        return context

    def _process_peer_connection(self, new_socket: socket.socket) -> None:
        encoded_message = new_socket.recv(1024)
        json_message = json.loads(encoded_message.decode())
        log.debug("Received the following JSON: %s", json_message)
        session_type = PeerSessionType(json_message["session_type"])

        if session_type == PeerSessionType.BLINK:
            log.debug("The peer connection server blinked.")
            return

        message_ref = PeerSessionReference(type=session_type, id=json_message["id"])
        with self._sockets_dict_lock:
            self._unclaimed_sockets[message_ref] = new_socket
            log.info("Peer connection with reference %s registered.", message_ref)


    def _listen_to_peers(self) -> None:
        peer_listener_thread_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix="peer_connection")

        log.info("Listening to peers at %s", self.address)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(self.address.to_tuple())
            sock.listen()
            while self._continue_listening:
                try:
                    connection_socket, addr = sock.accept()
                    secure_socket = self._server_ssl_context.wrap_socket(connection_socket, server_side=True)
                    log.debug("Accepted client connection.")

                    peer_listener_thread_pool.submit(self._process_peer_connection, secure_socket)
                except Exception as e:
                    log.error("Failed to accept or process client connection: %s", e)

        peer_listener_thread_pool.shutdown(wait=True)


    def _connect_as_server(self, session_ref: PeerSessionReference) -> socket.socket:
        starting_time = time.time()
        log.debug("Starting seach for session with type %s and id %s", session_ref.type, session_ref.id)

        while self.timeout > time.time()-starting_time:
            if session_ref in self._unclaimed_sockets:
                log.debug("Found a socket matching the type %s and id %s.", session_ref.type, session_ref.id)
                with self._sockets_dict_lock:
                    secure_socket = self._unclaimed_sockets.pop(session_ref)

                secure_socket.settimeout(self.timeout)
                secure_socket.sendall("ok".encode())
                log.info("Peer session %s established with %s.", session_ref, secure_socket.getpeername())
                return secure_socket
            time.sleep(0.2)

        log.error("After %s seconds, the client did not connect.", self.timeout)
        raise PeerNotConnectedError("The client peer did not start the session")


    def _connect_as_client(self, target: NetworkAddress, session_ref: PeerSessionReference) -> socket.socket:

        log.debug("Preparing for session with type %s and id %s", session_ref.type, session_ref.id)
        message = {
            "session_type" : session_ref.type.value,
            "id" : session_ref.id,
        }
        encoded_message = json.dumps(message).encode()

        raw_socket = socket.create_connection(target.to_tuple())
        secure_socket = self._client_ssl_context.wrap_socket(raw_socket, server_hostname=target.host)
        secure_socket.settimeout(self.timeout)

        log.debug("Sending server peer reference to server: %s", message)
        secure_socket.sendall(encoded_message)
        secure_socket.recv(256)

        log.info("Peer session %s established with %s.", session_ref, target)
        return secure_socket

    def start_listening(self) -> None:
        if self._listening_thread is not None and self._listening_thread.is_alive():
            log.warning("Cannot start the peer connection manager because it is already started.")
            return

        self._listening_thread = threading.Thread(
            target=self._listen_to_peers, name="peer_manager_listener"
        )

        self._continue_listening = True
        self._listening_thread.start()
        log.debug("Peer connection manager listener thread started.")

    def stop_listening(self) -> None:
        if self._listening_thread is None or not self._listening_thread.is_alive():
            log.warning("Cannot close the peer connection manager because it is already closed.")
            return

        self._continue_listening = False
        sock = self._connect_as_client(self.address, PeerSessionReference(PeerSessionType.BLINK, "blink"))
        sock.close()

        self._listening_thread.join()
        log.info("The peer connection manager has stopped listening as asked.")
        self._listening_thread = None

    def connect_peer(self, session_ref: PeerSessionReference, role: ConnectionRole, target: NetworkAddress) -> socket.socket:

        if role == ConnectionRole.SERVER:
            return self._connect_as_server(session_ref)
        elif role == ConnectionRole.CLIENT:
            return self._connect_as_client(target, session_ref)
        else:
            raise ValueError(f"Invalid role. Must be {ConnectionRole.CLIENT} or {ConnectionRole.SERVER}.")

