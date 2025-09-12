
import socket
from abc import ABC, abstractmethod

from hybridization_module.model.shared_enums import ConnectionRole
from hybridization_module.model.shared_types import NetworkAddress, PeerSessionReference


class PeerConnectionManager(ABC):

    @abstractmethod
    def start_listening(self) -> None:
        """Starts the connection manager server, this server will listen to any incoming
        connections and assign them a socket and a PeerSessionReference.

        This sockets can then be retrieced using connect_peer()
        """
        pass

    @abstractmethod
    def stop_listening(self) -> None:
        """Stops the peer connection manager server, and therefore stops accepting
        new sessions. However, unclaimed sessions can still be retrieved.
        """
        pass

    @abstractmethod
    def connect_peer(self, session_ref: PeerSessionReference, role: ConnectionRole, target: NetworkAddress) -> socket.socket:
        """Returns a socket that connect you to the peer with the same session_ref.

        Depending on the role, this method will send the session_ref to the other peer to
        start the session (CLIENT) or retrieve the new session from the connection manager (SERVER)

        Args:
            session_ref (PeerSessionReference): Unique identifier of the session you want to create.
            role (ConnectionRole): Role in the connection (SERVER or CLIENT).
            target (NetworkAddress): Network address of the other peer.

        Returns:
            socket.socket: Reserved socket that should be used for the purpose
            defined in session_ref.type
        """
        pass