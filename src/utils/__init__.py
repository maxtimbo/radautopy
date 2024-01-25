import pathlib

LOGGER_NAME = "RadioAutoPy Logger"

ROOT_DIR = pathlib.Path("~/radautopy").expanduser()
LOG_DIR = pathlib.Path(ROOT_DIR, "log")
CONFIG_DIR = pathlib.Path(ROOT_DIR, "config")

DOWNLOAD_DIR = pathlib.Path(ROOT_DIR, "download")
EXPORT_DIR = pathlib.Path(ROOT_DIR, "export")
AUDIO_TMP = pathlib.Path(ROOT_DIR, "audio_tmp")

ARGS_DICT = {
    "program": "RadioAutoPy",
    "description": ""
}

EMAIL_CONFIG = {
    "email": {
        "sender": "example sender",
        "subject": "example subject",
        "server": "smtp.example",
        "port": 465,
        "username": "EMAILUSER",
        "password": "EMAILPASS",
        "reply_to": "example@domain",
        "recipient": "example@domain",
        "header": "",
        "footer": ""
    }
}

DEFAULT_DIRS = {
    "dirs": {
        "download_dir": str(DOWNLOAD_DIR),
        "export_dir": str(EXPORT_DIR),
        "audio_tmp": str(AUDIO_TMP),
    }
}

DEFAULT_FILEMAP = {
    "filemap": [
        {
            "input_file": "input.mp3",
            "output_file": "output.wav",
            "artist": "artist",
            "title": "title"
        }
    ]
}

FTP_CONFIG = {
    "FTP": {
        "server": str,
        "username": str,
        "password": str,
        "pasv": True,
        "directory": "",
    },
}

