import hashlib
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel

from hybridization_module.model.shared_enums import HybridizationMethod, PqcAlgorithm

# OPEN CONNECT

class  OpenConnectQos(BaseModel):
    key_chunk_size: int
    max_bps: int
    min_bps: int
    jitter: int
    priority: int
    timeout: int
    ttl: int
    metadata_mimetype: str


class OpenConnectUriParameters(BaseModel):
    source_uuid: str
    destination_uuid: str
    hybrid_method: HybridizationMethod
    pqc_algorithm: PqcAlgorithm


class OpenConnectRequest(BaseModel):
    source: str
    destination: str
    qos: OpenConnectQos

    def get_uri_parameters(self) -> OpenConnectUriParameters:
        # Parse URIs
        try:
            parsed_source_uri = urlparse(self.source)
            parsed_destination_uri = urlparse(self.destination)
        except Exception as e:
            raise ValueError(f"Invalid URI format: {e}")

        source_uuid = parsed_source_uri.netloc.split("@")[1]
        destination_uuid = parsed_destination_uri.netloc.split("@")[1]

        parsed_qs = parse_qs(parsed_source_uri.query)
        hybrid_method = HybridizationMethod(parsed_qs["hybridization"][0])
        pqc_kem_mec = PqcAlgorithm(parsed_qs["kem_mec"][0])

        uri_params = OpenConnectUriParameters(
            source_uuid=source_uuid,
            destination_uuid=destination_uuid,
            hybrid_method=hybrid_method,
            pqc_algorithm=pqc_kem_mec
        )
        return uri_params

    def get_connection_id(self) -> str:
        undigested_id = hashlib.sha256(f"{self.source}{self.destination}".encode())
        return undigested_id.digest().hex()



# GET KEY

class GetKeyMetadata(BaseModel):
    size: int = 30 # Size of the metadata buffer
    buffer: str = "The metadata field is not used"

class GetKeyRequest(BaseModel):
    key_stream_id: str
    index: int
    metadata: GetKeyMetadata = GetKeyMetadata()

# CLOSE

class CloseRequest(BaseModel):
    key_stream_id: str