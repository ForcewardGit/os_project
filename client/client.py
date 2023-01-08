""" Module that defines all the logic of the client.
"""
from threading import Thread, Lock
from socket import socket, AF_INET, SOCK_STREAM, gaierror, timeout
from .cmd_handlers import connect_cmd, disconnect_cmd, lu_cmd, lf_cmd, send_cmd
from .protocol import CONNECT, DISCONNECT, LU, LF, MESSAGE
from .loggers import main_logger, sec_logger
from .global_vars import SERVER_IP, MAIN_PORT, RECEIVE_PORT, BUF_SIZE, \
    SERVER_BUF_SIZE, prompt_msg 


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
    
    def receive_msg(self, sock: socket) -> str:
        """ Receives the whole message from the `socket` whichever the buffer
            size is.
            Returns the encoded message received from `sock`.
        """
        msg = sock.recv(BUF_SIZE).decode()
        return msg
    
    def check_username(self, username: str) -> str:
        """ Checks the username, if it's valid, returns itself, if not -> 
            returns a string representing error message.
        """
        if len(username) < 3:
            return "Username must contain at least 3 characters"
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
    
    def check_user_input(self, user_input):
        if len(user_input) > SERVER_BUF_SIZE:
            raise TypeError(
                f"Too long input. Max input size is {SERVER_BUF_SIZE}")
    
    def receive_data(self, sock: socket) -> str:
        """ Receive whole data sent from client with size of data + space + 
            data content. 
            Return the whole received data.
        """
        msg = sock.recv(BUF_SIZE).decode().split(maxsplit=1)
        msg_size = int(msg[0])
        msg_data = msg[1]
        received_bytes = len(msg_data)
        total_received_bytes = received_bytes
        whole_message = msg_data
        while total_received_bytes < msg_size:
            msg = sock.recv(BUF_SIZE).decode()
            received_bytes = len(msg)
            whole_message += msg
            total_received_bytes += received_bytes       
        return whole_message

    def receive_msg_from_other_users(self):
        """ Always wait at port 2 for a new message from other users.
            Technically, we are connecting to server with SERVER_IP waiting at
            port 2 (RECEIVE_PORT).
        """
        # Always wait for a new message #
        while True:
            try:
                # BLOCKED HERE #
                command = self.receive_msg(self.receive_socket)
                if command:
                    msg = self.receive_data(self.receive_socket)
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
                self.check_user_input(user_input)
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
                        main_logger.info(self.whoami())
                    case "quit":
                        # Disconnect from server and finish the client program
                        self.disconnect(*params)
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
                message = self.receive_msg(self.com_socket)
                if message == "OK":
                    self.connected = True if self.com_socket else False
                    self.username = username
                    self.connect_to_port2()
                    self.receiving_thread = Thread(target=self.receive_msg_from_other_users)
                    self.receiving_thread.start()
                    main_logger.info(f"Successfully connected to server with ip={ip}")
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
            message = self.receive_msg(self.com_socket)
            if message.startswith("Error"):
                main_logger.error(message.removeprefix("Error: "))
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
                server_response = self.receive_msg(self.com_socket)
                if server_response.startswith("Error: "):
                    main_logger.error(server_response)
                else:
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
                server_response = self.receive_msg(self.com_socket)
                if server_response.startswith("Error: "):
                    error_msg = server_response.removeprefix("Error: ")
                    main_logger.error(error_msg)
                else:
                    main_logger.info(server_response)
        else:
            main_logger.warning("There was no connection")

    def lf(self):
        """ List all the files of our server's folder.
        """
        if self.connected:
            if lf_cmd(self.com_socket):
                server_response = self.receive_msg(self.com_socket)
                main_logger.info(server_response)
            else:
                self.disconnect_attrs()
        else:
            main_logger.warning("There was no connection")
