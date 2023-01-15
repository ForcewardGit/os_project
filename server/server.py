""" The module defines the logic of a TCP server in a class Server.

    This module is not intended to be runned!

    Used built-in modules
    ----------------------
    os, logging, threading, socket

    Used custom modules
    --------------------
    protocol, utils

    Classes
    -------
    Class Server:
        A multithreaded TCP server, which serves its clients according
        to protocols defined in `protocol.py` module.
"""

import os
import logging
from threading import Thread, Lock
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RD

from protocol import MESSAGE
from utils import send_msg_through_socket, receive_whole_data, receive_msg

# Configure log messages #
log_format = "%(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=log_format)

# Global Variables #
SELF_IP = "127.0.0.1"   # IP address of server, by default it is 127.0.0.1
PORT1 = 2021            # Port at which server waits clients and interacts with them
PORT2 = 2022            # Port to which server sends messages whenever accepts them in `send` command
BUF_SIZE = 4096         # Buffer size for receiving items
OK = "OK"               


class Server:
    """ A multithreaded TCP server, which serves its clients according 
        to protocols defined in `protocol.py` module.

        In order to run the server, `start()` method needs to be called

        Attributes:
        -----------
        ip : str
            IP address of the server (default is localhost)
        port1 : int
            The port used to receive commands sent by client 
            (default is 2021)
        port2 : int
            The port used to deliver msg when MESSAGE command is 
            received (default is 2022)
        clients_port1 : dict[str, (tuple, socket)]
            The dictionary of clients' usernames, who are connected to 
            server's `port1` and their connection info
        clients_port2 : dict[str, (tuple, socket)]
            The dictionary of clients' usernames, who are connected to 
            server's `port2` and their connection info
        active_connections: list[socket]
            list of all sockets of users, who are currently connected
            to server
        com_socket : socket
            The socket used to communicate with client in port1
        redirect_socket : socket
            The socket used to communicate with client in port2
        file_lock : Lock
            The lock that is used to prevent race conditions while
            performing fileoperations

        Methods:
        --------
        __init__(self, ip=`SELF_IP`, port1=`PORT1`, port2=`PORT2`)
            Initialization of object attributes

        configure_sockets(self)
            Create and return socket objects

        disconnect_clients(self):
            Disconnects all currently connected clients from server

        find_username_from_socket(self, s: socket)
            Find a username of the client, to which `s` is related

        delete_client_data(self, username: str, conn: socket)
            Removes all data from class attributes related to client

        communicate_with_client(self, conn: socket, addr: tuple)
            Communicates with connected client, receives messages
            from client and matches known received commands with 
            appropriate methods

        accept_disconnection(self, conn: socket, addr: tuple)
            Closes connection with client and send appropriate msg

        list_users(self, conn: socket, addr: tuple)
            Sends to client all currently connected clients' usernames

        list_files(self, conn: socket, addr: tuple)
            Sends to client all files in server's directory

        deliver_message(self, username: str, conn: socket, addr: tuple)
            Get the sender's message and deliver it to the receiver 
            client with username=`username`

        accept_connection_to_port2(self, username: str)
            Accepts a connection request to `PORT2`

        read_file(self, file_name: str, conn: socket, addr: tuple)
            Transfers file `file_name` according to protocol

        receive_and_save_file(self, file_name: str, client_sock: socket)
            Receives the file content from client and saves that file 
            content to server
        
        write_file(self, file_name: str, conn: socket, addr: tuple)
            Writes a new file `file_name`
        
        overwrite_file(self, file_name: str, conn: socket, addr: tuple)
            verwrites the `file_name`
        
        append_file(self, file_name: str, conn: socket, addr: tuple)
            Receives new content from the clien and appends that to
            `file_name`
        
        overread_file(self, file_name: str, conn: socket, addr: tuple)
            Transfers the `file_name` content to client according to
            OVERREAD protocol
        
        appendfile_file(self, client_fname: str, server_fname: str, 
            conn: socket, addr: tuple)
            Receives the content of `client_fname` and appends it to 
            server's `server_fname`.
        
        start(self)
            Starts the tcp server
    """
    def __init__(self, ip=SELF_IP, port1=PORT1, port2=PORT2):
        """ Initialization of object attributes

            Parameters:
            -----------
            ip : str, optional
                IP address of the server (default is localhost)
            port1 : int, optional
                The port used to receive commands sent by client 
                (default is 2021)
            port2 : int. optional
                The port used to deliver msg when MESSAGE command is 
                received (default is 2022
        """
        self.ip = ip
        self.port1 = port1
        self.port2 = port2
        self.clients_port1: dict[str, (tuple, socket)] = {}
        self.clients_port2: dict[str, (tuple, socket)] = {}
        self.active_connections: list[socket] = []
        self.com_socket, self.redirect_socket = self.configure_sockets()
        self.file_lock = Lock()

    def configure_sockets(self) -> tuple[socket, socket] | tuple[None, None]:
        """ Create and return socket objects. 

            Returns
            -------
            None
                If some error occurred
            tuple[socket, socket]
                the first socket is the socket that listens on port1,
                the second is the one listening on port2
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
        
    def disconnect_clients(self) -> None:
        """ Disconnects all currently connected clients from server.

            Returns
            -------
            None
        """
        for client in self.active_connections:
            client.close()

    def find_username_from_socket(self, s: socket) -> str:
        """ Find a username of the client, to which `s` is related

            Method assumes that the given socket `s` is connected to 
            one of server's ports.

            Parameters
            ----------
            s : socket
                socket object of one of connected client to server
            
            Returns
            -------
            str
                The username of `s` socket object
        """
        for username, (connection, _) in self.clients_port1.items():
            if connection == s:
                conn_username = username
                return conn_username
        for username, (connection, _) in self.clients_port2.items():
            if connection == s:
                conn_username = username
                return conn_username

    def delete_client_data(self, username: str, conn: socket) -> None:
        """ Removes all data from class attributes related to client

            Parameters
            ----------
            username : str
                The username of a client connected to server
            conn : socket
                The socket object of a client connected to server

            Returns
            -------
            None
        """
        if username in self.clients_port1.keys():
            del self.clients_port1[username]
        if username in self.clients_port2.keys():
            del self.clients_port2[username]
        if conn in self.active_connections:
            self.active_connections.remove(conn)

    def communicate_with_client(self, conn: socket, addr: tuple) -> None:
        """ Communicates with connected client, receives messages
            from client and matches known received commands with 
            appropriate methods.

            Parameters
            ----------
            conn : socket
                The socket object of client which sent connection 
                request to server
            addr : tuple
                Contains client's ip and port
            
            Finishes when the client has disconnected or when server 
            lost connection with client
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
                        with self.file_lock:
                            self.read_file(*params)
                    case "WRITE":
                        with self.file_lock:
                            self.write_file(*params)
                    case "OVERWRITE":
                        with self.file_lock:
                            self.overwrite_file(*params)
                    case "OVERREAD":
                        with self.file_lock:
                            self.overread_file(*params)
                    case "APPEND":
                        with self.file_lock:
                            self.append_file(*params)
                    case "APPENDFILE":
                        with self.file_lock:
                            self.appendfile_file(*params)
            except ConnectionResetError as exc:
                username = self.find_username_from_socket(conn)
                self.delete_client_data(username, conn)
                logging.error(exc.strerror)
                break
            except IndexError:
                break
            except Exception as exc:
                logging.error(f"{exc}")
                break
    
    def accept_connection(self, username: str, conn: socket, addr: tuple):
        """ Connect a client to server

            Parameters
            ----------
            username : str
                The username of a client
            conn : socket
                The socket object ofa  client
            addr : tuple
                Contains client's ip and port

            Returns
            -------
            None
        """
        message = str()
        if conn in self.active_connections:
            message = "Error: Attemp to establish a connection even if it's \
                already established!"
        elif username not in self.clients_port1.keys():
            self.clients_port1[username] = (conn, addr)
            self.active_connections.append(conn)
            message = OK
            logging.debug(f"Accepted connection to port 1")
        elif username in self.clients_port1.keys():
            message = "Error: User with given username already exists!"
        send_msg_through_socket(conn, message)
        if message == OK:
            self.accept_connection_to_port2(username)
            logging.info(f"User {username} is fully connected")

    def accept_disconnection(self, conn: socket, addr: tuple):
        """ Closes connection with client and send appropriate msg.

            Parameters
            ----------
            conn : socket
                The socket object of a client
            addr : tuple
                Contains client's ip and port

            Returns
            -------
            None
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
        """ Sends to client all currently connected clients' usernames

            Parameters
            ----------
            conn : socket
                The socket object of a client
            addr : tuple
                Contains client's ip and port

            Returns
            -------
            None
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
        """ Sends to client all files in server's directory

            Parameters
            ----------
            conn : socket
                The socket object of a client
            addr : tuple
                Contains client's ip and port

            Returns
            -------
            None
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
        """ Get the sender's message and deliver it to the receiver 
            client with username=`username`

            Parameters
            ----------
            username: str
                The username of a receiver client
            conn : socket
                The socket object of a sender client
            addr : tuple
                Contains sender client's ip and port
            
            Returns
            -------
            None
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
        """ Accepts a connection request to `PORT2`, which was sent to
            `self.redirect_socket`

            Parameters
            ----------
            username : str
                The username of a client who needs to send conn request
            
            Returns
            -------
            None
        """
        try:
            # Blocked until client sends connect() #
            logging.debug("Trying to accept a connection to port 2")
            client_conn, client_addr = self.redirect_socket.accept()
            logging.debug("Accepted connection request to port 2")
            self.clients_port2[username] = (client_conn, client_addr)
        except Exception as exc:
            logging.debug(exc)
    
    def read_file(self, file_name: str, conn: socket, addr: tuple) -> None:
        """ Transfers file `file_name` according to protocol.

            Parameters
            ----------
            file_name : str
                The name of the requested file
            conn : socket
                The socket object of a client
            addr : tuple
                Contains client's ip and port
            
            Returns
            -------
            None
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
        """ Receives the file content from client and saves that file 
            content to server.

            Parameters
            ----------
            file_name : str
                The name of the requested file
            client_conn : socket
                The socket object of the client
            
            Returns
            -------
            None
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
        """ Writes a new file `file_name`.

            First checks whether no file with name `file_name` exists 
            in server, then receives the file content

            Parameters
            ----------
            file_name : str
                The name of the requested file
            conn : socket
                The socket object of a client
            addr : tuple
                Contains client's ip and port
            
            Returns
            -------
            None

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

            Parameters
            ----------
            file_name : str
                The name of the requested file
            conn : socket
                The socket object of a client
            addr : tuple
                Contains client's ip and port
            
            Returns
            -------
            None
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
        """ Receives new content from the clien and appends that to
            `file_name`

            Parameters
            ----------
            file_name : str
                The name of the requested file
            conn : socket
                The socket object of a client
            addr : tuple
                Contains client's ip and port
            
            Returns
            -------
            None
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
        """ Transfers the `file_name` content to client according to
            OVERREAD protocol.

            Parameters
            ----------
            file_name : str
                The name of the requested file
            conn : socket
                The socket object of a client
            addr : tuple
                Contains client's ip and port
            
            Returns
            -------
            None
        """
        self.read_file(file_name, conn, addr)
    
    def appendfile_file(self, client_fname: str, server_fname: str, 
        conn: socket, addr: tuple):
        """ Receives the content of `client_fname` and appends it to 
            server's `server_fname`.

            Parameters
            ----------
            client_fname : str
                The client's filename, the content of which is going to 
                be appended to server's `server_fname`
            server_fname : str
                The server file which is going to be modified
            
            Returns
            -------
            None
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
        """ Starts the tcp server.

            Server's main job: always waiting connection request at 
            `PORT1`
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
