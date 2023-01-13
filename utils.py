""" Module that defines some universal functions for both client and server.
"""

from socket import socket


def send_msg_through_socket(sock: socket, message: str):
    """ Sends a given `message` through a given `sock` object.
    """
    sock.sendall(message.encode())


def receive_msg( sock: socket, buffer_size: int) -> str:
    """ Receives `BUF_SIZE` bytes from `sock`.
        Returns the encoded message.
    """
    msg = sock.recv(buffer_size).decode()
    return msg


def receive_whole_data(sock: socket, buffer_size: int) -> str:
    """ Receive whole data sent from `sock` with size of data + space + data 
        content.
        Return the whole received data.
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
