""" The definitions of functions which handle CMD app logic for
    different OS.
    They all handle some basic OS commands.
"""


from .os_classes import Linux, Windows, MacOS


def windows_cmd():
    """ The CMD app for Windows
    """
    operating_system = Windows(name = "Windows")

    while True:
        command = input("$ ")
        command = command.split()       # split in order to
            # distinguish between cmd function and its arguments
        command_function = command[0]

        match command_function:
            case "dir":
                operating_system.listdir()
            case "chdir":
                operating_system.current_path()
            case "cd":
                if len(command) > 0:
                    operating_system.change_dir(command[1])
                else:
                    print("Please specify the target!")
            case "exit":
                print("Command-line mode has finished...")
                break
            case _:
                print("Unsupported command!")
                   


def linux_cmd():
    """ The CMD app for Linux.
    """
    operating_system = Linux(name = "Linux")
    while True:
        command = input("$ ")
        command = command.split()
        command_function = command[0]

        match command_function:
            case "ls":
                operating_system.listdir()
            case "pwd":
                operating_system.current_path()
            case "cd":
                if len(command) > 0:
                    operating_system.change_dir(command[1])
                else:
                    print("Please specify the target!")
            case "exit":
                print("Command-line mode has finished...")
                break
            case _:
                print("Unsupported command!")


def macos_cmd():
    """ The CMD app for MacOS.
    """
    linux_cmd()