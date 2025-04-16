#!/bin/bash
# Generates a self-signed CA certificate

mkdir -p ca
openssl genrsa -out ca/ca.key 4096
openssl req -x509 -new -nodes -key ca/ca.key -sha256 -days 3650 \
  -out ca/ca.crt -subj "/C=EU/O=HybridizationCA/OU=CyberSec/CN=hybrid-ca"

echo "CA certificate and key generated in ./ca/"
