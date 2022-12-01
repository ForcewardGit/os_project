""" Module that defines all the logic of the server.
"""

from socket import socket, AF_INET, SOCK_STREAM
import logging


# Format log messages #
logging.basicConfig(level=logging.INFO)

# Global Variables #
SELF_IP = "127.0.0.1"
SELF_PORT = 2021
BUF_SIZE = 1024


class Server:
    """ The Server class which implements the logic of Server which can serve
        only 1 client at a time.
    """
    def __init__(self, ip=SELF_IP, port=SELF_PORT):
        self.ip = ip                            # IP address of server
        self.port = port                        # Port, at which server will wait
        self.socket = self.configure_socket()   # Socket object
        self.clients = {}                       # Dictionary which contains username: his connection info key-value pairs
        self.active_connections = []            # List of client connections who are currently connected to this server

    def configure_socket(self):
        """ Create and return socket object. If some error occurred, this 
            method returns None
        """
        try:
            s = socket(AF_INET, SOCK_STREAM)
            s.bind((self.ip, self.port))
            s.listen()
            return s
        except Exception as exc:
            logging.error(exc)
            return None
        
    def communicate_with_client(self, conn: socket, addr: tuple):
        """ Method to communicate with connected client. It receives messages
            from client and matches known received commands with appropriate 
            methods
        """
        while True:
            message = conn.recv(BUF_SIZE).decode().split()
            command = message[0]
            params = message[1:] if len(message)>1 else []
            params.extend([conn, addr])
            match command:
                case "connect":
                    self.accept_connection(*params)
                    logging.info(f"{params[0]} successfully connected")
                case "disconnect":
                    self.accept_disconnection(*params)
                    break
                case "lu":
                    self.list_users(*params)
                case "lf":
                    self.list_files(*params)
    
    def accept_connection(self, username: str, self_ip: str, conn: socket, \
        addr: tuple):
        """ Accept connection from a client. Save this client as currently 
            connected and send message
        """
        if conn in self.active_connections:
            message = "Error: Attemp to establish a connection even if it's \
                already established!"
            # conn.send(message.encode())
        elif username not in self.clients.keys():
            self.clients[username] = (conn, addr)
            self.active_connections.append(conn)
            message = "OK"
        elif username in self.clients.keys():
            message = "Error: User with given username already exists!"
        conn.send(message.encode())

    def accept_disconnection(self, conn: socket, addr: tuple):
        """ If client sends `disconnect` command, close connection with that client.
        """
        if conn in self.active_connections:
            conn_username = ""
            # find a username of conn's client
            for username, (connection, _) in self.clients.items():
                if connection == conn:
                    conn_username = username
            del self.clients[conn_username]
            self.active_connections.remove(conn)
            message = f"Server closed connection with {conn_username} successfully!"
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
            for client in self.clients.keys():
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
            directory_items = os.listdir()
            directory_items = [item for item in directory_items if not item.startswith("__")]
            message = " ".join(directory_items)
        else:
            message = "Error: Trying to access list of users before \
                establishing a connection"
        conn.send(message.encode())

    def start(self):
        """ Server's main job - always waiting connection request at `SELF_PORT`.
        """
        try:
            while True:
                logging.info("Waiting for a new connection...")
                conn, addr = self.socket.accept()
                self.communicate_with_client(conn, addr)
        except Exception as exc:
            logging.error(f"{exc} hereeeee")
        finally:
            self.socket.close()