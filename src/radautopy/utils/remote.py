from .config import JOB_TYPE_SKELETONS, RUNNER_SUPPORT
from .config.config import ConfigJSON
from .errors import ConfigError
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


def check_job_type(job_type: str | None) -> None:
    if not job_type:
        raise ConfigError("job has no job_type; pick one in the job form")
    if job_type not in JOB_TYPE_SKELETONS:
        raise ConfigError(f"unknown job_type '{job_type}'; expected one of {', '.join(JOB_TYPE_SKELETONS)}")


def check_runner(job_type: str | None, job_runner: str | None) -> None:
    check_job_type(job_type)
    if not job_runner:
        raise ConfigError("job has no job_runner; pick one in the job form")
    if job_runner not in RUNNER_SUPPORT:
        raise ConfigError(f"unknown job_runner '{job_runner}'; expected one of {', '.join(RUNNER_SUPPORT)}")
    if job_type not in RUNNER_SUPPORT[job_runner]:
        raise ConfigError(f"runner '{job_runner}' does not support job_type '{job_type}' (supported: {', '.join(RUNNER_SUPPORT[job_runner])})")


def build_remote(config: ConfigJSON):
    job_type = config.job.get("job_type")
    check_job_type(job_type)

    remote_cls, attr = REMOTE_CLASSES[job_type]
    if not hasattr(config, attr):
        raise ConfigError(f"job_type '{job_type}' needs a '{attr}' section in the config")
    try:
        return remote_cls(**getattr(config, attr))
    except TypeError as e:
        raise ConfigError(f"'{attr}' section is invalid: {e}") from e
