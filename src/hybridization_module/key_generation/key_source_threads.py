import logging
import threading

from hybridization_module.key_generation.key_source_interface import KeySource
from hybridization_module.model.requests import OpenConnectQos

log = logging.getLogger(__name__)

def handle_open_connect_thread(
    source: KeySource,
    hybrid_ksid: str,
    qos: OpenConnectQos,
    results_dict: dict,
    results_lock: threading.Lock
) -> None:

    source_id = source.get_id()
    try:
        log.info("Attempting to OPEN CONNECTION with %s...", source_id)
        source.open_connect(hybrid_ksid, qos)
        log.info("OPEN CONNECT succesful at %s.", source_id)

        with results_lock:
            results_dict[source_id] = True

    except Exception as e:
        log.error("Failed OPEN CONNECT in %s: %s", source_id, e)

def handle_get_key_thread(source: KeySource, results_dict: dict, results_lock: threading.Lock) -> None:

    source_id = source.get_id()
    try:
        log.info("Attempting to GET KEY from the %s source...", source_id)
        result = source.get_key()
        log.info("Obtained key from %s source.", source_id)

        with results_lock:
            results_dict[source_id] = result

    except Exception as e:
        log.error("Failed GET KEY from %s: %s", source_id, e)

def handle_close_thread(source: KeySource) -> None:

    source_id = source.get_id()
    try:
        log.info("Attempting to CLOSE the %s source...", source_id)
        source.close()
        log.info("Source %s closed.", source_id)
    except Exception as e:
        log.error("Failed CLOSE from %s: %s", source_id, e)
