import pathlib

args_dict = {
    "prog": "RadioAutoPy FTP",
    "description": "Use this for FTP shows."
}

DEFAULT_CONFIG = {
    "FTP": {
        "ftp_server": str,
        "ftp_username": str,
        "ftp_password": str,
        "ftp_pasv": True,
        "ftp_dir": "",
        "ftp_files": ""
    },
}
