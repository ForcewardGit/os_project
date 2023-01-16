""" Module that defines some global variables for client application.

    The module is not intended to be runned. Only constants are 
    imported by other modules.

    Defined constants
    -----------------
    SERVER_IP : str
        The ip address of server
    MAIN_PORT : str
        Port number, which is used for main communication with server
    RECEIVE_PORT : str
        Port number, which is used to listen for messages delivered by 
        server clients
    BUF_SIZE : int
        The buffer size of a client
    SERVER_BUF_SIZE : str
        The buffer size of a server
    prompt_msg : str
        The message which is prompted when receiving input from user
    error_prefix : str
        The prefix of messages sent by server to differentiate errors
"""

SERVER_IP = "127.0.0.1"
MAIN_PORT = 2021
RECEIVE_PORT = 2022
BUF_SIZE = 128
SERVER_BUF_SIZE = 4096
prompt_msg = "Enter a command: "
error_prefix = "Error: "
