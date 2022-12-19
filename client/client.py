""" Module that defines all the logic of the client.
"""
import logging
from io import StringIO
from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM, gaierror, timeout
from .cmd_handlers import connect_cmd, disconnect_cmd, lu_cmd, lf_cmd, send_cmd


# Format log messages #
log_format = "%(levelname)s: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=log_format)

# Global Variables #
SERVER_IP = "localhost"
PORT = 2021
RECEIVE_PORT = 2022
BUF_SIZE = 100
automatic_input = False
available_commands = ["connect", "disconnect", "lu", "lf", "send", "whoami"]


class Client:
    """ Client class which implements the logic of client objects. 
        Call ask_command() method in order to start the client.
    """
    def __init__(self) -> None:
        """ Initialization of client object.
        """
        self.username = None
        self.connected = False
        self.connected_port2 = False
        self.com_socket: socket = None
        self.receive_socket: socket = None
        self.receiving_thread: Thread = None
    
    def whoami(self) -> str:
        return self.username
    
    def is_socket_closed(self, s: socket) -> bool:
        try:
            return s.fileno() == -1
        except Exception:
            return False
    
    def debug_attrs(self):
        """ Method to keep track of client attributes [for debugging].
        """
        try:
            logging.debug(f"username: {self.username}")
            logging.debug(f"connected: {self.connected}")
            logging.debug(f"connected_port2: {self.connected_port2}")
            logging.debug(f"com_socket: {not self.is_socket_closed(self.com_socket)}")
            logging.debug(f"receive_socket: {not self.is_socket_closed(self.receive_socket)}")
            logging.debug(f"receiving_thread: {self.receiving_thread.is_alive()}")
        except Exception:
            pass
    
    def check_server(self) -> bool:
        """ Checks whether a server is alive.
        """
        try:
            self.com_socket.settimeout(1.0)
            self.com_socket.recv(BUF_SIZE).decode()
        except Exception:
            self.connected = False
            self.com_socket = None
            return False
        else:
            return True

    def receive_msg_from_other_users(self):
        """ Always wait at port 2 for a new message from other users.
            Technically, we are connecting to server with SERVER_IP waiting at
            port 2 (RECEIVE_PORT).
        """
        # Always wait for a new message #
        while True:
            try:
                # BLOCKED HERE #
                msg = self.receive_socket.recv(BUF_SIZE).decode()
                username, message = msg.split(" ", 1)
                
                logging.info(f"{username}: {message}")
            except ConnectionResetError as exc:
                logging.error(f"{exc.strerror}")
                self.connected = False
                self.connected_port2 = False
                self.receive_socket.close()
                self.com_socket.close()
                break
            except Exception as exc:
                # logging.error(exc)
                break
    
    def automatic_input(self):
        """ Get the input from user and return command and parameters
        """
        import sys
        class as_stdin:
            def __init__(self, buffer):
                self.buffer = buffer
                self.original_stdin = sys.stdin
            def __enter__(self):
                sys.stdin = self.buffer
            def __exit__(self, *exc):
                sys.stdin = self.original_stdin
        return as_stdin
    
    def ask_command(self):
        """ Method which is runned automatically when the client object is 
            created. Always asks the user for input, matches it with appropriate
            methods.
        """
        while True:
            try:
                user_input = input("Enter a command: ")
                user_input = user_input.split(maxsplit=2)
                command = user_input[0].lower()
                params = user_input[1:] if len(user_input)>1 else []
                match command:
                    case "connect":
                        self.connect(*params)
                        # self.debug_attrs()
                    case "disconnect":
                        self.disconnect(*params)
                        self.debug_attrs()
                        continue
                    case "lu":
                        self.lu(*params)
                        self.debug_attrs()
                    case "lf":
                        self.lf(*params)
                        self.debug_attrs()
                    case "send":
                        self.send(*params)
                        self.debug_attrs()
                    case "whoami":
                        logging.info(self.whoami())
                    case "quit":
                        # Disconnect from server and finish the client program
                        self.disconnect(*params)
                        self.debug_attrs()
                        break
                    case _:
                        logging.warning(f"Command '{command}' not found")
            except IndexError:
                logging.warning("Type a valid input")
            except ValueError as exc:
                logging.warning(exc)
            except TypeError as exc:
                logging.error(exc)
            except ConnectionResetError as exc:
                logging.error(exc.strerror)
            except ConnectionRefusedError as exc:
                logging.error(exc)

    def connect_to_port2(self):
        """ Connect receive_socket to the server's 2022
        """
        try:
            self.receive_socket = socket(AF_INET, SOCK_STREAM)
            self.receive_socket.connect((SERVER_IP, RECEIVE_PORT))
            self.connected_port2 = True
        except Exception as exc:
            logging.debug(exc)

    def connect(self, username: str, ip: str):
        """ Connect to the server with given `ip` and `port`.
        """
        ip = "127.0.0.1" if ip == "localhost" else ip
        ip = ip.rstrip()
        SERVER_IP = ip
        port = PORT

        if not self.connected:
            self.com_socket = connect_cmd(ip, port)
            if self.com_socket:
                self.com_socket.send(f"connect {username} {ip}".encode())
                message = self.com_socket.recv(BUF_SIZE).decode()
                if message == "OK":
                    self.connected = True if self.com_socket else False
                    self.username = username
                    self.connect_to_port2()
                    self.receiving_thread = Thread(target=self.receive_msg_from_other_users)
                    self.receiving_thread.start()
                    logging.info(f"Successfully connected to server with ip={ip}")
                else:
                    logging.error(message)
        elif self.connected:
            logging.warning("Already connected")

    def disconnect(self):
        """ Disconnect from the server, to which our client is currently
            connected.
        """
        if self.connected:
            disconnect_cmd(self.com_socket)
            message = self.com_socket.recv(BUF_SIZE).decode()
            if message.startswith("Error"):
                logging.error(message.removeprefix("Error: "))
                return None
            self.connected = False
            self.connected_port2 = False
            self.username = ""
            logging.info(message)
            self.receive_socket.close()
            self.com_socket.close()
        else:
            logging.warning("There was no connection")

    def lu(self):
        """ Print all the users which are currently connected to the server,
            to which our client is also connected
        """
        if self.connected:
            if lu_cmd(self.com_socket):
                server_response = self.com_socket.recv(BUF_SIZE).decode()
                logging.info(server_response)
            else:
                self.connected = False
        else:
            logging.warning("There was no connection")

    def send(self, username: str, message: str):
        """ Send a message to another user with username = `username`
        """
        message = message.rstrip()  # Make sure that the user didn't put any unnecessary spaces
        # Check whether `message` parameter is legal #
        if not (message.startswith("\"") and message.endswith("\"")):
            raise ValueError("Message should be written in double quotes!")

        # If everything is OK #
        if self.connected:
            if send_cmd(self.com_socket, username, message):
                server_response = self.com_socket.recv(BUF_SIZE).decode()
                if server_response.startswith("Error: "):
                    error_msg = server_response.removeprefix("Error: ")
                    logging.error(error_msg)
                else:
                    logging.info(server_response)
        else:
            logging.warning("There was no connection")

    def lf(self):
        """ List all the files of our server's folder.
        """
        if self.connected:
            if lf_cmd(self.com_socket):
                server_response = self.com_socket.recv(BUF_SIZE).decode()
                logging.info(server_response)
            else:
                self.connected = False
        else:
            logging.warning("There was no connection")
