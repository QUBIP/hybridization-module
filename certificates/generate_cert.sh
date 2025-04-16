#!/bin/sh

# Check if NODE_NAME is set, default to 'node' if not
NODE_NAME=${NODE_NAME:-node}

# Check if an IP argument is provided (for SAN)
if [ -z "$1" ]; then
  echo "Error: No IP address provided for certificate."
  exit 1
fi

NODE_IP=$1  # Capture the provided IP

# Create the certs directory if it doesn't exist
mkdir -p /app/certs

# Path for CA certificate and key
CA_CERT="/app/ca/ca.crt"
CA_KEY="/app/ca/ca.key"

# Generate private key
openssl genpkey -algorithm RSA -out /app/certs/${NODE_NAME}.key -pkeyopt rsa_keygen_bits:2048

# Generate Certificate Signing Request (CSR)
openssl req -new -key /app/certs/${NODE_NAME}.key -out /app/certs/${NODE_NAME}.csr -subj "/CN=${NODE_NAME}"

# Generate certificate signed by CA including the node IP as Subject Alternative Name (SAN)
openssl x509 -req \
    -in "$CSR_FILE" \
    -CA "$CA_CERT" \
    -CAkey "$CA_KEY" \
    -CAcreateserial \
    -out "$CRT_FILE" \
    -days 3650 \
    -sha256 \
    -extfile <(printf "subjectAltName=IP:${NODE_IP}")

# Remove CSR (not needed after signing)
rm /app/certs/${NODE_NAME}.csr

echo "Certificate created for ${NODE_NAME} with IP ${NODE_IP}"
