""" Module that defines all the logic of the client.
"""

import os
from threading import Thread, Lock
from socket import socket, AF_INET, SOCK_STREAM, gaierror, timeout

from utils import receive_whole_data, receive_msg
from .loggers import main_logger, sec_logger
from .global_vars import SERVER_IP, MAIN_PORT, RECEIVE_PORT, BUF_SIZE, \
    SERVER_BUF_SIZE, prompt_msg, error_prefix
from .cmd_handlers import connect_cmd, disconnect_cmd, lu_cmd, lf_cmd, \
    send_cmd, read_cmd, write_cmd, send_file_cmd, overwrite_cmd, \
        overread_cmd, append_cmd, appendfile_cmd


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
                    case "overread":
                        self.overread(*params)
                    case "append":
                        self.append(*params)
                    case "appendfile":
                        self.appendfile(*params)
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
    
    def connect_to_server(self, ip, port) -> socket | None:
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
            self.com_socket = self.connect_to_server(ip, port)
            if self.com_socket:
                if connect_cmd(self.com_socket, username):
                    message = receive_msg(self.com_socket, BUF_SIZE)
                    if message == "OK":
                        self.connected = True if self.com_socket else False
                        self.username = username
                        self.connect_to_port2()
                        self.receiving_thread = Thread(
                            target=self.receive_msg_from_other_users)
                        self.receiving_thread.start()
                        m = f"Successfully connected to server with ip={ip}"
                        main_logger.info(m)
                    else:
                        main_logger.error(message)
                else:
                    self.disconnect_attrs()

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
        """ Request the server's `file_name` content and save it. 
        """
        directory_items = os.listdir(os.path.join(os.getcwd(), "client"))
        directory_items = [item for item in directory_items 
                                if not item.startswith("__")]
        if self.connected:
            if file_name in directory_items:
                main_logger.error(f"{file_name} is already in client")
                return None
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
                        try:
                            with open(os.path.join("client", file_name), "w") \
                                as f:
                                f.write(file_content)
                        except Exception as exc:
                            main_logger.error(exc)
                        else:
                            m = "The file was received successfully!"
                            main_logger.info(m)
                        # self.print_file_content(file_content)
            else:
                self.disconnect_attrs(os.path.join(os.getcwd(), "client"))
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
                self.disconnect_attrs()
        else:
            main_logger.warning("There was no connection")
    
    def overread(self, file_name: str):
        """ Updates `file_name` in client from the one in server.
        """
        directory_items = os.listdir(os.path.join(os.getcwd(), "client"))
        directory_items = [item for item in directory_items 
                                if not item.startswith("__")]
        if self.connected:
            if file_name in directory_items and file_name.endswith(".py"):
                main_logger.error(f"{file_name} cannot be modified")
                return None
            if overread_cmd(self.com_socket, file_name):
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
                        try:
                            with open(os.path.join("client", file_name), "w") \
                                as f:
                                f.write(file_content)
                        except Exception as exc:
                            main_logger.error(exc)
                        else:
                            m = "The file was received successfully!"
                            main_logger.info(m)
                        # self.print_file_content(file_content)
            else:
                self.disconnect_attrs(os.path.join(os.getcwd(), "client"))
        else:
            main_logger.warning("There was no connection")
 
    def append(self, new_content: str, file_name: str):
        """ Request a server to get the file `file_name` and overwrite that file
            in the client.
        """
        mix_params = file_name.split()
        file_name = mix_params.pop()
        new_content += " " if len(mix_params)>0 else ""
        new_content += " ".join(mix_params)
        if not (new_content.startswith("\"") and new_content.endswith("\"")):
            raise ValueError("Message should be written in double quotes!")
        new_content = new_content.removeprefix("\"").removesuffix("\"")

        if self.connected:
            if append_cmd(self.com_socket, file_name):
                server_response = receive_msg(self.com_socket, BUF_SIZE)
                if server_response.startswith(error_prefix):
                    error_msg = server_response.removeprefix(error_prefix)
                    main_logger.error(error_msg)
                else:
                    main_logger.info(f"Server is ready to update {file_name}")
                    if send_file_cmd(self.com_socket, new_content, 
                        len(new_content)):
                        server_response2 = receive_msg(self.com_socket, BUF_SIZE)
                        if server_response2.startswith(error_prefix):
                            err_m = server_response2.removeprefix(error_prefix)
                            main_logger.error(err_m)
                        else:
                            m = f"Finished appending {file_name} in server"
                            main_logger.info(m)
                    else:
                        self.disconnect_attrs()
            else:
                self.disconnect_attrs()
        else:
            main_logger.warning("There was no connection")
    
    def appendfile(self, src_fname: str, dst_fname):
        """ Get the content of `src_fname` and append to server's `dst_fname`
        """
        directory_items = os.listdir(os.path.join(os.getcwd(), "client"))
        directory_items = [item for item in directory_items 
                                if not item.startswith("__")]
        if src_fname in directory_items:
            with open(os.path.join("client", src_fname), "r") as f:
                src_content = f.read()
                src_content_size = len(src_content)
        if self.connected:
            if src_fname not in directory_items:
                m = f"Source file {src_fname} not found in client"
                main_logger.error(m)
                return None
            if appendfile_cmd(self.com_socket, src_fname, dst_fname):
                server_response = receive_msg(self.com_socket, BUF_SIZE)
                if server_response.startswith(error_prefix):
                    error_msg = server_response.removeprefix(error_prefix)
                    main_logger.error(error_msg)
                else:
                    m = f"Server is ready to update {dst_fname}"
                    main_logger.info(m)
                    if send_file_cmd(self.com_socket, src_content, 
                        src_content_size):
                        server_response2 = receive_msg(self.com_socket, BUF_SIZE)
                        if server_response2.startswith(error_prefix):
                            err_m = server_response2.removeprefix(error_prefix)
                            main_logger.error(err_m)
                        else:
                            m = f"Finished appending {src_fname} to {dst_fname}"
                            main_logger.info(m)
                    else:
                        self.disconnect_attrs()
            else:
                self.disconnect_attrs()
        else:
            main_logger.warning("There was no connection")
