from socket import socket, inet_aton, error

def validate_socket(sock: socket) -> bool:
    """Returns True if socket is closed, otherwise False
    
    Parameters
    ----------
    sock : socket
        The socket of the client
    """

    try:
        return sock.fileno() == -1
        # fileno() will return -1 for closed sockets.
    except Exception:
        return False

def validate_ip(ip: str) -> bool:
    """Validates username, returns itself if it's valid.
    Otherwise, returns appropriate `error` message.
    
    Parameters
    ----------
    ip : str
        IP address of client, that will be checked for validity
    """

    try:
        inet_aton(ip)
        return ip
    except error:
        return "IP address is not valid!"
    
def validate_username(username: str) -> bool:
    """Validates username, returns itself if it's valid.
    Otherwise, returns appropriate `error` message.
    
    Parameters
    ----------
    username : str
        Username of the client, that will be checked for validity
    """

    if len(username) < 4:
        return "Too short! Username shold be at least 3 characters."
    elif len(username) > 20:
        return "Too long! Username should be at most 20 characters."
    if not username[0].isalpha():
        return "Username should start with alphabetic character."
    return username

def validate_input( user_input: str, buffer_size: int) -> None:
    """Checks if user input is not exceeded buffer size
    
    Parameters
    ----------
    user_input : str
        Input from user, that will be checked for validity
    buffer_size : int
        The capacity of the buffer

    Raises
    ------
    TypeError
        If user_input is greater then BUFFER_SIZE
    """

    if len(user_input) > buffer_size:
        raise TypeError(
            f"Too many characters. Max allowed input size is {buffer_size}"
        )