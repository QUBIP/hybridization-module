#kdfix/interface/interface_etsi004.py

import signal

from function.hmac import hmac_kdf_dict
from function.xorhmac import xorhmac_kdf_dict
from function.xoring import xoring_kdf_dict
from key.pqc_source import PQCSource
from key.qkd_source import QKDSource
from utils.aux_key import generate_deterministic_aux_key
from utils.colorlog import color_log
from utils.enc_code import form_key
from utils.key_stream import load_key_streams, save_key_streams, delete_key_streams
from utils.handle_request import parse_oc_request, generate_ksid, transform_qkd_request_oc
from utils.pqc_config import link_config
from utils.timeout import timeout_handler, TimeoutException

# Maximun time in seconds for each source to fetch keys
TIMEOUT_SECONDS = 10
signal.signal(signal.SIGALRM, timeout_handler)

class ETSI004:
    def __init__(self, node_config):
        """
        Initialize the ETSI004 interface with QKD and PQC configurations.

        """
        self.node_config = node_config
        # Initialize QKDSource
        self.qkd_source = None
        self.qkd_ksid = None  # from QKDSource response of OPEN CONNECT
        # Initialize PQCSource
        self.pqc_source = None
        self.pqc_pair = None  # Store the selected PQC pair for reuse
        self.pqc_link = None  # will be True if PQC LINK is connected



    def OPEN_CONNECT(self, request_oc):
        """
        Handles OPEN_CONNECT requests.
        Saves the key chunk size and hybrid method in the key stream state.
        
        Args:
            request_oc (dict): Request containing the chunk size and hybridization method.
            
        Returns:
            dict: Response with status and key_stream_id.
        """
        source_uuid, destination_uuid, hybrid_method, pqc_kem_mec, chunk_size = parse_oc_request(request_oc)
        color_log("KDFIX", "INFO",f"Requesting Hybrid Method: {hybrid_method} and chunk_size={chunk_size}")

        # FIXME Here the KSID is generated and this is differents for both nodes
        key_stream_id = generate_ksid(source_uuid, destination_uuid)

        key_streams = load_key_streams()

        key_streams[key_stream_id] = {
            'chunk_size': chunk_size,
            'hybrid_method': hybrid_method
        }
        # Save key_streams to file after updating
        save_key_streams(key_streams)


        # Config QKDSource and PQCSource depending on the Parsed Open Connect Request
        qkd_request_oc = transform_qkd_request_oc(request_oc)
        self.qkd_source = QKDSource(qkd_request_oc, tuple(self.node_config["local_node"]["qkd_address"]))

        pqc_link, pqc_address, pqc_role, self.pqc_pair = link_config(self.node_config, source_uuid, destination_uuid)
        self.pqc_source =  PQCSource(
            pqc_link,
            pqc_address,
            pqc_role,
            pqc_kem_mec,
        )

        # OPEN CONNECTION to QKD Module
        try:
            # Set the time limit for the QKDSource to open connect
            signal.alarm(TIMEOUT_SECONDS)
            color_log("QKD", "INFO", "Attempting to OPEN CONNECTION with QKD Module...", "   ├── ")
            self.qkd_ksid = self.qkd_source.open_connect(chunk_size)
        except TimeoutException:
            color_log("QKD", "KO", f"Skipping QKD OPEN CONNECT. \n\t\tTimeout reached after {TIMEOUT_SECONDS} seconds.", "   ├── ")
        except Exception as e:
            color_log("QKD", "KO", f"Failed OPEN CONNECT from QKDSource: {e}", "   ├── ")
        finally:
            signal.alarm(0)  # Deactivate alarm

        # Open the PQC Link
        try:
            # Set the time limit for the QKDSource to open connect
            signal.alarm(TIMEOUT_SECONDS)
            color_log("PQC", "INFO", "Attempting to CONNECTION with PQC Link...", "   ├── ")
            self.pqc_link = self.pqc_source.connect_socket()
            color_log("PQC", "OK", "Link OPENED", "   ├── ")
        except TimeoutException:
            color_log("PQC", "KO", f"Skipping PQC OPEN CONNECT. \n\t\tTimeout reached after {TIMEOUT_SECONDS} seconds.", "   ├── ")
        except Exception as e:
            color_log("PQC", "KO", f"Failed OPEN CONNECT from PQC Source: {e}", "   ├── ")
        finally:
            signal.alarm(0)  # Deactivate alarm

        # Respond with the key_stream_id
        return {
            "status": 0,
            "key_stream_id": key_stream_id
        }

    def GET_KEY(self, request_gk):
        """
        Handles GET_KEY requests.
        Retrieves keys from sources and hybridizes them.
        
        Args:
            request_gk (dict): Request containing the key_stream_id.
            
        Returns:
            dict: Response with status and key buffer.
        """
        key_streams = load_key_streams()  # Load key streams from file
        
        key_stream_id = request_gk.get("key_stream_id")
        # Check if the key_stream_id exists
        if key_stream_id not in key_streams:
            return {"status": 1, "message": "Invalid key_stream_id"}

        # Get the chunk size and hybrid method for this stream
        key_chunk_size = key_streams[key_stream_id]["chunk_size"]
        hybrid_method = key_streams[key_stream_id]["hybrid_method"]

        key_dict = {}  # Dictionary to hold available keys

        try:
            # Set the time limit for the QKDSource to fetch keys
            signal.alarm(TIMEOUT_SECONDS)
            color_log("QKD", "INFO", "Attempting to GET KEY from QKD Module...", "   ├── ")
            qkd_key = self.qkd_source.get_key(self.qkd_ksid)
            key_dict["qkd"] = [qkd_key]  # Add QKD key to the dictionary if successful

        except TimeoutException:
            color_log("QKD", "KO", f"Skipping QKD GET KEY. \n\t\t Timeout reached after {TIMEOUT_SECONDS} seconds. ", "   ├── ")
        except Exception as e:
            color_log("QKD", "KO", f"Failed GET KEY from QKDSource: {e}", "   ├── ")
        finally:
            signal.alarm(0)  # Deactivate alarm

        try:
            color_log("PQC", "INFO", "Attempting to get Shared Secret from PQC Link...", "   ├── ")
            pqc_key = self.pqc_source.get_key()
            
            key_dict["pqc"] = [pqc_key]  # Add PQC key to the dictionary if successful

        except Exception as e:
            color_log("PQC", "KO", f"Failed to get Shared Secret from PQCSource: {e}", "   ├── ")

        # If no keys were fetched, return an error
        if not key_dict:
            return {"status": 1, "message": "Failed to fetch any keys from sources"}

        color_log("KDFIX", "OK", f"\n\n\tFetched key dict: {key_dict}\n","")

        # Check if key_dict has only one key, and add an auxiliary entry if needed
        if len(key_dict) < 2:
            if self.pqc_pair and "shared_seed" in self.pqc_pair:
                # Generate the deterministic auxiliary key
                key_length = len(next(iter(key_dict.values()))[0])  # Length of the first key in the dictionary
                aux_key = generate_deterministic_aux_key(self.pqc_pair["shared_seed"], key_length)

                # Add the auxiliary key to the dictionary as a list of lists
                key_dict.update({"aux": [aux_key]})

                color_log("KDFIX", "INFO",
                          "Single key hybridization not allowed. Deterministic Aux key added to hybridize")
                color_log("KDFIX", "OK", f"\nUpdated Key dict with aux: {key_dict}\n", "")

            else:
                color_log("KDFIX", "INFO", "Single key hybridization is allowed; proceeding with a single key.")


        # Handle the case where key_dict has more than one key, or pqc_pair is None, or "shared_seed" is missing
        if len(key_dict) > 1 or self.pqc_pair is None or "shared_seed" not in self.pqc_pair :
            color_log("KDFIX", "INFO", f"Attempting to hybridize keys using method: {hybrid_method.upper()}")
        if hybrid_method == "xoring":
            hybrid_key = xoring_kdf_dict(key_dict, key_chunk_size)
        elif hybrid_method == "hmac":
            hybrid_key = hmac_kdf_dict(key_dict)
        elif hybrid_method == "xorhmac":
            hybrid_key = xorhmac_kdf_dict(key_dict, key_chunk_size)
        else:
            return {"status": 1, "message": "Unknown hybrid method"}

        if isinstance(hybrid_key, list):
            hybrid_key = bytes(hybrid_key)

        # Truncate the hybrid key to the specified chunk_size
        if key_chunk_size and len(hybrid_key) > key_chunk_size:
            hybrid_key = hybrid_key[:key_chunk_size]

        # Respond with the hybrid key
        color_log("KDFIX", "OK", f"Hybrid Key successfully retrieved for key_stream_id: {key_stream_id} "
                                 f"\n\t\tHybrid Key: {list(hybrid_key)}"
                                 f"\n\t\tHEX KEY: {hybrid_key.hex()}"
                                 f"\n\t\tENC_KEY: {form_key(hybrid_key.hex())}", to_console=True)
        return {
            "status": 0,
            "key_buffer": list(hybrid_key)
        }

    def CLOSE(self, request_cl):
        """
        Handles CLOSE requests.
        Removes the key_stream_id from memory.
        
        Args:
            request_cl (dict): Request containing the key_stream_id.
            
        Returns:
            dict: Response with status.
        """
        key_stream_id = request_cl.get('key_stream_id')
        
        # Load the current key streams from the file store
        key_store = load_key_streams()
        
        # Check if the key_stream_id exists in the store
        if key_stream_id in key_store:
            # Remove the key_stream_id entry
            del key_store[key_stream_id]
            save_key_streams(key_store)

            try:
                # Close QKD connection
                signal.alarm(TIMEOUT_SECONDS)  # Set the alarm for QKD close
                color_log("QKD", "INFO", "Attempting CLOSE QKD Module...", "   ├── ")
                self.qkd_source.close_connection(self.qkd_ksid)
            except TimeoutError:
                color_log("QKD", "KO", f"Skipping QKD CLOSE. Timeout reached after {TIMEOUT_SECONDS} seconds.",
                          "   ├── ")
            except Exception as e:
                color_log("QKD", "KO", f"Failed CLOSE from QKDSource: {e}", "   ├── ")
            finally:
                signal.alarm(0)  # Deactivate the alarm

            try:
                # Close PQC Link
                signal.alarm(TIMEOUT_SECONDS)  # Set the alarm for PQC close
                color_log("PQC", "INFO", "Attempting CLOSE PQC Link...", "   ├── ")
                self.pqc_source.close_socket()
            except TimeoutError:
                color_log("PQC", "KO", f"Skipping PQC CLOSE. Timeout reached after {TIMEOUT_SECONDS} seconds.",
                          "   ├── ")
            except Exception as e:
                color_log("PQC", "KO", f"Failed CLOSE PQC Link: {e}", "   ├── ")
            finally:
                signal.alarm(0)  # Deactivate the alarm

        return delete_key_streams()
        
