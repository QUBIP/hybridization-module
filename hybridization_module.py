# hybridization_module.py
import json
import os
import subprocess

from KDFix import start_server


def load_config():
    """
    Load the configuration file for each node (config.json).
    """
    config_file = os.getenv("CFGFILE")
    try:
        with open(config_file, "r") as f:
            print(f"Loaded configuration from {config_file}")
            return json.load(f)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        exit(1)

def generate_certificates(node_ip):
    """
    Run the generate_cert.sh script to generate certificates.
    """
    cert_script = "/app/certificates/generate_cert.sh"
    if os.path.exists(cert_script):
        print(f"Generating PQC Certificates for IP {node_ip}...")
        subprocess.run(["bash", cert_script, node_ip], check=True)  # Pass the node IP as an argument
        print("Certificates generated successfully!")
    else:
        print(f"Warning: Certificate script {cert_script} not found!")


# Run the KDFix Hybridization Module
if __name__ == "__main__":
    config = load_config()

    node_ip = config["local_node"]["ip_node"]
    generate_certificates(node_ip)

    hybridization_addr = tuple(config["local_node"]["hybridization_address"])
    print(f"Starting the Hybridization Module on {hybridization_addr}...")
    start_server(hybridization_addr)