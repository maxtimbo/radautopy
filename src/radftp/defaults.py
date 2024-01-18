import pathlib

args_dict = {
    "prog": "RadioAutoPy FTP",
    "description": "Use this for FTP shows."
}

DEFAULT_CONFIG = {
    "FTP": {
        "server": str,
        "username": str,
        "password": str,
        "pasv": True,
        "dir": "",
    },
}
