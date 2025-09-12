
from typing import Self

from pydantic import BaseModel, ConfigDict

from hybridization_module.model.shared_enums import PeerSessionType


class NetworkAddress(BaseModel):
    model_config = ConfigDict(frozen=True)

    host: str
    port: int

    def __str__(self) -> str:
        return f"{self.host}:{self.port}"

    @classmethod
    def from_tuple(cls, address_tuple: tuple[str, int]) -> Self:
        return NetworkAddress(host=address_tuple[0], port=address_tuple[1])

    def to_tuple(self)->tuple[str, int]:
        return (self.host, self.port)


class PeerSessionReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: PeerSessionType
    id: str

class LogTypeInformation(BaseModel):
    model_config = ConfigDict(frozen=True)

    level: int # They must be types like logging.DEBUG, logging.INFO, etc.