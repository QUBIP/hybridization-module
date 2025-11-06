import hashlib
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel

from hybridization_module.model.shared_enums import HybridizationMethod, KeyExtractionAlgorithm

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
    key_algorithms: list[KeyExtractionAlgorithm]


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

        query_key_sources = parsed_qs["key_sources"][0].split(",")
        key_algorithms = []

        for algorithm in query_key_sources:
            key_algorithms.append(KeyExtractionAlgorithm(algorithm))

        uri_params = OpenConnectUriParameters(
            source_uuid=source_uuid,
            destination_uuid=destination_uuid,
            hybrid_method=hybrid_method,
            key_algorithms=key_algorithms
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