# hybridization_module.py
import json
import os
import subprocess
import sys

sys.path.append(os.getenv("SRC_PATH"))

from hybridization_module.kdfix_server import Etsi004Server
from hybridization_module.model.config import (
    GeneralConfiguration,
    PeerInfo,
    TrustedPeerInfoValidator,
)
from hybridization_module.utils.log_utils import configure_logging


def load_general_config() -> GeneralConfiguration:
    """
    Load the configuration file for each node (config.json).
    """
    config_path = os.getenv("CFGFILE")
    try:
        with open(config_path, "r") as config_file:
            print(f"Loaded configuration from {config_path}")
            return GeneralConfiguration.model_validate(json.load(config_file))
    except Exception as e:
        print(f"Error loading configuration: {e}")
        exit(1)

def load_trusted_peers_info() -> dict[str, PeerInfo]:
    """
    Load the information about the connected peers (trusted_peers_info.json).
    """
    peers_info_path = os.getenv("TRUSTED_PEERS_INFO")
    try:
        with open(peers_info_path, "r") as peers_info_file:
            print(f"Loaded configuration from {peers_info_path}")
            json_peers_info = json.load(peers_info_file)

        peers_info_validator = TrustedPeerInfoValidator.model_validate({"peers_info" : json_peers_info})
        return peers_info_validator.peers_info
    except Exception as e:
        print(f"Error loading configuration: {e}")
        exit(1)

def sign_certificates(node_ip: str) -> None:
    """
    Run the sign_cert.sh script to generate certificates.
    """
    cert_script = "/app/certificates/sign_cert.sh"
    if os.path.exists(cert_script):
        print(f"Generating PQC Certificates for IP {node_ip}...")
        subprocess.run(["bash", cert_script, node_ip], check=True)  # Pass the node IP as an argument
        print("Certificates generated successfully!")
    else:
        print(f"Warning: Certificate script {cert_script} not found!")


# Run the KDFix Hybridization Module
if __name__ == "__main__":
    config: GeneralConfiguration = load_general_config()
    peers_info = load_trusted_peers_info()

    configure_logging(config.logging_config)
    sign_certificates(config.certificate_config.certificate_ip)

    server = Etsi004Server(config, peers_info)

    print(f"Starting the Hybridization Module on {config.hybridization_server_address}...")
    server.start_server()