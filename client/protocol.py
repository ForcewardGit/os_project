""" Protocols for a client to recognize commands sent from server and take 
    appropriate actions.
"""

CONNECT = "CONNECT"
DISCONNECT = "DISCONNECT"
LU = "LU"
LF = "LF"
MESSAGE = "MESSAGE"
READ = "READ"
WRITE = "WRITE"
OVERWRITE = "OVERWRITE"
APPEND = "APPEND"
OVERREAD = "OVERREAD"
APPENDFILE = "APPENDFILE"