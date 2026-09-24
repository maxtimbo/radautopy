from .config.config import ConfigJSON
from .ftp import RadFTP
from .sftp import RadSFTP
from .cloud import RadCloud
from .rss import RadRSS
from .ttwn import TTWN

REMOTE_CLASSES = {
    "ftp": (RadFTP, "FTP"),
    "sftp": (RadSFTP, "SFTP"),
    "cloud": (RadCloud, "cloud"),
    "rss": (RadRSS, "rss"),
    "ttwn": (TTWN, "ttwn"),
}


def build_remote(config: ConfigJSON):
    job_type = config.job["job_type"]
    if job_type not in REMOTE_CLASSES:
        raise ValueError(f"unknown job_type: {job_type}")

    remote_cls, attr = REMOTE_CLASSES[job_type]
    return remote_cls(**getattr(config, attr))
