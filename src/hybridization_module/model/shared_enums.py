from enum import Enum, StrEnum
from typing import Self

## Base classes


class CaseInsensitiveStrEnum(StrEnum):
    @classmethod
    def _missing_(cls, value: str) -> Self | None:
        if not isinstance(value, str):
            return None

        normalized_value = value.lower()
        for member in cls:
            if member.value.lower() == normalized_value:
                return member

        return None

## Configuration

class LogType(CaseInsensitiveStrEnum):
    NONE = "NONE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


## Connection coordinaton


class ConnectionRole(StrEnum):
    CLIENT = "CLIENT"
    SERVER = "SERVER"


class PeerSessionType(Enum):
    BLINK = 0  # Special command that just makes the peer session server do a roundtrip so it can stop
    SHARE_KSID = 1
    PQC = 2

## Key sources

class KeyType(StrEnum):
    QKD = "QKD"
    PQC = "PQC"

## Query parameters


class HybridizationMethod(CaseInsensitiveStrEnum):
    XOR = "xoring"
    HMAC = "hmac"
    XORHMAC = "xorhmac"


class PqcAlgorithm(CaseInsensitiveStrEnum):
    # Marked with an X, the algorithms that currently do not work

    ### Inherited from liboqs ###

    BIKE_L1 = "BIKE-L1"
    BIKE_L3 = "BIKE-L3"
    BIKE_L5 = "BIKE-L5"

    MCELIECE348864 = "Classic-McEliece-348864" # X Does not crash, but the key is not the same in both sides
    MCELIECE460896 = "Classic-McEliece-460896" # X Does not crash, but the key is not the same in both sides
    MCELIECE6688128 = "Classic-McEliece-6688128" # X Crashes on client side (Probably due to the side of the public key)
    MCELIECE6960119 = "Classic-McEliece-6960119" # X Crashes on client side (Probably due to the side of the public key)
    MCELIECE8192128 = "Classic-McEliece-8192128" # X Crashes on client side (Probably due to the side of the public key)

    MCELIECE348864_F = "Classic-McEliece-348864f" # X Does not crash, but the key is not the same in both sides
    MCELIECE460896_F = "Classic-McEliece-460896f" # X Does not crash, but the key is not the same in both sides
    MCELIECE6688128_F = "Classic-McEliece-6688128f" # X Crashes on client side (Probably due to the side of the public key)
    MCELIECE6960119_F = "Classic-McEliece-6960119f" # X Crashes on client side (Probably due to the side of the public key)
    MCELIECE8192128_F = "Classic-McEliece-8192128f" # X Crashes on client side (Probably due to the side of the public key)

    HQC_128 = "HQC-128"
    HQC_192 = "HQC-192"
    HQC_256 = "HQC-256"

    KYBER512 = "Kyber512"
    KYBER768 = "Kyber768"
    KYBER1024 = "Kyber1024"

    ML_KEM512 = "ML-KEM-512"
    ML_KEM768 = "ML-KEM-768"
    ML_KEM1024 = "ML-KEM-1024"

    SNTRUP761 = "sntrup761"

    FRODO_KEM_640_AES = "FrodoKEM-640-AES"
    FRODO_KEM_976_AES = "FrodoKEM-976-AES"
    FRODO_KEM_1344_AES = "FrodoKEM-1344-AES" # X Does not crash, but the key is not the same in both sides

    FRODO_KEM_640_SHAKE = "FrodoKEM-640-SHAKE"
    FRODO_KEM_976_SHAKE = "FrodoKEM-976-SHAKE"
    FRODO_KEM_1344_SHAKE = "FrodoKEM-1344-SHAKE" # X Does not crash, but the key is not the same in both sides
