""" Module that contains helper functions for the client. The logic of all of 
    them are similar: send message to server and return something, if message
    cannot be sent, return some other thing.
"""

from socket import socket, AF_INET, SOCK_STREAM, gaierror, timeout
import logging


# Format log messages #
# log_format = "%(levelname)s: %(message)s"
# logging.basicConfig(level=logging.DEBUG, format=log_format)


def connect_cmd(ip: str, port: int):
    """ Create the socket, connect it to the server and return it
    """
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((ip, port))
        return s
    except ConnectionRefusedError as exc:
        logging.error(f"{exc.strerror}")
    except gaierror:
        logging.error("Invalid IP address")
    except TimeoutError as exc:
        logging.error(exc.strerror)
    return None


def disconnect_cmd(s: socket):
    """ Sends to server a message for disconnection.
    """
    try:
        s.send("disconnect".encode())
        return 1
    except ConnectionResetError as exc:
        pass
    except Exception as exc:
        logging.error(f"{exc}")
    return 0


def lu_cmd(s: socket):
    """ Asks server to get list of all connected users
    """
    try:
        s.send("lu".encode())
        return 1
    except Exception as exc:
        logging.error(f"{exc}")
    return 0


def lf_cmd(s: socket):
    """ Asks server to get list of all files in server's directory
    """
    try:
        s.send("lf".encode())
        return 1
    except Exception as exc:
        logging.error(f"{exc}")
        return 0

def send_cmd(s: socket, username: str, message: str):
    """ 
    """
    try:
        m = f"send {username} {message}"
        s.send(m.encode())
        return 1
    except Exception as exc:
        logging.error(exc)
        return 0