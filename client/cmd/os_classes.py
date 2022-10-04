""" The definitions of different OS classes with commands being their
    methods.
"""

import os

class OS:
    """ The base class which defines methods that are general to all
        OS types. ['general' - in terms of the logic, not the name]
    """

    def __init__(self, name) -> None:
        self.name = name
        
    def listdir(self):
        """ Method which lists the contents of the current directory
            Windows: `dir`
            Linux: `ls`
            MacOS: `ls`
        """
        dir_contents = os.listdir()
        for item in dir_contents:
            if os.path.isdir(item):
                print(f"{item} --- directory")
            else:
                print(f"{item} --- file")
    
    def current_path(self):
        """ Prints the complete path of the current working directory
            Windows: `chdir`
            Linux: `pwd`
            MacOS: `pwd`
        """
        print(os.getcwd())
    
    def change_dir(self, target_path):
        """ Changes the directory to a specified target path
            Windows: `cd`
            Linux: `cd`
            MacOS: `cd`
        """
        try:
            os.chdir(target_path)
        except Exception as e:
            print(f"{e}")


class Windows(OS):
    """ Methods of commands that correspond to only Windows
    """
    pass

class Linux(OS):
    """ Methods of commands that correspond to only Linux
    """
    pass

class MacOS(OS):
    """ Methods of commands that correspond to only MacOS
    """
    pass
