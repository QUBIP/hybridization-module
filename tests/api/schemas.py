from pydantic import BaseModel
from typing import Dict, List

class HybridKeyRequest(BaseModel):
    """Schema for requesting a hybrid key negotiation."""
    remote_uuid: str  # The UUID of the node to connect with
    session_params: Dict  # Parameters for the session negotiation

class HybridKeyResponse(BaseModel):
    """Schema for the hybrid key response."""
    status: int  # Status code
    key_material: List[int] # List of integers representing the bytes
    key_stream_id: str

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str  # Error message details

class QoSParams(BaseModel):
    key_chunk_size: int
    max_bps: int
    min_bps: int
    jitter: int
    priority: int
    timeout: int
    ttl: int
    metadata_mimetype: str

class OpenConnectData(BaseModel):
    source: str
    destination: str
    qos: QoSParams

class OpenConnectRequest(BaseModel):
    command: str
    data: OpenConnectData