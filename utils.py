""" Module defines some universal functions for both client and server.

    The module is not intended to be runned! The module is used by
    client and server.

    Used built-in modules
    ---------------------
    socket

    Defined functions
    -----------------
    send_msg_through_socket(sock: socket, message: str)
        Sends a given `message` through a given `sock` object
    receive_msg(sock: socket, buffer_size: int)
        Receives `BUF_SIZE` bytes from `sock`
    receive_whole_data(sock: socket, buffer_size: int) -> str:
        Receives whole data sent from `sock` with size of 
        (data + space + data content)
"""

from socket import socket


def send_msg_through_socket(sock: socket, message: str):
    """ Sends a given `message` through a given `sock` object.

        Parameters
        ----------
        sock : socket
        message : str

        Returns
        -------
        None
    """
    sock.sendall(message.encode())


def receive_msg(sock: socket, buffer_size: int) -> str:
    """ Receives `BUF_SIZE` bytes from `sock`.

        Parameters
        ----------
        sock : socket
            The socket object from which we are going to receive msg
        buffer_size : int
            The buffer size of a receiver (server/client)

        Returns 
        -------
        str
            the encoded message.
    """
    msg = sock.recv(buffer_size).decode()
    return msg


def receive_whole_data(sock: socket, buffer_size: int) -> str:
    """ Receives whole data sent from `sock` with size of 
        (data + space + data content)

        Parameters
        ----------
        sock : str
            the socket object from which we're receiving data
        buffer_size : int
            The buffer size of a receiver

        Returns
        -------
        str
            the whole received data.
    """
    msg = sock.recv(buffer_size).decode().split(maxsplit=1)
    try:
        msg_size = int(msg[0])
        msg_data = msg[1]
    except ValueError:
        return " ".join(msg)
        
    received_bytes = len(msg_data)
    total_received_bytes = received_bytes
    whole_message = msg_data
    while total_received_bytes < msg_size:
        msg = sock.recv(buffer_size).decode()
        received_bytes = len(msg)
        whole_message += msg
        total_received_bytes += received_bytes      
    return whole_message
