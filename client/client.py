""" Module that defines all the logic of the client.
"""

from cmd_handlers import connect_cmd, disconnect_cmd, lu_cmd, lf_cmd
import logging


# Format log messages #
logging.basicConfig(level=logging.INFO)

# Global Variables #
SERVER_IP = "localhost"
PORT = 2021
BUF_SIZE = 100
available_commands_apps = ["connect", "disconnect", "lu", "lf"]  # list of available commands that can be handled by client


class Client:
    """ Client class which implements the logic of client objects.
    """
    def __init__(self) -> None:
        """ Initialization of client object
        """
        self.username = None    # the username of client
        self.connected = False  # True when the client is connected to server
        self.socket = None      # socket object to communicate with server
    
    def ask_command(self):
        """ Method which is runned automatically when the client object is 
            created. Always asks the user for input, matches it with appropriate
            methods.
        """
        while True:
            try:
                user_input = input("Enter a command: ")
                user_input = user_input.split()
                command = user_input[0].lower()
                params = user_input[1:] if len(user_input)>1 else []
                match command:
                    case "connect":
                        self.connect(*params)
                    case "disconnect":
                        self.disconnect(*params)
                    case "lu":
                        self.lu(*params)
                    case "send":
                        self.send(*params)
                    case "lf":
                        self.lf(*params)
                    case "quit":
                        # Disconnect from server and finish the client program
                        self.disconnect(*params)
                        break
                    case _:
                        logging.warning(f"Command {command} not found")
            except Exception as exc:
                logging.error(f"{exc} ask_command")
                continue
    
    def connect(self, username: str, ip: str):
        """ Connect to the server with given `ip` and `port`.
        """
        SERVER_IP = ip
        port = PORT

        if not self.connected:
            self.socket = connect_cmd(port, ip)
            if self.socket:
                self.socket.send(f"connect {username} {ip}".encode())
                message = self.socket.recv(BUF_SIZE).decode()
                if message == "OK":
                    self.connected = True if self.socket else False
                    logging.info(f"Successfully connected to server with ip={ip}")
                else:
                    logging.error(message)
        elif self.connected:
            logging.error("Warning: Already connected")

    def disconnect(self):
        """ Disconnect from the server, to which our client is currently
            connected.
        """
        if self.connected:
            disconnect_cmd(self.socket)
            message = self.socket.recv(BUF_SIZE).decode()
            if message.startswith("Error"):
                logging.error(message.removeprefix("Error: "))
                return None
            self.connected = False
            logging.info(message)
            self.socket.close()
        else:
            logging.warning("There was no connection")

    def lu(self):
        """ Print all the users which are currently connected to the server,
            to which our client is also connected
        """
        if self.connected:
            try:
                lu_cmd(self.socket)
                server_response = self.socket.recv(BUF_SIZE).decode()
                logging.info(server_response)
            except Exception as exc:
                logging.error(exc)
        else:
            logging.warning("There was no connection")

    def send(self, username: str):
        """ Send a message to another user with username = `username`
        """
        # To be implemented in the next submissions
        pass

    def lf(self):
        """ List all the files of our server's folder.
        """
        if self.connected:
            lf_cmd(self.socket)
            server_response = self.socket.recv(BUF_SIZE).decode()
            logging.info(server_response)
        else:
            logging.warning("There was no connection")
