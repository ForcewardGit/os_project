""" This module must be runned to start a server.

    Used custom modules
    -------------------
    server

    Functions
    ---------
    main()
        Creates a Server object and runs it
"""

from .server import Server


def main(): 
    """ Creates a Server object and runs it.
    """
    s = Server()
    s.start()


if __name__ == "__main__":
    main()
