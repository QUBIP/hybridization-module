import socket


def receive_nbytes(sock: socket.socket, num_bytes: int) -> bytes:
    """Uses the socket (sock) to receive exactly a num_bytes amount of bytes

    IMPORTANT: The socket must be already connected to another one.

    Note: This method is used because sock.recv does not guarantee the buffer it returns
    has the size you asked.

    Args:
        sock (socket.socket): The socket that will be used for the connection
        num_bytes (int): The amount of bytes you expect to receive.

    Returns:
        bytes: A buffer with a bytes object of lenght num_bytes
    """
    buffer = b''

    while len(buffer) < num_bytes:
        received_data = sock.recv(num_bytes-len(buffer))
        buffer += received_data

    return buffer
