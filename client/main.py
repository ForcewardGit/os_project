""" Client application's main part.
"""

from client import Client


def main():
    client = Client()
    client.ask_command()


if __name__ == "__main__":
    main()