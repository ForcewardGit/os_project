""" Client application's main part. This file should be runned to start a server
"""

from .client import Client


def main():
    client = Client()
    client.ask_command()


if __name__ == "__main__":
    main()