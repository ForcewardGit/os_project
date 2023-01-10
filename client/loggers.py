""" Module that configures Logger objects for the client program.
"""

import logging
from .global_vars import prompt_msg

# Configure main logger for logging messages in main thread #
main_logger = logging.getLogger("main")
main_logger.setLevel(logging.DEBUG)
main_sh = logging.StreamHandler()
main_sh.setLevel(logging.DEBUG)
main_log_format = logging.Formatter("%(levelname)s: %(message)s")
main_sh.setFormatter(main_log_format)
main_logger.addHandler(main_sh)


# Configure sec_logger for usage in client's receiving thread #
sec_logger = logging.getLogger("sec_logger")
sec_logger.setLevel(logging.INFO)
sec_sh = logging.StreamHandler()
sec_sh.setLevel(logging.DEBUG)
sec_sh.terminator = f"\n{prompt_msg}"
sec_log_format = logging.Formatter("\n%(levelname)s: %(message)s")
sec_sh.setFormatter(sec_log_format)
sec_logger.addHandler(sec_sh)