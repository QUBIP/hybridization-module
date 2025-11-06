
from hybridization_module.model.shared_enums import KeyExtractionAlgorithm, KeyType

KEY_ALGORITHM_TO_KEY_TYPE = {

    ### QKD ###

    KeyExtractionAlgorithm.QKD : KeyType.QKD,

    ### PQC ###

    KeyExtractionAlgorithm.BIKE_L1: KeyType.PQC,
    KeyExtractionAlgorithm.BIKE_L3: KeyType.PQC,
    KeyExtractionAlgorithm.BIKE_L5: KeyType.PQC,

    KeyExtractionAlgorithm.MCELIECE348864: KeyType.PQC,
    KeyExtractionAlgorithm.MCELIECE460896: KeyType.PQC,
    KeyExtractionAlgorithm.MCELIECE6688128: KeyType.PQC,
    KeyExtractionAlgorithm.MCELIECE6960119: KeyType.PQC,
    KeyExtractionAlgorithm.MCELIECE8192128: KeyType.PQC,

    KeyExtractionAlgorithm.MCELIECE348864_F: KeyType.PQC,
    KeyExtractionAlgorithm.MCELIECE460896_F: KeyType.PQC,
    KeyExtractionAlgorithm.MCELIECE6688128_F: KeyType.PQC,
    KeyExtractionAlgorithm.MCELIECE6960119_F: KeyType.PQC,
    KeyExtractionAlgorithm.MCELIECE8192128_F: KeyType.PQC,

    KeyExtractionAlgorithm.HQC_128: KeyType.PQC,
    KeyExtractionAlgorithm.HQC_192: KeyType.PQC,
    KeyExtractionAlgorithm.HQC_256: KeyType.PQC,

    KeyExtractionAlgorithm.KYBER512: KeyType.PQC,
    KeyExtractionAlgorithm.KYBER768: KeyType.PQC,
    KeyExtractionAlgorithm.KYBER1024: KeyType.PQC,

    KeyExtractionAlgorithm.ML_KEM512: KeyType.PQC,
    KeyExtractionAlgorithm.ML_KEM768: KeyType.PQC,
    KeyExtractionAlgorithm.ML_KEM1024: KeyType.PQC,

    KeyExtractionAlgorithm.SNTRUP761: KeyType.PQC,

    KeyExtractionAlgorithm.FRODO_KEM_640_AES: KeyType.PQC,
    KeyExtractionAlgorithm.FRODO_KEM_976_AES: KeyType.PQC,
    KeyExtractionAlgorithm.FRODO_KEM_1344_AES: KeyType.PQC,

    KeyExtractionAlgorithm.FRODO_KEM_640_SHAKE: KeyType.PQC,
    KeyExtractionAlgorithm.FRODO_KEM_976_SHAKE: KeyType.PQC,
    KeyExtractionAlgorithm.FRODO_KEM_1344_SHAKE: KeyType.PQC,
}