""" Module that defines a customer Formatter class used to format output
    logs in different colors.

    Defined class
    -------------
    CustomFormatter(logging.Formatter)
        Colored logs formatter class
"""

import logging

class CustomFormatter(logging.Formatter):
    """ Colored logs formatter class
        
        The class inherits all the logic of logging.Formatter class.

        Class attributes
        ----------------
        grey : str
            The ANSI representation of grey color
        blue : str
            The ANSI representation of blue color
        yellow : str
            The ANSI representation of yellow color
        red : str
            The ANSI representation of red color
        bold_red : str
            The ANSI representation of bold red color
        reset : str
            Reset format attribute
        
        Object attributes
        -----------------
        self.fmt : str
            Format of log messages
        self.FORMATS : dict[int, str]
            Dictionary of log_level and its ANSI color key-value pairs
        
        Methods
        -------
        format(self, record)
            Format specified `record` as text
    """
    # Class variables #
    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    def __init__(self, fmt):
        """ Initializes object attributes of inheriting class as well as
            some new attributes.
        """
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        """ Format specified `record` as text.
        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)