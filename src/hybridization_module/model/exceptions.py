# kdfix/utils/exceptions.py

class QkdError(Exception):
    """Base exception for QKD-related errors."""
    pass

class PqcError(Exception):
    """Base exception for PQC-related errors."""
    pass

class PeerNotConnectedError(QkdError):
    """Exception raised when peer is not connected."""
    pass

class InsufficientKeyError(QkdError):
    """Exception raised when GET_KEY fails due to insufficient key availability."""
    pass

class PeerApplicationNotConnectedError(QkdError):
    """Exception raised when peer application is not connected."""
    pass

class NoQKDConnectionError(QkdError):
    """Exception raised when no QKD connection is available."""
    pass

class KSIDInUseError(QkdError):
    """Exception raised when the KSID is already in use."""
    pass

class TimeoutError(QkdError):
    """Exception raised when a timeout occurs."""
    pass

class QoSSettingsError(QkdError):
    """Exception raised when QoS settings could not be met."""
    pass

class MetadataSizeError(QkdError):
    """Exception raised when the metadata buffer size is insufficient."""
    pass


def check_status(status_code: int) -> None:
    """
    Check the status code from the KMS response and raise appropriate exceptions.

    Args:
        status_code (int): The status code returned by the KMS.

    Raises:
        QKDException: Based on the status code.
    """
    if status_code == 0:
        return  # Success, no error to raise
    elif status_code == 1:
        raise PeerNotConnectedError("Connection successful, but peer is not connected.")
    elif status_code == 2:
        raise InsufficientKeyError("GET_KEY failed due to insufficient key availability.")
    elif status_code == 3:
        raise PeerApplicationNotConnectedError("GET_KEY failed because peer application is not connected.")
    elif status_code == 4:
        raise NoQKDConnectionError("No QKD connection is available.")
    elif status_code == 5:
        raise KSIDInUseError("OPEN_CONNECT failed because the KSID is already in use.")
    elif status_code == 6:
        raise TimeoutError("The call failed due to the specified TIMEOUT.")
    elif status_code == 7:
        raise QoSSettingsError("OPEN failed because requested QoS settings could not be met.")
    elif status_code == 8:
        raise MetadataSizeError("GET_KEY failed because the metadata buffer size is insufficient.")
    else:
        raise QkdError(f"Unknown error with status code {status_code}.")
