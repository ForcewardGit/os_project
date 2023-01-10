""" Module that defines all the logic of the client.
"""
import os
from threading import Thread, Lock
from socket import socket, AF_INET, SOCK_STREAM, gaierror, timeout
from .loggers import main_logger, sec_logger
from .cmd_handlers import connect_cmd, disconnect_cmd, lu_cmd, lf_cmd, send_cmd,\
    read_cmd, write_cmd, send_file_cmd, overwrite_cmd
from .global_vars import SERVER_IP, MAIN_PORT, RECEIVE_PORT, BUF_SIZE, \
    SERVER_BUF_SIZE, prompt_msg, error_prefix
from utils import send_msg_through_socket, receive_whole_data, receive_msg


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
        self.print_lock = Lock()
        self.message_received = False
    
    def whoami(self) -> str:
        """ Returns the username to the user.
        """
        return self.username
    
    def is_socket_closed(self, s: socket) -> bool:
        try:
            return s.fileno() == -1
        except Exception:
            return False
    
    def check_username(self, username: str) -> str:
        """ Checks the username, if it's valid, returns itself, if not -> 
            returns a string representing error message.
        """
        if len(username) < 3 or len(username) > 30:
            return "Username must contain at least 3 characters and at most 30"
        if not username[0].isalpha():
            return "Username should start with alphabetic character"
        return username
            
    def disconnect_attrs(self):
        """ When connection lost with server by any reason, resets all the 
            necessary attributes.
        """
        if self.connected:
            self.connected = False
        if self.connected_port2:
            self.connected_port2 = False
        if not self.is_socket_closed(self.receive_socket):
            self.receive_socket.close()
        if not self.is_socket_closed(self.com_socket):
            self.com_socket.close()
        self.username = ""
    
    def debug_attrs(self):
        """ Method to keep track of client attributes [for debugging].
        """
        try:
            main_logger.debug(f"username: {self.username}")
            main_logger.debug(f"connected: {self.connected}")
            main_logger.debug(f"connected_port2: {self.connected_port2}")
            main_logger.debug(f"com_socket: {not self.is_socket_closed(self.com_socket)}")
            main_logger.debug(f"receive_socket: {not self.is_socket_closed(self.receive_socket)}")
            main_logger.debug(f"receiving_thread: {self.receiving_thread.is_alive()}")
        except Exception:
            pass
    
    def check_user_input_size(self, user_input: str):
        if len(user_input) > SERVER_BUF_SIZE:
            raise TypeError(
                f"Too long input. Max input size is {SERVER_BUF_SIZE}")

    def print_file_content(self, file_content: str):
        """ Gets the file content and prints it in a beautiful way.
        """
        print("-"*80)
        print(file_content)
        print("-"*80)

    def receive_msg_from_other_users(self):
        """ Always wait at port 2 for a new message from other users.
            Technically, we are connecting to server with SERVER_IP waiting at
            port 2 (RECEIVE_PORT).
        """
        # Always wait for a new message #
        while True:
            try:
                # BLOCKED HERE #
                command = receive_msg(self.receive_socket, BUF_SIZE)
                if command:
                    msg = receive_whole_data(self.receive_socket, BUF_SIZE)
                    sec_logger.info(f"{msg}")
                else:
                    break

            except ConnectionResetError as exc:
                sec_logger.error(f"{exc.strerror}")
                self.disconnect_attrs()
                break
            except Exception as exc:
                # main_logger.error(exc)
                break
    
    def ask_command(self):
        """ Method which is runned automatically when the client object is 
            created. Always asks the user for input, matches it with appropriate
            methods.
        """
        while True:
            try:
                user_input = input(prompt_msg)
                self.check_user_input_size(user_input)
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
                    case "read":
                        self.read(*params)
                    case "write":
                        self.write(*params)
                    case "overwrite":
                        self.overwrite(*params)
                    case "whoami":
                        main_logger.info(self.whoami())
                    case "quit":
                        # Disconnect from server and finish the client program
                        self.disconnect(*params)
                        main_logger.info("Client finished his job!")
                        self.debug_attrs()
                        break
                    case _:
                        main_logger.warning(f"Command '{command}' not found")
            except IndexError:
                main_logger.warning("Type a valid input")
            except ValueError as exc:
                main_logger.warning(exc)
            except TypeError as exc:
                main_logger.error(exc)
            except ConnectionResetError as exc:
                main_logger.error(exc.strerror)
            except ConnectionRefusedError as exc:
                main_logger.error(f"{exc.strerror}")

    def connect_to_port2(self):
        """ Connect `receive_socket` to the server's 2022 port.
        """
        try:
            self.receive_socket = socket(AF_INET, SOCK_STREAM)
            self.receive_socket.connect((SERVER_IP, RECEIVE_PORT))
            self.connected_port2 = True
        except Exception as exc:
            main_logger.debug(exc)

    def connect(self, username: str, ip: str):
        """ Connect to the server with given `ip` and `port`.
        """
        global SERVER_IP        
        ip = "127.0.0.1" if ip == "localhost" else ip
        ip = ip.rstrip()
        SERVER_IP = ip
        port = MAIN_PORT

        username_msg = self.check_username(username)
        if username_msg != username:
            main_logger.warning(f"{username_msg}")
            return None

        if not self.connected:
            self.com_socket = connect_cmd(ip, port)
            if self.com_socket:
                self.com_socket.send(f"CONNECT {username}".encode())
                message = receive_msg(self.com_socket, BUF_SIZE)
                if message == "OK":
                    self.connected = True if self.com_socket else False
                    self.username = username
                    self.connect_to_port2()
                    self.receiving_thread = Thread(
                        target=self.receive_msg_from_other_users)
                    self.receiving_thread.start()
                    info_msg = f"Successfully connected to server with ip={ip}"
                    main_logger.info(info_msg)
                else:
                    main_logger.error(message)
        elif self.connected:
            main_logger.warning("Already connected")

    def disconnect(self):
        """ Disconnect from the server, to which our client is currently
            connected.
        """
        if self.connected:
            disconnect_cmd(self.com_socket)
            message = receive_msg(self.com_socket, BUF_SIZE)
            if message.startswith("Error"):
                main_logger.error(message.removeprefix(error_prefix))
                return None
            self.disconnect_attrs()
            main_logger.info(message)
        else:
            main_logger.warning("There was no connection")

    def lu(self):
        """ Print all the users which are currently connected to the server,
            to which our client is also connected
        """
        if self.connected:
            if lu_cmd(self.com_socket):
                server_response = receive_msg(self.com_socket, BUF_SIZE)
                if server_response.startswith(error_prefix):
                    main_logger.error(server_response)
                else:
                    main_logger.info(server_response)
            else:
                self.disconnect_attrs()
        else:
            main_logger.warning("There was no connection")
    
    def lf(self):
        """ List all the files of our server's folder.
        """
        if self.connected:
            if lf_cmd(self.com_socket):
                server_response = receive_msg(self.com_socket, BUF_SIZE)
                main_logger.info(server_response)
            else:
                self.disconnect_attrs()
        else:
            main_logger.warning("There was no connection")

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
                server_response = receive_msg(self.com_socket, BUF_SIZE)
                if server_response.startswith(error_prefix):
                    error_msg = server_response.removeprefix(error_prefix)
                    main_logger.error(error_msg)
                else:
                    main_logger.info(server_response)
        else:
            main_logger.warning("There was no connection")

    def read(self, file_name: str):
        """ Request the server's `file_name` content and print it on terminal. 
        """
        if self.connected:
            if read_cmd(self.com_socket, file_name):
                server_response = receive_msg(self.com_socket, BUF_SIZE)
                if server_response.startswith(error_prefix):
                    error_msg = server_response.removeprefix(error_prefix)
                    main_logger.error(error_msg)
                else:
                    main_logger.info(server_response)
                    server_response2 = receive_whole_data(
                        self.com_socket, BUF_SIZE)
                    if server_response2.startswith(error_prefix):
                        error_msg = server_response2.removeprefix(error_prefix)
                        main_logger.error(error_msg)
                    else:
                        file_content = server_response2
                        main_logger.info(f"Content of {file_name}:")
                        self.print_file_content(file_content)
            else:
                self.disconnect_attrs()
        else:
            main_logger.warning("There was no connection")
        
    def write(self, file_name: str):
        """ Sends the content of `file_name` to server.
        """
        directory_items = os.listdir(os.path.join(os.getcwd(), "client"))
        directory_items = [item for item in directory_items 
                                if not item.startswith("__")]
        if self.connected:
            if file_name not in directory_items:
                main_logger.error(f"{file_name} is not found in client")
                return None
            
            with open(os.path.join("client", file_name), "r") as f:
                file_data = f.read()
                file_size = len(file_data)
            
            if write_cmd(self.com_socket, file_name):
                server_response = receive_msg(self.com_socket, BUF_SIZE)
                if server_response.startswith(error_prefix):
                    error_msg = server_response.removeprefix(error_prefix)
                    main_logger.error(error_msg)
                else:
                    main_logger.info(f"Server is ready to get contents of {file_name}...")
                    if send_file_cmd(self.com_socket, file_data, file_size):
                        server_response2 = receive_msg(self.com_socket, BUF_SIZE)
                        if server_response.startswith(error_prefix):
                            error_msg = server_response2.removeprefix(error_prefix)
                            main_logger.error(error_msg)
                        else:
                            main_logger.info(server_response2)
                    else:
                        self.disconnect_attrs()
            else:
                self.disconnect_attrs()

        else:
            main_logger.warning("There was no connection")
    
    def overwrite(self, file_name: str):
        """ Transfers the file `file_name` to server. If the server already has
            file `file_name`, that file is updated with the file content sent by
            client.
        """
        directory_items = os.listdir(os.path.join(os.getcwd(), "client"))
        directory_items = [item for item in directory_items 
                                if not item.startswith("__")]
        if self.connected:
            if file_name not in directory_items:
                main_logger.error(f"{file_name} is not found in client")
                return None
            with open(os.path.join("client", file_name), "r") as f:
                file_data = f.read()
                file_size = len(file_data)
            if overwrite_cmd(self.com_socket, file_name):
                server_response = receive_msg(self.com_socket, BUF_SIZE)
                if server_response.startswith(error_prefix):
                    error_msg = server_response.removeprefix(error_prefix)
                    main_logger.error(error_msg)
                else:
                    main_logger.info(f"Server is ready to get contents of {file_name}...")
                    if send_file_cmd(self.com_socket, file_data, file_size):
                        server_response2 = receive_msg(self.com_socket, BUF_SIZE)
                        if server_response.startswith(error_prefix):
                            error_msg = server_response2.removeprefix(error_prefix)
                            main_logger.error(error_msg)
                        else:
                            main_logger.info(server_response2)
                    else:
                        self.disconnect_attrs()
        else:
            main_logger.warning("There was no connection")
