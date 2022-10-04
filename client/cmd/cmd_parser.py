""" The CMD application that has several OS options to be selected.
    For now - Linux, Windows and MacOS commands are available.
"""

from .os_cmds import linux_cmd, windows_cmd, macos_cmd

def cmdapp():
    """ Function which defines the starting point of a CMD app. Calls
        appropriate CMD subapps once selected by the user.
    """
    os_options = ["linux", "windows", "macos"]
    for i, option in zip(range(len(os_options)), os_options):
        print(f"{i}: {option}")

    os_type = input("Choose one of the OS options[0-2]: ")

    match os_type:
        case "0":
            linux_cmd()
        case "1":
            windows_cmd()
        case "2":
            macos_cmd()
        case _:
            linux_cmd()
