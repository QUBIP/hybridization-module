from utils.colorlog import color_log

def link_config(node_config, source_uuid, destination_uuid):
    """
    Configure the PQC link based on node configuration and UUIDs.

    Args:
        node_config (dict): Node configuration containing local_node and remote_nodes.
        source_uuid (str): UUID of the source node.
        destination_uuid (str): UUID of the destination node.

    Returns:
        tuple: pqc_role (str), pqc_link (tuple), pqc_pair (dict)
               If errors occur, pqc_link and pqc_pair will be None.

    """
    pqc_role, pqc_link, pqc_pair = None, None, None

    try:
        # Validate 'local_node' and 'uuid'
        if "local_node" not in node_config or "uuid" not in node_config["local_node"]:
            raise KeyError("Missing 'local_node' or 'uuid' in node_config.")
        pqc_role = "CLIENT" if node_config["local_node"]["uuid"] == source_uuid else "SERVER"
    except KeyError as e:
        color_log("PQC", "KO", f"[ERROR] {e}. Defaulting pqc_role to 'SERVER'.", "   ├── ")
        pqc_role = "SERVER"  # Default role if an error occurs

    try:
        # Define the UUID to search for based on the role
        search_uuid = destination_uuid if pqc_role == "CLIENT" else source_uuid
        # Find the PQC pair
        pqc_pair = next((node for node in node_config.get("remote_nodes", []) if node["uuid"] == search_uuid), None)
        if not pqc_pair:
            raise ValueError(f"PQC pair with UUID {search_uuid} not found in 'remote_nodes'.")
    except ValueError as e:
        color_log("PQC", "KO", f"[ERROR] {e}. Skipping PQC pair setup.", "   ├── ")

    
    try:
        # Validate and extract the PQC address
        if pqc_pair and "pqc_link" in pqc_pair:
            pqc_link = tuple(pqc_pair["pqc_link"])

            if len(pqc_link) != 2 or not isinstance(pqc_link[0], str) or not isinstance(pqc_link[1], int):
                raise ValueError(f"Invalid 'pqc_link' format in PQC pair: {pqc_pair['pqc_link']}")
        else:
            raise KeyError(f"Missing 'pqc_link' in PQC pair for UUID.")
    except (KeyError, ValueError) as e:
        color_log("PQC", "KO", f"[ERROR] {e}. Skipping PQC address setup.", "   ├── ")


    try:
        if "pqc_address" in node_config["local_node"]:
            pqc_address = tuple(node_config["local_node"]["pqc_address"])
        else:
            raise KeyError("Missing 'pqc_address' in local_node.")
    except KeyError as e:
        color_log("PQC", "KO", f"[ERROR] {e}. Using default ('0.0.0.0', 3001).", "   ├── ")
        pqc_address = ("0.0.0.0", 3001)

    return pqc_link, pqc_address, pqc_role, pqc_pair
