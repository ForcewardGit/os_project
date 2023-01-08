from socket import socket

def send_msg_through_socket(sock: socket, message: str):
    """ Sends a given `message` through a given `sock` object.
    """
    sock.sendall(message.encode())