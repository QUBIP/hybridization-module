# **Hybrid Key Exchange in a Network of Trusted Nodes**

### **Table of Contents**

- [Introduction](#introduction)
- [Project Structure](#project-structure)
- [Runing the module](#runing-the-module)
    - [Certificate setup](#0-certificate-setup)
    - [Module Configuration](#1-node-configuration)
    - [Docker setup](#2-docker-environment-setup)
    - [Reading file logs](#3-reading-the-logs)
    - [Testing the module locally](#extra-testing-the-module-locally)
- [Module's API](#modules-api)
- [Implementation details]()
    - [Key Sources](#key-sources)
    - [Hybridization methods](#hybridization-methods)
    - [Logging types](#logging-types)
    - [TLS Certificate for Secure Socket Establishment](#tls-certificate-for-secure-socket-establishment)

## Introduction
This project is an implementation of an **Hybridization module (HM)**. That is a piece of software designed to derive cryptographic keys
through a combination of two or more independent keys. What makes special this implementation is the capability of
hybridizing **Quantum Key Distribution (QKD)** keys and **Post-Quantum Cryptography (PQC)**.

The project incorporates various key derivation function methods based on **NIST recommendations** and adheres to the **ETSI 004 standard**, enabling seamless communication and ensuring robust security.


## Project Structure
The project is organized into the following parts:

1. **HM source files**: Located in the `src/hybridization_module` directory, this contains the core implementation of the Hybridization Module, including:
    - **`main.py`**: The file that starts the hybridization module. Prepares the configuration files and certificates and starts the server.
    - **`kdfix_server.py`**: Contains the server that opens the HM `ETSI QKD 004` API so that the key requesting applications can comunicate with the module.
    - **`hybridization_functions/`**: The functions used to hybridize the key. More information about hybridization [here](#hybridization-methods)
    - **`key_generation/`**: Includes all the code used to obtain the keys from the different sources (such as QKD or PQC). More information about the sources [here](#key-sources)
    - **`model/`**: The model of the hybridization module.
    - **`peer_connector/`**: Code used to connect HM between each other. Necessary in cases shuch as the sharing of the ETSI QKD 004 ksid or the PQC negotiation.
    - **`session/`**: While the kdfix_server receives the requests, the sessions handle it. This is the main pipeline of the program.
    - **`utils/`**: Code utilities that do not fit in other categories.

2. **Configuration**: The configuration for the module, the repository comes with three prebuild configurations for a 3 node network. Each node is represented by its own folder under the `config/` directory:
    - **`config.json`**: Configuration file specifying the node's UUID, network addresses and certificate information.
    - **`trusted_peers_info.json`**: Configuration file that contains necessary information about the other hybridization modules in the network.

3. **Tests**: The `test/` directory contains the files necessary to test the hybrid module in a local environment. These files can also be used as references when it comes to deploy the HM in real environments.
    - **`Docker-compose.yml`**: Defines an example of network with 3 hybridization modules, perfect to locally test the module or take as a reference to deploy it in other scenarios.
    - **`driver.py`**: Small script that simulates a client doing a full cicle of ETSI QKD 004 calls.
    - **`bulk_driver.py`**: Same as driver.py but in this case makes 10 concurrent life cicles instead of just one. Usually used to test the concurrency in the HM.
    - **`requests/`**: Contains examples of OPEN CONNECT requests. These are used by driver.py to do the initial OPEN CONNECT.

4. **Suporting Scripts**: The module have various bash scripts:
    - **`create_ca.sh`**: Helper script to generate the CA key and certificate before running the system.
    - **`generate_cert.sh`**: Script to generate node certificates. IMPORTANT: This script is used inside main.py, so there is no need to use it before runing the HM.
    - **`run_all.sh`**: Prepares a tmux session in which you can test an scenario with 3 nodes.

5. **Other files and directories**:
    - **`Dockerfile`**: Defines the final container image, including runtime dependencies, environment setup, and execution commands.
    - **`requirements.txt`**: Python session requirements for the HM to run.
    - **`ruff.toml`**: The configuration of the Ruff python linter and formatter.


## Runing the module

### 0. **Certificate Setup**

Before running the networks hybridization modules, one must generate a Root CA certificate and key that will be used to sign each node's certificate.

Run the following command from the project root to create a ca/ folder with the necessary files:

```bash
bash certificates/create_ca.sh
```

This script creates the ca/ folder with the CA key and certificate.
These are required for each node to auto-generate and sign its own certificate at startup (See more [here](#tls-certificate-for-secure-socket-establishment)), enabling secure TLS communication.

### 1. **Node Configuration**:

To start an instance of the hybridization module you first have to prepare two files. The first one (`config.json`) it's used to configure the hybridization module itself, where will it be listening, the paths to the certificates, identification information etc. While the other one (`trusted_peers_info.json`) contains useful data about the other hybridization modules in the network, such as where their peer connector is listening.

#### **Main configuration**

The main configuration file, usually named `config.json` contains the following information:

- **uuid:** The hybridization module uuid (Usually the same as the node it is in).
- **logging_config:**
  - **console_log_type:** Logging type used in the console logs. See more information about logging type [here](#logging-types).
  - **colorless_console_log:** True = Monochrome console logs. False = Console logs with colors.
  - **file_log_type:** Logging type used in the logging file. See more information about logging type [here](#logging-types).
  - **filename:** Path to the certificates's key.
- **certificate_config:**
  - **certificate_ip:** The ip to which the certificate is sign (In real scenarios it is usually the public ip of the node, or at least the one peers connect to)
  - **cert_authority_path:** Path of the ca certificate.
  - **cert_path:** Path to the hybridization module certificate.
  - **key_path:** Path to the certificates's key.
- **hybridization_server_address:** The host and port in which the hybridization module entry point will be deployed (The one apps connect to obtain hybridated key).
- **qkd_address:** The host and port of the qkd node the hybridization module uses to obtain quantum key.
- **peer_local_address:** The host and port the hybridization module will listen to when comunicating with other hybridization modules.

Example of `config.json`:
```json
{
  "uuid" : "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",

  "logging_config" : {
    "console_log_type" : "info",
    "colorless_console_log" : false,

    "file_log_type" : "debug",
    "filename" : "hybrid.log"
  },

  "certificate_config" : {
    "certificate_ip" : "10.10.11.246",
    "cert_authority_path" : "/app/ca/ca.crt",
    "cert_path" : "/app/certs/node.crt",
    "key_path" : "/app/certs/node.key"
  },

  "hybridization_server_address": {
    "host" : "10.10.11.246",
    "port" : 65430
  },

  "qkd_address": {
    "host" : "192.168.222.1",
    "port" : 54001
  },

  "peer_local_address": {
    "host" : "10.10.11.246",
    "port" : 3001
  }
}
```

#### **Trusted peers information**

The json that contains information about the other hybridization modules in the network, usually named `trusted_peers_info.json`, it is structured a bit different. Each hybridization module has an entry (identified by its **uuid**), and each entry contains the following information:
-  **shared_seed:** A pre-negotiated seed used to generate a deterministic key in the scenario that one (and only one) of the key sources is available.
-  **address:** The address that hybridization modules is using to communicate with other hybridization modules.

Example of `trusted_peers_info.json`:

```json
{
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" : {
        "shared_seed" : "123456789",
        "address": {
            "host" : "10.10.11.245",
            "port" : 3001
        }
    },
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb" : {
        "shared_seed" : "123456789",
        "address": {
            "host" : "10.10.11.246",
            "port" : 3001
        }
    },
    "cccccccc-cccc-cccc-cccc-cccccccccccc" : {
        "shared_seed" : "123456789",
        "address": {
            "host" : "10.10.11.245",
            "port" : 3001
        }
    }
}
```
### 2. **Docker Environment Setup**

This module is highly tied to docker and containerization, to the point that it has not been tested in other environments outside of docker. Therefore, setting up docker correctly is key for a successful installation. To run the Dockerfile correctly you must know the following things:

- When building the docker image you must provide the following arguments:
    - CFGFILE: The path to the [main configuration](#main-configuration) file you want to use for the image. For example, `config/Alice/config.json`
    - TRUSTED_PEERS_INFO: The path to the [Trusted peer configuration](#trusted-peers-information) file containing all the information of the network. For example, `config/Alice/trusted_peers_info.json`

- An instance of the module listens to two address at the same time, the address of the API server, which is the entrypoint for the clients that want to get key, and address that listens to other hybridization modules. Depending on your network configuration you may want to expose the ports, set up a docker network or do nothing (This last option is just if you are [testing the module in a local environment](#extra-testing-the-module-locally)).

#### **Docker deployment examples**

Although you can use docker directly with the next commands:

```bash
# Building
docker build -t hybridization:1 -f Dockerfile . --build-arg CFGFILE="config/Alice/config.json" --build-arg TRUSTED_PEERS_INFO="config/Alice/trusted_peers_info.json"

# Running with both ports exposed
docker run --name hybridization_module -p <host_hybridization_port>:<container_hybridization_port> -p <host_peer_port>:<container_peer_port> --rm hybridization:1
```

It is highly recommended to use something similar to docker compose, since it provides a clearer view of the whole configuration.

Example with both ports exposed:
```yaml
version: '3'

services:
  hybridmodule:
    container_name: hybridization_module
    build:
      dockerfile: Dockerfile
      args:
        CFGFILE: "config/Alice/config.json"
        TRUSTED_PEERS_INFO: "config/Alice/trusted_peers_info.json"
    ports:
      - "<host_ip_address>:<host_hybridization_port>:<container_hybridization_port>"
      - "<host_ip_address>:<host_peer_port>:<container_peer_port>"
```

<br>

Example with the application in the docker compose:
```yaml
version: '3'

services:
  hybridmodule:
    container_name: hybridization_module
    build:
      context: kdfix-docker/
      dockerfile: Dockerfile
      args:
        CFGFILE: "config/Alice/config.json"
        TRUSTED_PEERS_INFO: "config/Alice/trusted_peers_info.json"
    ports:
      - "<host_ip_address>:<host_peer_port>:<container_peer_port>"
    networks:
      hybrid_network:
        ipv4_address: 10.10.11.211

  client_app:
    container_name: client_app
    build:
      context: client_app/
      dockerfile: Dockerfile
    networks:
      hybrid_network:
        ipv4_address: 10.10.11.111

networks:
  hybrid_network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 10.10.11.0/24
          gateway: 10.10.11.1
```


#### **Dockefile implementation details**

It is usually recommended to use something like docker compose, since it usually requires network configuration.

The building process of the image has 2 stages:

   1. **Builder image**

      In this stage docker creates a temporal image that will be used to build the liboqs library.

   2. **Building the final image**

      Once the liboqs is built, we get the binaries and shared libraries from the temporal image and copy them to a new one. This avoid keeping unnecessary build programs/files that would only make the image heavier than it already is.

      Once those files are copied, we start copying the file from the hybridization module such as:

      - The Hybridization Module source files
      - Node-specific configurations (`config.json`, `trusted_peers_info.json`)
      - Certificate generation scripts
      - The scrips used to test the hybridization (driver.py).


### 3. Reading the logs

Once the hybridization module is running it will generate logs in:
- **Console:** The stderr of the program. If allowed it will use colors.
- **Logfile:** A file inside the container (unless connected through a volume).

The kind of logs that get printed to one of these sources is defined on the log type it is using (See more [here](#logging-types)), and this type along with other logs related things is set in the [main configuration](#main-configuration).

To access the logs without setting up a volume you can allways use the command:

```bash
docker exec -it <container_name> tail -f <logfile_path>
```


### **Extra: Testing the module locally**

Besides the source files and configurations of the module, the repository also comes with some utilities to test the module locally:

#### Docker compose 3 node simulation

The `docker-compose.yml` located in `tests/` prepares a simulation of a network with 3 hybridization modules.

To run this simulation you just need to run the subsequent command:

```bash
docker compose up --build
```

Once the containers are up, you may use the driver scripts to test the module.

Note: These modules are not connected by default to any QKD source, so you will receive error logs saying the connection to these devices have failed.

#### Driver Scripts

After the Hybridization Module is initialized and is listening for requests, the **driver script** can be executed to perform ETSI 004 workflow and achieve key exchanges.
Each container has its own driver, which interacts with the respective Hybridization Modules to manage connections and derive hybrid keys.

Steps to Run the Driver:

1. **Access the Node's Container**
    Since the driver runs inside each node's container, you first need to enter the container's environment.
    Use the following command to open a terminal inside the running container:
      ```bash
      docker exec -it <node-conatiner-name> /bin/bash
      ```

2. **Run the Driver Script**

    Once inside the container, execute the driver script to initiate the ETSI 004 workflow to request hybrid key:
    ```bash
    python3 driver.py
    ```

    This step sends the required ETSI 004 commands (`OPEN_CONNECT`, `GET_KEY`, and `CLOSE`, [See more details](#modules-api)) to the Hybridization Module, initiating and managing the key exchange process.

`driver.py` requires a OPEN_CONNECT template to work. That is why the Dockerfile also copies the `tests/requests/` directory into the container with the name of `request/`. If given no arguments, `driver.py` will use `open_connect_request.json`, however, if it has arguments it will use the first one as the path to the OPEN_CONNECT to use. [See more details about the structure of OPEN_CONNECT Requests](#open_connect-request)


## **Module's API**

The hybridization modules uses the [ETSI GS QKD 004](https://www.etsi.org/deliver/etsi_gs/QKD/001_099/004/02.01.01_60/gs_qkd004v020101p.pdf) as its client API. The ETSI 004 workflow consists of three primary commands:

1. **OPEN_CONNECT**:
    - Establishes a secure connection between nodes.
    - Uses the node’s configuration (`config.json` and `open_connect_request.json`) to configure sockets and negotiate key exchange parameters (e.g., QKD, PQC, and hybridization methods).
    - Prepares the system for subsequent commands (`GET_KEY` and `CLOSE`).
2. **GET_KEY**:
    - Obtains cryptographic keys from QKD and PQC sources.
    - Combines these keys using the specified hybridization method (e.g., `xoring`) to derive a secure hybrid key.
    - Ensures the derived key is securely and synchronously obtained by both nodes.
3. **CLOSE**:
    - Terminates the session, ensuring all active connections are closed and resources are released.



### OPEN_CONNECT Request

For the key exchange to succeed, both nodes must send identical and correctly configured OPEN_CONNECT request.
These matching requests get the connection paramters, ensure synchronization, and allow the Hybridization Module to securely derive the same hybrid key for both nodes.

Example of `open_connect_request.json` (for node `aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa` or node `bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb`):

```json
{
    "command": "OPEN_CONNECT",
    "data": {
        "source": "hybrid://SPI_1@aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa?hybridization=xoring&kem_mec=Kyber512",
        "destination": "hybrid://SPI_1@bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb?hybridization=xoring&kem_mec=Kyber512",
        "qos": {
            "key_chunk_size": 32,
            "max_bps": 32,
            "min_bps": 32,
            "jitter": 0,
            "priority": 0,
            "timeout": 0,
            "ttl": 0,
            "metadata_mimetype": "application/json"
        }
    }
}
```

The key componets of the request are:

**Command:**

Specifies the operation to be performed by the Hybridization Module.

**`command`**: `"OPEN_CONNECT"`

**Data:**

The `data` field contains the core details required for the connection and key exchange. It includes:

- **Source and Destination URIs**:  Information about the nodes and the cryptographic algorithms required for hybridization.

  **Structure:**
      ```
      hybrid://<name>@<UUID>?hybridization=<method>&kem_mec=<PQC KEM>
      ```

  * **Schema**: Indicates that the request involves hybrid key exchange. `hybrid://`
  * **Path Parameter**: Contains the application name and the UUID of the source and destination node, uniquely identifying it in the network. `aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa`
  * **Query Parameters**:

    + `hybridization`: Specifies the hybridization method. See all the options [here](#hybridization-methods).

    +  `kem_mec`: Specifies the Post-Quantum Cryptography (PQC) key encapsulation mechanism. See all the options [here](#hybridization-methods)

- **QoS (Quality of Service)**: Describes the characteristics of the requested key. Currently the only qos that is taken into account is the key_chunk_size
  * `key_chunk_size`: The size of the key buffer in bytes.

Properly formatted **OPEN_CONNECT** requests ensure that both nodes synchronize their configurations and cryptographic parameters to derive the same hybrid key.

## Implementation details

### **Key sources**

While the key extraction process is usually simplified in Quantum Key Distribution (QKD) and Post Quantum Criptography (PQC), PQC refers to a considerable number of algorithms, the current implementation supports the following options when picking a pqc algorithm:

- **BIKE-L1**
- **BIKE-L3**
- **BIKE-L5**

<br>

- **Classic-McEliece-348864**
- **Classic-McEliece-460896**
- **Classic-McEliece-6688128**
- **Classic-McEliece-6960119**
- **Classic-McEliece-8192128**

- **Classic-McEliece-348864f**
- **Classic-McEliece-460896f**
- **Classic-McEliece-6688128f**
- **Classic-McEliece-6960119f**
- **Classic-McEliece-8192128f**


<br>

- **HQC-128**
- **HQC-192**
- **HQC-256**

<br>

- **Kyber512**
- **Kyber768**
- **Kyber1024**

<br>

- **ML-KEM-512**
- **ML-KEM-786**
- **ML-KEM-1024**

<br>

- **sntrup761**

<br>

- **FrodoKEM-640-AES**
- **FrodoKEM-976-AES**
- **FrodoKEM-1344-AES**

- **FrodoKEM-640-SHAKE**
- **FrodoKEM-976-SHAKE**
- **FrodoKEM-1344-SHAKE**

### **Hybridization methods**

The available hybridization methods are a mix of standardized and experimental functions.

- **xoring:** Method based on the [NIST recomendations](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-133r2.pdf#page=28) that consist in making an xor operation between both keys.
- **hmac:** Method based on the [NIST recomendations](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-133r2.pdf#page=28) which consist in using an HMAC algorthim using a secret/public value (also know as salt) as key and the concatenation of keys to hybridize as message. In this implementation the first key is used as salt and the rest of keys as message, currently the HASH algorithm is SHA-256.
- **xorhmac:** Experimental method tha comes from combining the xoring and hmac methods. In this implementation it first make the hmac method with both the list of keys and the same list in inverted order, then it applies the xoring operation between the two hmac results.


### Logging types

In order to make logging easy to configure the hybridization module provides the following logging types:

- **Debug:** Logs messages from the levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
- **Info:** Logs messages from the levels: INFO, WARNING, ERROR, CRITICAL.
- **Warning:** Logs messages from the levels: WARNING, ERROR, CRITICAL.
- **Error:** Logs messages from the levels: ERROR, CRITICAL.
- **None:** No logging for that particular source.

### **TLS Certificate for Secure Socket Establishment**

In this project, **TLS (Transport Layer Security)** is used to secure the communication channels between nodes during **PQC key negotiation**. The certificate generation and management are handled in two stages:

1. **CA Certificate Generation (Build Stage):**

    During the Docker build process, a **self-signed Certificate Authority (CA)** is created using RSA-2048. This CA (`ca.crt` and `ca.key`) acts as the trusted root for signing the node certificates.
    Run `./create_ca.sh` once to generate a local Certificate Authority.


2. **Node Certificate Generation (Runtime Stage):**

    When each node container is started, the **`sign_cert.sh`** script is executed automatically. This script:

    - Generates an **RSA-2048 private key** for the node.
    - Creates a **Certificate Signing Request (CSR)** based on the node’s UUID (which doubles as the container’s DNS name).
    - Uses the CA from the build stage to sign the CSR, resulting in a **node-specific certificate** (`${NODE_NAME}.crt`).

3. **Secure Socket Establishment with TLS:**

    When nodes initiate the PQC key negotiation, **TLS sockets** are established using these certificates:

    - The **server** wraps its socket with the node's certificate and key (`server_side=True`).
    - The **client** connects to the server's DNS (UUID) and verifies its identity using the CA certificate.

This ensures that all PQC key exchanges are encrypted and authenticated, preventing **man-in-the-middle attacks** and ensuring **data integrity**.
