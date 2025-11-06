#kdfix/key/pqc_source.py
import logging
import socket
from uuid import uuid4

import oqs

from hybridization_module.key_generation.key_source_interface import KeySource
from hybridization_module.model.exceptions import PqcError
from hybridization_module.model.requests import OpenConnectQos
from hybridization_module.model.shared_enums import (
    ConnectionRole,
    KeyExtractionAlgorithm,
    KeyType,
    PeerSessionType,
)
from hybridization_module.model.shared_types import NetworkAddress, PeerSessionReference
from hybridization_module.peer_connector.connector_interface import PeerConnectionManager
from hybridization_module.utils.io_utils import receive_nbytes

log = logging.getLogger(__name__)

class PQCSource(KeySource):
    def __init__(
        self,
        peer_manager: PeerConnectionManager,
        peer_address: NetworkAddress,
        role: ConnectionRole,
        kem_algorithm: KeyExtractionAlgorithm = KeyExtractionAlgorithm.KYBER512,
        kem_appearance_index: int = 0,
        sig_algorithm: str = None) -> None:
        """
        Initializes the PQC Link using the node, and with a specified KEM and optional signature mechanism.

        Args:
            peer_manager (PeerConnectionManager): The peer connection manager of the hybridization module.
            peer_addres (NetworkAddress): The address of the hybridization with which the key is going to be generated.
            role (ConnectionRole): The role the local hybridization module is going to take in the connection.
            kem_algorithm (str): The KEM algorithm to use (default: 'Kyber512').
            kem_appearance_index (int): The number of souces that have the same kem_algorithm when the PQCSource was created.
            sig_algorithm (str): The signature algorithm to use (optional).
        """
        self.id: str = f"{self.get_key_type()}-{uuid4()}"
        log.debug("Initializing PQC source with id: %s", self.id)

        self.peer_manager: PeerConnectionManager = peer_manager
        self.peer_address: NetworkAddress = peer_address
        self.kem_algorithm: KeyExtractionAlgorithm = kem_algorithm
        self.kem_appearance_index: int = kem_appearance_index
        self.sig_algorithm = sig_algorithm
        self.role: ConnectionRole = role
        self.key_stream_id: str = None
        self.secure_socket: socket.socket = None

        if not self.kem_algorithm:
            raise ValueError("The PQC source cannot start because it is missing the pqc algorithm.")

        self.kem = oqs.KeyEncapsulation(self.kem_algorithm)

        log.debug("Configuration loaded:")
        log.debug("Role=%s", role)
        log.debug("KEM Mechanism=%s", self.kem_algorithm)
        log.debug("Appearance_index=%s", self.kem_appearance_index)

        if self.sig_algorithm:
            log.debug("Digital Signature Mechanism=%s", self.sig_algorithm)

        self.public_key = None

    @classmethod
    def get_key_type(cls) -> KeyType:
        return KeyType.PQC

    def get_id(self) -> str:
        return self.id

    ### Open Connect ###

    def open_connect(self, hybrid_ksid: str, qos: OpenConnectQos, timeout: int = 10) -> None:
        """Implements the open_connect method from KeySource.

        Starts the socket connection between the peers so that they can exchange PQC information.
        """

        peer_session_id = f"{self.kem_algorithm}-{self.kem_appearance_index}-{hybrid_ksid}"
        peer_session_ref = PeerSessionReference(type=PeerSessionType.PQC, id=peer_session_id)
        self.secure_socket = self.peer_manager.connect_peer(peer_session_ref, self.role, self.peer_address)
        self.key_stream_id = hybrid_ksid

    ### Get Key ###

    def _client_side_get_key(self) -> bytes:

        # CLIENT: Generates keypair, send public key, and receives ciphertext to get the shared secret
        public_key = self.kem.generate_keypair()
        log.debug("[CLIENT] Public key generated, sending it to server...")

        self.secure_socket.sendall(public_key)
        log.debug("[CLIENT] Server received public key. Waiting for ciphertext...")

        ciphertext = receive_nbytes(self.secure_socket, self.kem.details["length_ciphertext"])
        log.debug("[CLIENT] Received ciphertext, starting decapsulation...")

        shared_secret= self.kem.decap_secret(ciphertext)
        log.debug("[CLIENT] Shared secret decapsulated. GET KEY completed successfully.", )
        return  shared_secret


    def _server_side_get_key(self) -> bytes:

        # SEVER: Receives public key from the secure socket and sends the ciphertext.
        public_key = receive_nbytes(self.secure_socket, self.kem.details["length_public_key"])
        log.debug("[SERVER] Received public key, encapsulating secret...")

        ciphertext, shared_secret = self.kem.encap_secret(public_key)
        log.debug("[SERVER] Shared secret encapsulated. Sending ciphertext to client.")

        self.secure_socket.sendall(ciphertext)  # Send back shared secret
        log.debug("[SERVER] Client received ciphertext. GET KEY completed successfully.")
        return shared_secret

    def get_key(self, retries: int = 5, timeout: int = 10) -> bytes:
        """Implements the get_key method from KeySource.

        Performs the key exchange process based on the role.
        - CLIENT: Generates keypair, sends public key, and receives ciphertext to get the shared secret
        - SERVER: Receives public key from the secure socket and sends the ciphertext.

        Raises:
            PQCException: If the key exchange fails after all retries.
        """
        # delay = 1
        self.secure_socket.settimeout(timeout)

        if not self.secure_socket:
            raise PqcError(f"[{self.role}] Secure socket not established")
        try:
            if self.role == ConnectionRole.CLIENT:
                return self._client_side_get_key()
            elif self.role == ConnectionRole.SERVER:
                return self._server_side_get_key()
            else:
                raise ValueError(f"Invalid role: must be {ConnectionRole.CLIENT} or {ConnectionRole.SERVER}")
        except Exception as e:
            log.error("[%s] Failure Getting key for KSID %s: %s", self.role, self.key_stream_id, e)
            raise e


    ### Close ###

    def close(self) -> None:
        """Implements the close method from KeySource.

        Closes the socket connection.
        """
        if self.secure_socket:
            try:
                self.secure_socket.close()
                log.debug("%s socket connection closed", self.id)
            except Exception as e:
                log.error("Failed to close the connection for %s: %s", self.id, e)
            finally:
                self.secure_socket = None
