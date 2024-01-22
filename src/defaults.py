import pathlib


DEFAULT_ROOT_DIR = pathlib.Path("~/radautopy").expanduser()
DEFAULT_LOG_DIR = pathlib.Path(DEFAULT_ROOT_DIR, "log")
DEFAULT_CONFIG_DIR = pathlib.Path(DEFAULT_ROOT_DIR, "config")

DEFAULT_DOWNLOAD_DIR = pathlib.Path(DEFAULT_ROOT_DIR, "download")
DEFAULT_EXPORT_DIR = pathlib.Path(DEFAULT_ROOT_DIR, "export")
DEFAULT_AUDIO_TMP = pathlib.Path(DEFAULT_ROOT_DIR, "audio_tmp")

DEFAULT_CONFIG = {
    "email": {
        "server": "smtp.example",
        "port": 465,
        "username": "EMAILUSER",
        "password": "EMAILPASS",
        "reply_to": "example@domain",
        "recipient": "example@domain",
    },
    "dirs": {
        "download_dir": str(DEFAULT_DOWNLOAD_DIR),
        "export_dir": str(DEFAULT_EXPORT_DIR),
        "audio_tmp": str(DEFAULT_AUDIO_TMP),
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
