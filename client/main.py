""" This module must be runned to start a client

    Used custom modules
    -------------------
    client

    Defined function
    ----------------
    main()
        Creates a client and starts it
"""

from .client import Client


def main():
    """ Creates a client and starts it.
    """
    client = Client()
    client.ask_command()


if __name__ == "__main__":
    main()