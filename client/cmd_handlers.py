""" Contains functions sending commands to server according to protocol.
    
    The logic of all of 
    them are similar: send message to server and return something, if 
    message cannot be sent, return some other thing.

    PROTOCOL:                         responsible function
    ---------------------------------------------------------
    `CONNECT USERNAME`              - connect_cmd(*params)
    `DISCONNECT`                    - disconnect_cmd(*params)
    `LU`                            - lu_cmd(*params)
    `LF`                            - lf_cmd(*params)
    `MESSAGE USER\nMSGSIZE MSGDATA` - send_cmd(*params)
"""

from socket import socket
from utils import send_msg_through_socket
from protocol import CONNECT, DISCONNECT, LU, LF, MESSAGE, READ, WRITE,\
    OVERWRITE, OVERREAD, APPEND, APPENDFILE
from .loggers import main_logger


def connect_cmd(s: socket, username: str):
    """ Send connection command to server.
    """
    try:
        m = f"{CONNECT} {username}"
        send_msg_through_socket(s, m)
        return 1
    except Exception as exc:
        main_logger.error(f"{exc}")
    return 0

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


def write_cmd(s: socket, file_name: str):
    """ Sends to server the request write `file_name`.
    """
    try:
        FILENAME = file_name
        m = f"{WRITE} {FILENAME}"
        send_msg_through_socket(s, m)
        return 1
    except Exception as exc:
        main_logger.error(exc)
        return 0


def send_file_cmd(s: socket, file_content: str, file_size: int):
    """ Sends to server the content and size of the file that's already created
        in server.
    """
    try:
        FILESIZE = file_size
        FILEDATA = file_content
        m = f"{FILESIZE} {FILEDATA}"
        send_msg_through_socket(s, m)
        return 1
    except Exception as exc:
        main_logger.error(exc)
        return 0


def overwrite_cmd(s: socket, file_name: str):
    """ Sends to server the request to overwrite the `file_name`.
    """
    try:
        FILENAME = file_name
        m = f"{OVERWRITE} {FILENAME}"
        send_msg_through_socket(s, m)
        return 1
    except Exception as exc:
        main_logger.error(exc)
        return 0

def overread_cmd(s: socket, file_name: str):
    """ Sends to server the request to update `file_name`
    """
    try:
        FILENAME = file_name
        m = f"{OVERREAD} {FILENAME}"
        send_msg_through_socket(s, m)
        return 1
    except Exception as exc:
        main_logger.error(exc)
        return 0

def append_cmd(s: socket, file_name: str):
    """ Ask server for a content of `file_name` file.
    """
    try:
        FILENAME = file_name
        m = f"{APPEND} {FILENAME}"
        send_msg_through_socket(s, m)
        return 1
    except Exception as exc:
        main_logger.error(exc)
        return 0

def appendfile_cmd(s: socket, client_fname: str, server_fname):
    """ Sending command to server to update
    """
    try:
        SRC_FILENAME = client_fname
        DST_FILENAME = server_fname
        m = f"{APPENDFILE} {SRC_FILENAME} {DST_FILENAME}"
        send_msg_through_socket(s, m)
        return 1
    except Exception as exc:
        main_logger.error(exc)
        return 0
