""" Module that defines all the logic of the server.
"""

from socket import socket, AF_INET, SOCK_STREAM
import logging
from threading import Thread, Lock


# Format log messages #
log_format = "%(levelname)s: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=log_format)

# Global Variables #
SELF_IP = "127.0.0.1"   # IP address of server
PORT1 = 2021            # Port at which server waits clients and interacts with them
PORT2 = 2022            # Port to which server sends messages whenever accepts them in `send` command
BUF_SIZE = 1024         # Buffer size of receiving items


class Server:
    """ The Server class which implements the logic of Server which can serve
        only 1 client at a time
    """
    def __init__(self, ip=SELF_IP, port1=PORT1, port2=PORT2):
        self.ip = ip
        self.port1 = port1
        self.port2 = port2
        self.clients_port1 = {}       # Dictionary which contains username: his connection info key-value pairs for port 1
        self.clients_port2 = {}       # Dictionary which contains username: his connection info key-value pairs for port 2
        self.active_connections = []  # List of client connections who are currently connected to this server
        self.com_socket, self.redirect_socket = self.configure_sockets()
        self.lock = Lock()

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
                message = conn.recv(BUF_SIZE).decode().split(" ", 2)
                command = message[0]
                params = message[1:] if len(message)>1 else []
                params.extend([conn, addr])
                match command:
                    case "connect":
                        self.accept_connection(*params)
                    case "disconnect":
                        self.accept_disconnection(*params)
                        break
                    case "lu":
                        self.list_users(*params)
                    case "lf":
                        self.list_files(*params)
                    case "send":
                        self.deliver_message(*params)
            except ConnectionResetError as exc:
                username = self.find_username_from_socket(conn)
                self.delete_client_data(username, conn)
                logging.error(exc.strerror)
                break
            except Exception as exc:
                logging.error(f"{exc}")
                break
    
    def accept_connection(self, username: str, self_ip: str, conn: socket, \
        addr: tuple):
        """ Accept connection from a client. Save this client as currently 
            connected and send message
        """
        if conn in self.active_connections:
            message = "Error: Attemp to establish a connection even if it's \
                already established!"
        elif username not in self.clients_port1.keys():
            self.clients_port1[username] = (conn, addr)
            self.active_connections.append(conn)
            message = "OK"
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
            conn.send(message.encode())
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
        import os

        if conn in self.active_connections:
            directory_items = os.listdir(os.path.join(os.getcwd(), "server"))
            directory_items = [item for item in directory_items 
                                    if not item.startswith("__")]
            message = " ".join(directory_items)
        else:
            message = "Error: Trying to access list of users before \
                establishing a connection"
        conn.send(message.encode())

    def deliver_message(self, username: str, message: str, conn: socket, \
        addr: tuple):
        """ Send the sender client's message to receiver client with username =
            `username`
        """
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
            msg4receiver = f"{sender_username} {message}"
            try:
                logging.debug(self.find_username_from_socket(receiver_conn))
                receiver_conn.send(msg4receiver.encode())
            except Exception as exc:
                error_msg = f"Error: Lost connection with {receiver_username}"
                sender_conn.send(error_msg.encode())
                self.delete_client_data(receiver_username, receiver_conn)
                logging.error(error_msg)
            else:
                sender_conn.send("OK".encode())
        # If the receiver is not online, send appropriate message to sender #
        elif sender_conn in self.active_connections and receiver_username not \
            in self.clients_port2.keys():
            error_msg = f"Error: {receiver_username} is not online"
            sender_conn.send(error_msg.encode())
        # In some weird conditions, this may happen #
        elif sender_conn not in self.active_connections:
            error_msg = "Error: Trying to send the message to another user, before \
                establishing a connection with server"
            sender_conn.send(error_msg.encode())

    def accept_connection_to_port2(self, username: str) -> bool:
        """ Accepts a connection request from a queue of requests. Method's aim
            is to find the right connection request of the user with given 
            username.
        """
        try:
            # Blocked until client sends connect() #
            client_conn, client_addr = self.redirect_socket.accept()
            logging.debug("Accepted connection request to port 2")
            self.clients_port2[username] = (client_conn, client_addr)
        except Exception as exc:
            logging.debug(exc)

    def start(self):
        """ Server's main job: always waiting connection request at `PORT1`.
        """
        try:
            while True:
                logging.info("Waiting for a new connection...")
                conn, addr = self.com_socket.accept()
                logging.debug(addr)
                t = Thread(target=self.communicate_with_client, args=[conn, addr])
                t.start()
        except Exception as exc:
            logging.error(f"{exc}")
        finally:
            self.com_socket.close()
