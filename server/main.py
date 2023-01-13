""" Server's main application part. This file should be runned to start a server
"""

from .server import Server


def main():
    s = Server()
    s.start()


if __name__ == "__main__":
    main()
    