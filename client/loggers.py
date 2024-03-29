""" Module configures Logger objects for the client program.

    Module is not intended to be runned!
    Defines 2 main Logger objects:
    main_logger : Logger
        Logger used for logging messages on main thread on client
    sec_logger : Logger
        Logger used to log messages on receiving thread on client
    
    Used built-in modules
    ---------------------
    logging

    Used custom modules
    -------------------
    global_vars, logging_formatter
"""

import logging
from .global_vars import prompt_msg
from .logging_formatter import CustomFormatter

# Configure main logger for logging messages in main thread #
main_logger = logging.getLogger("main")
main_logger.setLevel(logging.INFO)
main_sh = logging.StreamHandler()
main_sh.setLevel(logging.INFO)
main_log_format = CustomFormatter("%(levelname)s: %(message)s")
main_sh.setFormatter(main_log_format)
main_logger.addHandler(main_sh)


# Configure sec_logger for usage in client's receiving thread #
sec_logger = logging.getLogger("sec_logger")
sec_logger.setLevel(logging.INFO)
sec_sh = logging.StreamHandler()
sec_sh.setLevel(logging.INFO)
sec_sh.terminator = f"\n{prompt_msg}"
sec_log_format = CustomFormatter("\n%(levelname)s: %(message)s")
sec_sh.setFormatter(sec_log_format)
sec_logger.addHandler(sec_sh)