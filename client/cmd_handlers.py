""" Module that contains helper functions for the client. The logic of all of 
    them are similar: send message to server and return something, if message
    cannot be sent, return some other thing.

    PROTOCOL:                         responsible function
    ---------------------------------------------------------
    `CONNECT USERNAME`              - connect_cmd(*params)
    `DISCONNECT`                    - disconnect_cmd(*params)
    `LU`                            - lu_cmd(*params)
    `LF`                            - lf_cmd(*params)
    `MESSAGE USER\nMSGSIZE MSGDATA` - send_cmd(*params)
"""

from socket import socket, AF_INET, SOCK_STREAM, gaierror, timeout
from .protocol import CONNECT, DISCONNECT, LU, LF, MESSAGE, READ
from utils import send_msg_through_socket
from .loggers import main_logger


def connect_cmd(ip: str, port: int) -> socket | None:
    """ Create the socket, connect it to the server and return it
    """
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((ip, port))
        return s
    except ConnectionRefusedError as exc:
        main_logger.error(f"{exc.strerror}")
    except gaierror:
        main_logger.error("Invalid IP address")
    except TimeoutError as exc:
        main_logger.error(exc.strerror)
    return None


def disconnect_cmd(s: socket):
    """ Sends to server a message for disconnection.
    """
    try:
        send_msg_through_socket(s, DISCONNECT)
        return 1
    except ConnectionResetError as exc:
        pass
    except Exception as exc:
        main_logger.error(f"{exc}")
    return 0


def lu_cmd(s: socket):
    """ Asks server to get list of all connected users
    """
    try:
        send_msg_through_socket(s, LU)
        return 1
    except Exception as exc:
        main_logger.error(f"{exc}")
    return 0


def lf_cmd(s: socket):
    """ Asks server to get list of all files in server's directory
    """
    try:
        send_msg_through_socket(s, LF)
        return 1
    except Exception as exc:
        main_logger.error(f"{exc}")
        return 0


def send_cmd(s: socket, username: str, message: str):
    """ Sends to server a message for another user with username=`username`.
        The two-step process is carried out.
    """
    try:
        USER = username
        MSGSIZE, MSGDATA = len(message), message
        m = f"{MESSAGE} {USER}"
        send_msg_through_socket(s, m)
        m = f"{MSGSIZE} {MSGDATA}"
        send_msg_through_socket(s, m)
        return 1
    except Exception as exc:
        main_logger.error(exc)
        return 0


def read_cmd(s: socket, file_name: str):
    """ Ask server for a content of `file_name` file.
    """
    try:
        FILENAME = file_name
        m = f"{READ} {FILENAME}"
        send_msg_through_socket(s, m)
        return 1
    except Exception as exc:
        main_logger.error(exc)
        return 0
