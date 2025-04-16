#kdfix/key/pqc_source.py
import ssl

import oqs
import time
import socket
import ast
from utils.exception import PQCException
from utils.colorlog import color_log

class PQCSource:
    def __init__(self, pqc_link, pqc_address, role=None, kem_algorithm='Kyber512', sig_algorithm=None):
        """
        Initializes the PQC Link using the node, and with a specified KEM and optional signature mechanism.

        Args:
            kem_algorithm (str): The KEM algorithm to use (default: 'Kyber512').
            sig_algorithm (str): The signature algorithm to use (optional).
            is_encap (bool): If True, the node acts as a server, otherwise acts as a client.

        """
        color_log("PQC", "INFO", f"Connection with PQC link initialized")
        self.kem_algorithm = kem_algorithm
        self.sig_algorithm = sig_algorithm
        self.role = role
        self.pqc_link = pqc_link
        self.pqc_address = pqc_address
        # Paths to certificates
        self.cert = f"/app/certs/node.crt"
        self.key = f"/app/certs/node.key"
        self.ca_cert = "/app/ca/ca.crt"

        color_log("PQC", "INFO", f"Configuration loaded: ")
        color_log("PQC", "INFO", f"Role={role}", "   ├── ")
        color_log("PQC", "INFO", f"Source Ip={self.pqc_link}", "   ├── ")
        if self.kem_algorithm:
            color_log("PQC", "INFO", f"KEM Mechanism={self.kem_algorithm}", "   ├── ")
            # Initialize OQS KEM object
            self.kem = oqs.KeyEncapsulation(self.kem_algorithm)
        if self.sig_algorithm:
            color_log("PQC", "INFO", f"Digital Signature Mechanism={self.sig_algorithm}", "   ├── ")


        self.public_key = None

        self.context = self._setup_ssl_context()
        self.raw_socket = None  # To store the raw socket once created
        self.secure_socket = None  # To store the secure socket once connected

    def _setup_ssl_context(self):
        context = ssl.create_default_context(
            ssl.Purpose.CLIENT_AUTH if self.role == 'SERVER' else ssl.Purpose.SERVER_AUTH
        )
        context.load_cert_chain(certfile=self.cert, keyfile=self.key)
        context.load_verify_locations(self.ca_cert)
        context.verify_mode = ssl.CERT_REQUIRED
        return context

    def connect_socket(self, retries=5, delay=1):
        """
        Opens the socket connection based on the role.
        - SERVER: Acts as a server and waits for the client's connection.
        - CLIENT: Acts as a client and connects to the peer's server.

        Args:
            retries (int): Number of retries for the client to connect.
            delay (int): Delay (in seconds) between retries.
        """
        if self.role == "SERVER":
            # Server logic: Start the server and wait for the client to connect
            try:
                raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                raw_socket.bind(self.pqc_address)

                raw_socket.listen(1)
                self.raw_socket = raw_socket  # Store raw socket for accepting connections later
                color_log("PQC", "INFO", f"[SERVER] Listening for connections on {self.pqc_address}", "   ├── ")
            except Exception as e:
                color_log("PQC", "KO", f"[SERVER] Failed to start server: {e}", "   ├── ")
                raise PQCException("Unable to start PQC server socket")
        elif self.role == "CLIENT":
            # Client logic: Attempt to connect to the server with retries
            for attempt in range(retries):
                try:
                    raw_socket = socket.create_connection(self.pqc_link)
                    self.secure_socket = self.context.wrap_socket(raw_socket, server_hostname=self.pqc_link[0])
                    color_log("PQC", "INFO", f"[CLIENT] Connected & TLS wrapped to {self.pqc_link}", "   ├── ")
                    return
                except Exception as e:
                    color_log("PQC", "WARNING", f"[CLIENT] Attempt {attempt + 1} failed: {e}", "   ├── ")
                    if attempt < retries - 1:
                        time.sleep(delay)  # Wait before retrying
                    else:
                        color_log("PQC", "KO", "[CLIENT] Failed to connect to server after multiple retries.", "   ├── ")
                        raise PQCException("Unable to connect to server after retries")
        else:
            raise ValueError("Invalid role. Must be 'CLIENT' or 'SERVER'.")

    def get_key(self, retries=5, delay=1 , timeout=10):
        """
        Performs the key exchange process based on the role.
        - CLIENT: Generates the keypair, sends the public key, and receives the shared secret.
        - SERVER: Receives the public key, encapsulates the shared secret, and sends it back.

        Args:
            retries (int): Number of retries for the shared secret exchange.
            delay (int): Delay (in seconds) between retries.
            timeout (int): Timeout (in seconds) between retries.

        Returns:
            bytes: The shared secret.

        Raises:
            PQCException: If the key exchange fails after all retries.
        """
        start_time = time.time()  # Record the start time for timeout tracking

        if self.role == "SERVER":
            self.raw_socket.settimeout(timeout)  # Set timeout for accept()
            for attempt in range(retries):
                # Check if timeout has been reached
                if time.time() - start_time > timeout:
                    color_log("PQC", "KO", "[SERVER] Timeout reached during key exchange.", "   ├── ")
                    raise PQCException("Key exchange failed: Timeout reached.")
                try:
                    # SERVER: Receive public key, encapsulate secret, and send ciphertext
                    color_log("PQC", "INFO", "[SERVER] Waiting for public key from client...", "   ├── ")
                    client_socket, addr = self.raw_socket.accept()
                    self.secure_socket = self.context.wrap_socket(client_socket, server_side=True)

                    # Verify client certificate
                    cert = self.secure_socket.getpeercert()
                    if cert:
                        color_log("PQC", "OK", f"[SERVER] Client certificate verified, cert['subject']: {cert['subject']}", "   ├── ")
                    else:
                        raise ssl.SSLError("Client certificate verification failed")

                    self.secure_socket.settimeout(timeout - (time.time() - start_time))  # Timeout for recv()
                    with client_socket:
                        public_key = self.secure_socket.recv(4096)
                        color_log("PQC", "INFO", "[SERVER] Received public key, encapsulating secret...", "   ├── ")
                        ciphertext, shared_secret = self.kem.encap_secret(public_key)
                        response = {
                            'ciphertext': list(ciphertext),
                            'shared_secret': list(shared_secret)
                        }

                        self.secure_socket.sendall(str(response).encode('utf-8'))  # Send back shared secret
                        color_log("PQC", "OK", f"[SERVER] Shared secret encapsulated: {shared_secret}", "   ├── ")
                        return list(shared_secret)
                except socket.timeout:
                    color_log("PQC", "WARNING", "[SERVER] Connection timed out. Retrying...", "   ├── ")
                except Exception as e:
                    color_log("PQC", "WARNING", f"[SERVER] Attempt {attempt + 1} failed: {e}", "   ├── ")
                    if attempt < retries - 1:
                        time.sleep(delay)  # Wait before retrying
        elif self.role == "CLIENT":
            for attempt in range(retries):
                # Check if timeout has been reached
                if time.time() - start_time > timeout:
                    color_log("PQC", "KO", "[CLIENT] Timeout reached during key exchange.", "   ├── ")
                    raise PQCException("Key exchange failed: Timeout reached.")
                try:
                    # CLIENT: Generate keypair, send public key, and receive shared secret
                    public_key = self.kem.generate_keypair()
                    color_log("PQC", "INFO", "[CLIENT] Generated public key, sending to server...", "   ├── ")
                    self.secure_socket.sendall(public_key)

                    # Set timeout for receiving the server response
                    self.secure_socket.settimeout(timeout - (time.time() - start_time))

                    # Wait for server to send ciphertext
                    color_log("PQC", "INFO", "[CLIENT] Waiting for ciphertext from server...", "   ├── ")
                    response = self.secure_socket.recv(4096)
                    data = ast.literal_eval(response.decode('utf-8'))
                    shared_secret = data['shared_secret']
                    color_log("PQC", "OK", f"[CLIENT] Received shared secret: {list(shared_secret)}", "   ├── ")
                    return shared_secret
                except Exception as e:
                    color_log("PQC", "WARNING", f"[CLIENT] Attempt {attempt + 1} failed: {e}", "   ├── ")
                    if attempt < retries - 1:
                        time.sleep(delay)  # Wait before retrying
                    else:
                        color_log("PQC", "KO", "[CLIENT] Failed to exchange keys after multiple attempts.", "   ├── ")
                        raise PQCException("Key exchange failed")

            color_log("PQC", "KO", "[SERVER] Failed to exchange keys after multiple attempts.", "   ├── ")
            raise PQCException("Key exchange failed")

        else:
            raise ValueError("Invalid role. Must be 'CLIENT' or 'SERVER'.")

    def close_socket(self):
        """
        Closes the socket connection.
        """
        if self.secure_socket:
            try:
                self.secure_socket.close()
                color_log("PQC", "OK", f"[{self.role}] Socket connection closed.", "   ├── ")
            except Exception as e:
                color_log("PQC", "ERROR", f"[{self.role}] Failed to close socket: {e}", "   ├── ")
            finally:
                self.secure_socket = None
