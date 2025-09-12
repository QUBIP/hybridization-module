#kdfix/interface/interface_etsi004.py


import logging
import threading
import uuid

from hybridization_module.hybridization_functions.hmac import hmac_kdf
from hybridization_module.hybridization_functions.xorhmac import xorhmac_kdf
from hybridization_module.hybridization_functions.xoring import xoring_kdf
from hybridization_module.key_generation.key_emulation import generate_deterministic_aux_key
from hybridization_module.key_generation.key_source_interface import KeySource
from hybridization_module.key_generation.key_source_threads import (
    handle_close_thread,
    handle_get_key_thread,
    handle_open_connect_thread,
)
from hybridization_module.key_generation.sources.pqc_source import PQCSource
from hybridization_module.key_generation.sources.qkd_source import QKDSource
from hybridization_module.model.config import GeneralConfiguration, PeerInfo
from hybridization_module.model.exceptions import PeerNotConnectedError
from hybridization_module.model.requests import (
    CloseRequest,
    GetKeyRequest,
    OpenConnectQos,
    OpenConnectRequest,
    OpenConnectUriParameters,
)
from hybridization_module.model.shared_enums import (
    ConnectionRole,
    HybridizationMethod,
    PeerSessionType,
)
from hybridization_module.model.shared_types import NetworkAddress, PeerSessionReference
from hybridization_module.peer_connector.connector_interface import PeerConnectionManager

log = logging.getLogger(__name__)

# Maximun time in seconds for each source to fetch keys
TIMEOUT_SECONDS = 60

class Etsi004Session:

    ### Initialization ###

    def __init__(
            self,
            node_config: GeneralConfiguration,
            peers_info: dict[str, PeerInfo],
            peer_manager: PeerConnectionManager,
            uri_params: OpenConnectUriParameters
        ) -> None:
        """
        Initialize the ETSI004 interface with QKD and PQC configurations.
        """

        ## Get the connection role

        if node_config.uuid == uri_params.source_uuid:
            connection_role = ConnectionRole.CLIENT
        elif node_config.uuid == uri_params.destination_uuid:
            connection_role = ConnectionRole.SERVER
        else:
            log.error("Neither %s nor %s match with the local uuid of %s", uri_params.source_uuid, uri_params.destination_uuid, node_config.uuid)
            raise ValueError("The open connect request did not contain the local node uuid")

        log.info("Chosed the connection role %s.", connection_role)

        ## Finding peer information (self.peer)

        peer_uuid = uri_params.destination_uuid if connection_role == ConnectionRole.CLIENT else uri_params.source_uuid

        if peer_uuid not in peers_info:
            log.error("The hybridization module with uuid %s is not registered.", peer_uuid)
            return {"status" : 1, "message" : f"The hybridization module with uuid {peer_uuid} is not registered."}

        peer: PeerInfo = peers_info[peer_uuid]
        log.debug("Found the peer connection information %s.", peer)

        ## Get the key sources

        key_sources: dict[str, KeySource] = {}

        qkd_source = QKDSource(uri_params, node_config.qkd_address)
        key_sources[qkd_source.get_id()] = qkd_source

        pqc_source = PQCSource(
            peer_manager=peer_manager,
            peer_address=peer.address,
            role=connection_role,
            kem_algorithm=uri_params.pqc_algorithm
        )
        key_sources[pqc_source.get_id()] = pqc_source
        log.debug("Key sources initialized %s", key_sources)

        ## Initializing instance variables

        self.peer_manager: PeerConnectionManager = peer_manager
        self.role: ConnectionRole = connection_role
        self.peer: PeerInfo = peer

        self.qos: OpenConnectQos = None
        self.key_sources: dict[str, KeySource] = key_sources
        self.hybrid_method: HybridizationMethod = uri_params.hybrid_method
        log.debug("Etsi004Session initialized.")

    ### Open Connect ###

    def _share_ksid(self, connection_id: str, target: NetworkAddress) -> uuid.UUID:
        session_ref = PeerSessionReference(
            type=PeerSessionType.SHARE_KSID,
            id=connection_id
        )

        log.debug("Connecting peer %s to get the ksid of the session.", target)
        with self.peer_manager.connect_peer(session_ref, self.role, target) as sock:
            if self.role == ConnectionRole.CLIENT:
                ksid_bytes = uuid.uuid4().bytes
                log.debug("[CLIENT] Shared Hybrid KSID generated. Sending it to the server.")
                sock.sendall(ksid_bytes)
            elif self.role == ConnectionRole.SERVER:
                log.debug("[SEVER] Waiting for connection ksid.")
                ksid_bytes = sock.recv(16)
            else:
                raise ValueError(f"Invalid role. Must be {ConnectionRole.CLIENT} or {ConnectionRole.SERVER}.")

        return str(uuid.UUID(bytes=ksid_bytes))


    def open_connect(self, oc_request: OpenConnectRequest) -> dict:
        """
        Handles OPEN_CONNECT requests.
        Saves the key chunk size and hybrid method in the key stream state.

        Args:
            oc_request (OpenConnectRequest): The data of the OPEN_CONNECT request aimed to start this session.

        Returns:
            dict: Response with status and key_stream_id.
        """
        self.qos = oc_request.qos

        try:
            # Generate a key_stream_id of the hybrid session
            hybrid_ksid = self._share_ksid(oc_request.get_connection_id(), self.peer.address)
            log.info("Hybrid ksid generated with %s: %s", self.peer.address, hybrid_ksid)
        except (PeerNotConnectedError, TimeoutError, RuntimeError) as e:
            log.error("Failed to share ksid with %s: %s", self.peer.address, e)
            return {"status": 1, "message": str(e)}


        # Initiate arrays for threading flow
        threads: list[threading.Thread] = []
        results = {}
        results_lock = threading.Lock()

        for key_source_id, key_source in self.key_sources.items():
            log.debug("Starting OPEN_CONNECT thread for %s", key_source.get_id())
            oc_thread = threading.Thread(
                target=handle_open_connect_thread,
                args=(key_source, hybrid_ksid, self.qos, results, results_lock),
                name=key_source_id[:12],
            )
            oc_thread.start()
            threads.append(oc_thread)

        for t in threads:
            t.join()
            if t.is_alive():
                log.warning("Thread %s exceeded timeout and is still running.", t.name)

        if not results:
            log.error("None of the sources could open connect, sending error response to agent.")
            return {"status": 1, "message": "None of the key sources could open connect."}

        failed_key_sources_ids = []
        for key_source_id, key_source in self.key_sources.items():
            if key_source_id not in results:
                failed_key_sources_ids.append(key_source_id)

        for key_source_id in failed_key_sources_ids:
            log.warning("The source %s failed to open connect, removing it from available key sources for future operations.", key_source_id)
            self.key_sources.pop(key_source_id)

        # Respond with the key_stream_id
        return {"status": 0, "key_stream_id": hybrid_ksid}

    ### Get Key ###

    def get_key(self, gk_request: GetKeyRequest) -> dict:
        """
        Handles GET_KEY requests.
        Retrieves keys from sources and hybridizes them.

        Args:
            request_gk (GetKeyRequest): The data of a GET_KEY request aimed to this session.

        Returns:
            dict: Response with status and key buffer.
        """

        # Initiate arrays for threading flow
        threads: list[threading.Thread] = []
        results = {}
        results_lock = threading.Lock()

        for key_source_id, key_source in self.key_sources.items():
            log.debug("Starting GET_KEY thread for %s", key_source.get_id())
            qk_thread = threading.Thread(
                target=handle_get_key_thread,
                args=(key_source, results, results_lock),
                name=key_source_id[:12],
            )
            qk_thread.start()
            threads.append(qk_thread)

        for t in threads:
            t.join()
            if t.is_alive():
                log.warning("Thread %s exceeded timeout and is still running.", t.name)

        # If no keys were fetched, return an error
        if not results:
            return {"status": 1, "message": "Failed to fetch any keys from sources"}

        log.debug("Fetched key dict: %s", results)

        # Check if key_dict has only one key, and add an auxiliary entry if needed
        if len(results) < 2:
            # Generate the deterministic auxiliary key
            key_length = len(next(iter(results.values())))
            aux_key = generate_deterministic_aux_key(self.peer.shared_seed, key_length)

            # Add the auxiliary key to the dictionary as a list of lists
            results.update({"aux": bytes(aux_key)})

            log.debug("Single key hybridization not allowed. Deterministic Aux key added to hybridize")
            log.debug("Updated Key dict with aux: %s", results)


        keys = list(results.values())
        if not all(isinstance(key, bytes) for key in keys):
            raise TypeError("All keys must be bytes.")

        log.info("Key generation completed, starting key hybridization proccess using %s.", self.hybrid_method)

        keys.sort() # We do this to ensure the order of the keys is the same in both modules.

        if self.hybrid_method == HybridizationMethod.XOR:
            hybrid_key = xoring_kdf(keys, self.qos.key_chunk_size)
        elif self.hybrid_method == HybridizationMethod.HMAC:
            hybrid_key = hmac_kdf(keys)
        elif self.hybrid_method == HybridizationMethod.XORHMAC:
            hybrid_key = xorhmac_kdf(keys, self.qos.key_chunk_size)
        else:
            return {"status": 1, "message": "Unknown hybrid method"}

        # Truncate the hybrid key to the specified chunk_size
        if len(hybrid_key) > self.qos.key_chunk_size:
            hybrid_key = hybrid_key[:self.qos.key_chunk_size]

        # Respond with the hybrid key
        log.info("Keys successfully hybridazed using %s.", self.hybrid_method)
        log.debug("Hybrid Key: %s", list(hybrid_key))

        return {
            "status": 0,
            "key_buffer": list(hybrid_key)
        }

    ### Close ###

    def close(self, cl_request: CloseRequest) -> dict:
        """
        Handles CLOSE requests.
        Removes the key_stream_id from memory.

        Args:
            cl_request (CloseRequest): The data of a CLOSE request aimed to this session.

        Returns:
            dict: Response with status.
        """

        threads: list[threading.Thread] = []

        for key_source_id, key_source in self.key_sources.items():
            log.debug("Starting CLOSE thread for %s", key_source.get_id())
            cl_thread = threading.Thread(
                target=handle_close_thread,
                args=(key_source ,),
                name=key_source_id[:12],
            )
            cl_thread.start()
            threads.append(cl_thread)

        for t in threads:
            t.join()
            if t.is_alive():
                log.warning("Thread %s exceeded timeout and is still running.", t.name)

        return {"status" : 0}