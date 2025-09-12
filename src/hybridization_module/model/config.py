from pydantic import BaseModel

from hybridization_module.model.shared_enums import LogType
from hybridization_module.model.shared_types import NetworkAddress


class LoggingConfiguration(BaseModel):
    console_log_type: LogType
    colorless_console_log: bool

    file_log_type: LogType
    filename: str

class CertificateConfiguration(BaseModel):
    certificate_ip: str
    cert_authority_path: str
    cert_path: str
    key_path: str

class GeneralConfiguration(BaseModel):
    uuid: str

    logging_config: LoggingConfiguration
    certificate_config: CertificateConfiguration
    hybridization_server_address: NetworkAddress
    peer_local_address: NetworkAddress
    qkd_address: NetworkAddress


# ---- Trusted Peers info

class PeerInfo(BaseModel):
    shared_seed: str
    address: NetworkAddress


class TrustedPeerInfoValidator(BaseModel):
    peers_info: dict[str, PeerInfo]