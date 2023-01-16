""" Protocols for client and server to communicate between each other.
    Module defines constant string commands.

    The module is used by both server and client, and, is not intended 
    to be runned!
    
    Defined Variables
    -----------------
    CONNECT : str
        The command protocol used for connection
    DISCONNECT : str
        The command protocol used for disconnection
    LU : str
        The command protocol used for listing the online users in server
    LF : str
        The command protovol user for listing the files in server
    MESSAGE : str
        The command protovol user for communication of clients through
        a server
    READ : str
        The command protovol user for reading a file from server and 
        saving it on client
    WRITE : str
        The command protovol user for writing client's file to server
    OVERWRITE : str
        The command protovol user for overwriting server's file
    OVERREAD : str
        The command protovol user for reading a file from server and 
        overwriting it on client
    APPEND : str
        The command protovol user for appending client's sent data to
        server's file
    APPENDFILE : str
        The command protovol user for appending client's file data to
        server's file
"""

CONNECT = "CONNECT"
DISCONNECT = "DISCONNECT"
LU = "LU"
LF = "LF"
MESSAGE = "MESSAGE"
READ = "READ"
WRITE = "WRITE"
OVERWRITE = "OVERWRITE"
OVERREAD = "OVERREAD"
APPEND = "APPEND"
APPENDFILE = "APPENDFILE"