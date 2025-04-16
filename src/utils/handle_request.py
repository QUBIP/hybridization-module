from urllib.parse import urlparse, parse_qs
import hashlib
import re

def parse_oc_request(request):
    """
    Parses the open connect request. To determines from path the source and the destination UUID to resolves QKD and PQC nodes,
    and role (server/client) to key negotiation.
    Also from Query params the hybridization method, KEM mechanism for PQC key exchange,
    and from QOS, chunk_size and other information about the required key.


    :param request: Dictionary containing the request data.
    :return: Parsed configuration details.
    """
    source_uri = request.get("source")
    destination_uri = request.get("destination")

    if not source_uri or not destination_uri:
        raise ValueError("Both source and destination URIs are required.")

    # Parse URIs
    try:
        source_uri_parsed = urlparse(source_uri)
        destination_uri_parsed = urlparse(destination_uri)
    except Exception as e:
        raise ValueError(f"Invalid URI format: {e}")

    # Extract UUIDs from the URI path (after // and before query params)
    source_uuid = source_uri_parsed.netloc.split("@")[1]
    destination_uuid = destination_uri_parsed.netloc.split("@")[1]

    # Additional validation (ensure UUIDs are present)
    if not source_uuid or not destination_uuid:
        raise ValueError("Both source and destination UUIDs must be non-empty.")

    # Extract from Query params Hybridization Module and Kem mechanism
    parsed_qs = parse_qs(source_uri_parsed.query)
    hybrid_method = parsed_qs["hybridization"][0]
    pqc_kem_mec = parsed_qs["kem_mec"][0]

    # Extract from QOS the chunk_size of the requiered key
    chunk_size = request.get("qos").get("key_chunk_size")

    return source_uuid, destination_uuid, hybrid_method, pqc_kem_mec, chunk_size

def generate_ksid(source_uuid, destination_uuid):
    # Combine the two UUIDs as string
    combined  = str(source_uuid) + str(destination_uuid)

    # Hash the source and destination to generate a string to use as KSIºD
    ksid = hashlib.sha256(combined.encode('utf-8')).hexdigest()

    return ksid[:16]  # First 16 characters, adjust as needed


def transform_qkd_request_oc(input_request: dict) -> dict:
    """
    Transforms a hybrid OPEN_CONNECT request into a QKD-compatible OPEN_CONNECT request.

    Args:
        input_request (dict): The original request in hybrid format.
    Returns:
        dict: The transformed request formatted for QKD.
    """
    if not isinstance(input_request, dict) or "command" not in input_request or "data" not in input_request:
        raise ValueError("Invalid input_request format")

    data = input_request["data"]

    # Extract source and destination UUIDs dynamically
    source_match = re.search(r'@(.*?)\?', data["source"])
    destination_match = re.search(r'@(.*?)\?', data["destination"])
    key_chunk_size = data["qos"].get("key_chunk_size")

    if not source_match or not destination_match:
        raise ValueError("Invalid source or destination format in request")

    source_uuid = source_match.group(1)
    destination_uuid = destination_match.group(1)

    # Construct the new source and destination URIs
    new_source = f"qkd://Application1@{source_uuid}"
    new_destination = f"qkd://Application4@{destination_uuid}"

    # Create the transformed request
    transformed_request = {
        "command": "OPEN_CONNECT",
        "data": {
            "source": new_source,
            "destination": new_destination,
            "qos": {
                "key_chunk_size": key_chunk_size,
                "max_bps": data["qos"].get("max_bps", 32),
                "min_bps": data["qos"].get("min_bps", 32),
                "jitter": data["qos"].get("jitter", 0),
                "priority": data["qos"].get("priority", 0),
                "timeout": data["qos"].get("timeout", 0),
                "ttl": data["qos"].get("ttl", 0),
                "metadata_mimetype": data["qos"].get("metadata_mimetype", "application/json")
            }
        }
    }

    return transformed_request