from socket import socket, AF_INET, SOCK_STREAM
import logging


# Format log messages #
logging.basicConfig(level=logging.INFO)


def connect_cmd(port: int, ip: str):
    """ Create the socket, connect it to the server and return it
    """
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((ip, port))
        return s
    except Exception as exc:
        logging.error(f"{exc}")
        return None


def disconnect_cmd(s: socket):
    """ Sends a server a message for disconnection.
    """
    try:
        s.send("disconnect".encode())
    except Exception as exc:
        logging.error(exc)


def lu_cmd(s: socket):
    try:
        s.send("lu".encode())
    except Exception as exc:
        logging.error(exc)


def lf_cmd(s: socket):
    try:
        s.send("lf".encode())
    except Exception as exc:
        logging.error(exc)
