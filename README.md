# **Hybrid Key Exchange in a Network of Trusted Nodes**

### **Table of Contents**

- [Introduction](#introduction)
   * [Project Structure](#project-structure)
   * [Quick Start: Command Summary](#quick-start-command-summary)
- [How It Works](#how-it-works)
  * [1. Node Configuration:](#1-node-configuration)
  * [2. Docker Network & Image Setup](#2-Docker-network-and-image-setup**)
  * [3. Hybridization Module Initialization](#3-hybridization-module-initialization)
  * [4. Running the Driver and Executing the ETSI 004 Workflow](#4-running-the-driver-and-executing-the-etsi-004-workflow)
- [ETSI 004 Workflow](#etsi-004-workflow)
- [OPEN_CONNECT Request](#open_connect-request)
- [TLS Certificate for Secure Socket Establishment](#tls-certificate-for-secure-socket-establishment)

# Introduction 
This project is a possible implementation of a secure and scalable framework for cryptographic key hybridization exchange 
between multiple nodes (e.g.,Alice,Bob,etc.).

Each node operates independently, using the **Hybridization Module (HM)** —the core component of this project— designed 
to derive hybrid cryptographic keys through a combination of **Quantum Key Distribution (QKD)** and **Post-Quantum Cryptography (PQC)**.

The project incorporates various key derivation function methods based on **NIST recommendations** and adheres to the **ETSI 004 standard**, enabling seamless communication and ensuring robust security.


## Project Structure
The project is organized into two main components:

1. **Node Folders**: Each node is represented by its own folder under the `nodes/` directory:
    - **`config.json`**: Configuration file specifying the node's UUID and network addresses.
2. **HM Library Folder**: Located in the `src/` directory, this contains the core implementation of the Hybridization Module, including:
    - **ETSI 004 Commands**: Processes commands such as `OPEN_CONNECT`, `GET_KEY`, and `CLOSE`.
    - **QKD System Interface**: Ensures compatibility with various QKD providers via standardized `ETSI QKD 004` protocols.
    - **Post-Quantum Cryptography**: Utilizes the `Liboqs` library for encapsulation and signing of shared secrets with `NIST-approved algorithms` through secure sockets.
    - **Hybridization Methods**: Implements secure and efficient key derivation techniques like `xoring` and `hmac`, located in the `functions/` folder.
    - **Extensible Design**: Allows easy integration of new key sources and derivation methods in the `key/` directory.
    - **Utilities**: Helper functions and logging utilities are stored in the `utils/` directory.
3. **Supporting Files and Scripts**:
    - **`driver.py`**: Client driver script to interact with the hybridization module.
    - **`hybridization_module.py`**: Entry point for the hybridization module.
   
   **DockerConfigs**
    - **`Dockerfile`**: Defines the final container image, including runtime dependencies, environment setup, and execution commands.
    - **`Docker.base`**: Creates a reusable base image with pre-installed dependencies to speed up builds.
    - **`Docker-compose.yml`**: Defines multi-container orchestration, networking, and environment configurations for running multiple nodes.
   
   **Certificates**
    - **`create_ca.sh`**: Helper script to generate the CA key and certificate before running the system.
    - **`generate_cert.sh`**: Script to generate node certificates.
   
   **Requests**
    - **`open_connect_request.json`**: Contains the ETSI 004 request, defining specific key exchange features between nodes.

Together, these components enable the nodes in the network to establish trusted connections and dynamically derive shared cryptographic keys.


# Quick Start: Command Summary

### 0. **Certificate Setup**

Before launching the hybridization modules, one must generate a Root CA certificate and key that will be used to sign each node's certificate.

Run the following command from the project root to create a ca/ folder with the necessary files:

```bash
bash certificates/create_ca.sh
```

This script creates the ca/ folder with the CA key and certificate.
These are required for each node to auto-generate and sign its own certificate at startup, enabling secure TLS communication.
### 1. **Build the Hybridization Module Base Image**

Create a reusable base image with all necessary dependencies to speed up builds:

```bash
docker build -t kdfix-docker-base -f Dockerfile.base .
```

### 2. **Build the Hybridization Module Containers**

Build the Docker images for the hybrid key negotiation nodes:

```bash
docker compose build --no-cache
```

### 3. **Run Node Containers**

Start the node containers and establish the Docker network:

```bash
docker compose up
```

### 4. **Interacting with Nodes**

Access each container using the node’s UUID (which matches the container name) and run `driver.py` to initiate the key exchange:

```bash
docker exec -it <NODE-UUID> /bin/bash
python3 driver.py
```
This  sends open_connect_request.json to the node's, initiating the hybrid key exchange.


