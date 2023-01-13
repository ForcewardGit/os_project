""" Module that defines all the logic of the server.
"""

import os
import logging
from threading import Thread, Lock
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RD

from protocol import MESSAGE
from utils import send_msg_through_socket, receive_whole_data, receive_msg

# Format log messages #
log_format = "%(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=log_format)

# Global Variables #
SELF_IP = "127.0.0.1"   # IP address of server, by default it is 127.0.0.1
PORT1 = 2021            # Port at which server waits clients and interacts with them
PORT2 = 2022            # Port to which server sends messages whenever accepts them in `send` command
BUF_SIZE = 4096         # Buffer size for receiving items
OK = "OK"               


class Server:
    """ The Server class which implements the logic of Server which can serve
        only 1 client at a time
    """
    def __init__(self, ip=SELF_IP, port1=PORT1, port2=PORT2):
        self.ip = ip
        self.port1 = port1
        self.port2 = port2
        self.clients_port1: dict[str, (tuple, socket)] = {}
        self.clients_port2: dict[str, (tuple, socket)] = {}
        self.active_connections: list[socket] = []
        self.com_socket, self.redirect_socket = self.configure_sockets()
        self.rfile_lock = Lock()
        self.wfile_lock = Lock()

    def configure_sockets(self):
        """ Create and return socket objects. If some error occurred, the method
            returns None. In returned tuple, the first socket is the socket that
            listens in port 1, the second is the one listening in port 2
        """
        try:
            s1 = socket(AF_INET, SOCK_STREAM)
            s2 = socket(AF_INET, SOCK_STREAM)
            s1.bind((self.ip, self.port1))
            s2.bind((self.ip, self.port2))
            s1.listen()
            s2.listen()
            return s1, s2
        except Exception as exc:
            logging.error(exc)
            return None, None
        
    def disconnect_clients(self):
        """ Disconnects all currently connected clients from server.
        """
        for client in self.active_connections:
            client.close()

    def find_username_from_socket(self, s: socket) -> str:
        """ Method assumes that the given socket `s` is connected to one of 
            server's ports.
        """
        for username, (connection, _) in self.clients_port1.items():
            if connection == s:
                conn_username = username
                return conn_username
        for username, (connection, _) in self.clients_port2.items():
            if connection == s:
                conn_username = username
                return conn_username

    def delete_client_data(self, username: str, conn: socket):
        """ Method that removes all data from attributes related to client with 
            username=`username`
        """
        if username in self.clients_port1.keys():
            del self.clients_port1[username]
        if username in self.clients_port2.keys():
            del self.clients_port2[username]
        if conn in self.active_connections:
            self.active_connections.remove(conn)

    def communicate_with_client(self, conn: socket, addr: tuple):
        """ Method to communicate with connected client. It receives messages
            from client and matches known received commands with appropriate 
            methods
        """
        while True:
            try:
                message = receive_msg(conn, BUF_SIZE).split()
                command = message[0]
                params = message[1:] if len(message)>1 else []
                params.extend([conn, addr])
                match command:
                    case "CONNECT":
                        self.accept_connection(*params)
                    case "DISCONNECT":
                        self.accept_disconnection(*params)
                        break
                    case "LU":
                        self.list_users(*params)
                    case "LF":
                        self.list_files(*params)
                    case "MESSAGE":
                        self.deliver_message(*params)
                    case "READ":
                        with self.rfile_lock:
                            self.read_file(*params)
                    case "WRITE":
                        with self.wfile_lock:
                            self.write_file(*params)
                    case "OVERWRITE":
                        with self.wfile_lock:
                            self.overwrite_file(*params)
                    case "OVERREAD":
                        with self.rfile_lock:
                            self.overread_file(*params)
                    case "APPEND":
                        with self.wfile_lock:
                            self.append_file(*params)
                    case "APPENDFILE":
                        with self.wfile_lock:
                            self.appendfile_file(*params)
            except ConnectionResetError as exc:
                username = self.find_username_from_socket(conn)
                self.delete_client_data(username, conn)
                logging.error(exc.strerror)
                break
            except Exception as exc:
                logging.error(f"{exc}")
                break
    
    def accept_connection(self, username: str, conn: socket, addr: tuple):
        """ Accept connection from a client. Save this client as currently 
            connected and send message
        """
        if conn in self.active_connections:
            message = "Error: Attemp to establish a connection even if it's \
                already established!"
        elif username not in self.clients_port1.keys():
            self.clients_port1[username] = (conn, addr)
            self.active_connections.append(conn)
            message = OK
            logging.info(f"{username} successfully connected")
        elif username in self.clients_port1.keys():
            message = "Error: User with given username already exists!"
        send_msg_through_socket(conn, message)
        if message == OK:
            self.accept_connection_to_port2(username)
        logging.info(f"User {username} is fully connected")

    def accept_disconnection(self, conn: socket, addr: tuple):
        """ If client sends `disconnect` command, close connection with that 
            client.
        """
        if conn in self.active_connections:
            username = self.find_username_from_socket(conn)
            self.delete_client_data(username, conn)
            message = f"Server closed connection with {username} successfully!"
            logging.info(message)
            send_msg_through_socket(conn, OK)
            conn.shutdown(SHUT_RD)
            conn.close()
        else:
            message = "Error: Trying to disconnect before establishing a \
                connection"
            send_msg_through_socket(conn, message)
    
    def list_users(self, conn: socket, addr: tuple):
        """ Send the requested client the list of currently connected users
        """
        message = ""
        if conn in self.active_connections:
            for client in self.clients_port1.keys():
                message += client + " "
        else:
            message = "Error: Trying to access list of users before \
                establishing a connection"
        send_msg_through_socket(conn, message)

    def list_files(self, conn: socket, addr: tuple):
        """ Send the requested client the list of files in server's directory
        """
        if conn in self.active_connections:
            directory_items = os.listdir(os.path.join(os.getcwd(), "server"))
            directory_items = [item for item in directory_items 
                                    if not item.startswith("__")]
            message = " ".join(directory_items)
        else:
            message = "Error: Trying to access list of users before \
                establishing a connection"
        send_msg_through_socket(conn, message)

    def deliver_message(self, username: str, conn: socket, addr: tuple):
        """ Send the sender client's message to receiver client with username =
            `username`
        """
        message = receive_whole_data(conn, BUF_SIZE)
        sender_conn: socket = conn
        receiver_username = username
        # If both sender and receiver are online #
        if sender_conn in self.active_connections and receiver_username in \
            self.clients_port2.keys():
            receiver_conn: socket = self.clients_port2[receiver_username][0]
            sender_username = self.find_username_from_socket(conn)
            # Don't let the sender to send a message to itself #
            if sender_username == receiver_username:
                error_msg = "Error: Sending message to yourself is prohibited."
                send_msg_through_socket(sender_conn, error_msg)
                return None
            try:
                send_msg_through_socket(receiver_conn, MESSAGE)
                msg4receiver = f"{len(message)} {message}"
                send_msg_through_socket(receiver_conn, msg4receiver)
            except Exception as exc:
                error_msg = f"Error: Lost connection with {receiver_username}"
                send_msg_through_socket(sender_conn, error_msg)
                self.delete_client_data(receiver_username, receiver_conn)
                logging.error(error_msg)
            else:
                send_msg_through_socket(sender_conn, OK)
        # If the receiver is not online, send appropriate message to sender #
        elif sender_conn in self.active_connections and receiver_username not \
            in self.clients_port2.keys():
            error_msg = f"Error: {receiver_username} is not online"
            send_msg_through_socket(sender_conn, error_msg)
        # In some weird conditions, this may happen #
        elif sender_conn not in self.active_connections:
            error_msg = "Error: Trying to send the message to another user, \
                before establishing a connection with server"
            send_msg_through_socket(sender_conn, error_msg)

    def accept_connection_to_port2(self, username: str) -> bool:
        """ Accepts a connection request to `PORT2`, which was sent to \
            `self.redirect_socket`
        """
        try:
            # Blocked until client sends connect() #
            logging.info("Trying to accept a connection to port 2")
            client_conn, client_addr = self.redirect_socket.accept()
            logging.debug("Accepted connection request to port 2")
            self.clients_port2[username] = (client_conn, client_addr)
        except Exception as exc:
            logging.debug(exc)
    
    def read_file(self, file_name: str, conn: socket, addr: tuple):
        """ Reads a file `file_name`. Send OK message if `file_name` is in 
            server. Otherwise, appropriate error is sent to the client which 
            requested
        """
        # Get the file names of server's directory #
        directory_items = os.listdir(os.path.join(os.getcwd(), "server"))
        directory_items = [item for item in directory_items 
                                if not item.startswith("__")]
        # Send appropriate msg to client depending on existance of requested 
        # file #
        if file_name not in directory_items:
            msg = f"Error: {file_name} is not found in server"
            send_msg_through_socket(conn, msg)
            return None
        else:
            msg = OK
            send_msg_through_socket(conn, msg)
        # Send the file using the protocol #
        try:
            with open(os.path.join("server", file_name), "r") as f:
                file_data = f.read()
                file_size = len(file_data)
            send_msg_through_socket(conn, f"{file_size} {file_data}")
        except UnicodeDecodeError:
            file_type = file_name.split(".")[-1]
            error_msg = f"Error: Requested {file_type} file cannot be delivered"
            send_msg_through_socket(conn, error_msg)
        except Exception as exc:
            send_msg_through_socket(conn, exc.__str__())
    
    def receive_and_save_file(self, file_name: str, client_sock: socket):
        """ Receives the file content from client and saves that file content to
            server.
        """
        try:
            file_content = receive_whole_data(client_sock, BUF_SIZE)
            with open(os.path.join("server", file_name), "w") as f:
                f.write(file_content)
        except Exception as exc:
            send_msg_through_socket(client_sock, f"Error: {exc.__str__()}")
        else:
            send_msg_through_socket(client_sock, OK)
        
    def write_file(self, file_name: str, conn: socket, addr: tuple):
        """ Writes a new file `file_name`. First checks whether no file with 
            name `file_name` exists in server, then receives the content of file
        """
        directory_items = os.listdir(os.path.join(os.getcwd(), "server"))
        directory_items = [item for item in directory_items 
                                if not item.startswith("__")]
        if file_name in directory_items:
            msg = f"Error: File with name {file_name} is already in server"
            send_msg_through_socket(conn, msg)
            return None
        else:
            send_msg_through_socket(conn, OK)
        self.receive_and_save_file(file_name, conn)

    def overwrite_file(self, file_name: str, conn: socket, addr: tuple):
        """ Overwrites the `file_name`
        """
        directory_items = os.listdir(os.path.join(os.getcwd(), "server"))
        directory_items = [item for item in directory_items 
                                if not item.startswith("__")]
        if file_name in directory_items and file_name.endswith(".py"):
            m = "Error: The requested file cannot be modified"
            send_msg_through_socket(conn, m)
            return None
        else:
            send_msg_through_socket(conn, OK)
        self.receive_and_save_file(file_name, conn)
    
    def append_file(self, file_name: str, conn: socket, addr: tuple):
        """ Appends `new_content` to a `file_name`.
        """
        directory_items = os.listdir(os.path.join(os.getcwd(), "server"))
        directory_items = [item for item in directory_items 
                                if not item.startswith("__")]
        if file_name not in directory_items:
            error_msg = f"Error: The file {file_name} is not in server"       
            send_msg_through_socket(conn, error_msg)
        elif file_name.endswith(".py"):
            error_msg = f"Error: {file_name} cannot be modified"
            send_msg_through_socket(conn, error_msg)
        else:
            send_msg_through_socket(conn, OK)
            new_content = receive_whole_data(conn, BUF_SIZE)
            try:
                with open(os.path.join("server", file_name), "a") as f:
                    f.write(f"{new_content}\n")
            except Exception as exc:
                error_msg = f"Error: {exc}"
                send_msg_through_socket(conn, error_msg)
            else:
                send_msg_through_socket(conn, OK)

    def overread_file(self, file_name: str, conn: socket, addr: tuple):
        """ When the client requests to get server's `file_name`, server sends
            this file if file exists.
        """
        self.read_file(file_name, conn, addr)
    
    def appendfile_file(self, client_fname: str, server_fname: str, 
        conn: socket, addr: tuple):
        """ Take the contents of `client_fname` and append it to server's 
            `server_fname`
        """
        directory_items = os.listdir(os.path.join(os.getcwd(), "server"))
        directory_items = [item for item in directory_items 
                                if not item.startswith("__")]
        if server_fname not in directory_items:
            err_m = f"Error: The requested file {server_fname} is not in server"
            send_msg_through_socket(conn, err_m)
        elif server_fname.endswith(".py"):
            error_msg = f"Error: {server_fname} cannot be modified"
            send_msg_through_socket(conn, error_msg)
        else:
            send_msg_through_socket(conn, OK)
            client_fcontent = receive_whole_data(conn, BUF_SIZE)
            try:
                with open(os.path.join("server", server_fname), "a") as f:
                    f.write(client_fcontent)
            except Exception as exc:
                error_msg = f"Error: {exc}"
                send_msg_through_socket(conn, error_msg)
            else:
                send_msg_through_socket(conn, OK)

    def start(self):
        """ Starts the server. Server's main job: always waiting connection
            request at `PORT1`
        """
        try:
            while True:
                logging.info("Waiting for a new connection...")
                conn, addr = self.com_socket.accept()
                logging.debug(addr)
                t = Thread(target=self.communicate_with_client, args=[conn, addr])
                t.start()
        except KeyboardInterrupt:
            logging.info("Server is shutting down...")
        except Exception as exc:
            logging.error(f"{exc}")
        finally:
            self.disconnect_clients()
            self.com_socket.close()
