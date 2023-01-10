""" Module that defines all the logic of the server.
"""

import os
from socket import socket, AF_INET, SOCK_STREAM
import logging
from threading import Thread, Lock
from .protocol import CONNECT, LU, LF, MESSAGE, READ
from utils import send_msg_through_socket, receive_whole_data, receive_msg

# Format log messages #
log_format = "%(levelname)s: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=log_format)

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
                message = receive_msg(conn, BUF_SIZE).split(" ", 1)
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
                        self.read_file(*params)
                    case "WRITE":
                        self.write_file(*params)
                    case "OVERWRITE":
                        self.overwrite_file(*params)
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
        conn.send(message.encode())
        self.accept_connection_to_port2(username)

    def accept_disconnection(self, conn: socket, addr: tuple):
        """ If client sends `disconnect` command, close connection with that 
            client.
        """
        if conn in self.active_connections:
            username = self.find_username_from_socket(conn)
            self.delete_client_data(username, conn)
            message = f"Server closed connection with {username} successfully!"
            logging.info(message)
            conn.send(OK.encode())
            conn.close()
        else:
            message = "Error: Trying to disconnect before establishing a \
                connection"
            conn.send(message.encode())
    
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
        conn.send(message.encode())

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
        conn.send(message.encode())

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
                sender_conn.send(error_msg.encode())
                return None
            try:
                receiver_conn.send(MESSAGE.encode())
                msg4receiver = f"{len(message)} {message}"
                receiver_conn.send(msg4receiver.encode())
            except Exception as exc:
                error_msg = f"Error: Lost connection with {receiver_username}"
                sender_conn.send(error_msg.encode())
                self.delete_client_data(receiver_username, receiver_conn)
                logging.error(error_msg)
            else:
                sender_conn.send(OK.encode())
        # If the receiver is not online, send appropriate message to sender #
        elif sender_conn in self.active_connections and receiver_username not \
            in self.clients_port2.keys():
            error_msg = f"Error: {receiver_username} is not online"
            sender_conn.send(error_msg.encode())
        # In some weird conditions, this may happen #
        elif sender_conn not in self.active_connections:
            error_msg = "Error: Trying to send the message to another user, \
                before establishing a connection with server"
            sender_conn.send(error_msg.encode())

    def accept_connection_to_port2(self, username: str) -> bool:
        """ Accepts a connection request to `PORT2`, which was sent to \
            `self.redirect_socket`
        """
        try:
            # Blocked until client sends connect() #
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
            conn.send(msg.encode())
            return None
        else:
            msg = OK
            conn.send(msg.encode())
        # Send the file using the protocol #
        try:
            with open(os.path.join("server", file_name), "r") as f:
                file_data = f.read()
                file_size = len(file_data)
            conn.send(f"{file_size} {file_data}".encode())
        except UnicodeDecodeError:
            file_type = file_name.split(".")[-1]
            error_msg = f"Error: Requested {file_type} file cannot be delivered"
            conn.send(error_msg.encode())
        
    def write_file(self, file_name: str, conn: socket, addr: tuple):
        """ Writes a new file `file_name`. First checks whether no file with 
            name `file_name` exists in server, then receives the content of file
        """
        directory_items = os.listdir(os.path.join(os.getcwd(), "server"))
        directory_items = [item for item in directory_items 
                                if not item.startswith("__")]
        if file_name in directory_items:
            msg = f"Error: File with name {file_name} is already in server"
            conn.send(msg.encode())
            return None
        else:
            send_msg_through_socket(conn, OK)
        try:
            file_content = receive_whole_data(conn, BUF_SIZE)
            with open(os.path.join("server", file_name), "w") as f:
                f.write(file_content)
        except Exception as exc:
            send_msg_through_socket(conn, exc.__str__())
        else:
            send_msg_through_socket(conn, OK)

    def overwrite_file(self, file_name: str, conn: socket, addr: tuple):
        """ Overwrites the `file_name`
        """
        if file_name.endswith(".py"):
            m = "Error: The requested file cannot be modified"
            send_msg_through_socket(conn, m)
            return None
        else:
            send_msg_through_socket(conn, OK)
        try:
            file_content = receive_whole_data(conn, BUF_SIZE)
            with open(os.path.join("server", file_name), "w") as f:
                f.write(file_content)
        except Exception as exc:
            send_msg_through_socket(conn, f"Error: {exc.__str__()}")
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
