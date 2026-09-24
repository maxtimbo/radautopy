import shlex
import subprocess

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .utils.config import LOG_DIR, store
from .utils.log_setup import RadLogger
from .utils.utilities import radautopy_executable

LOG_FILE = LOG_DIR / "radautopy-scheduler.log"
RESCAN_SECONDS = 60

logger = RadLogger(LOG_FILE).get_logger()


def _load_jobs() -> dict[str, dict]:
    jobs = {}
    for filename, config in store.list_jobs().items():
        job = config.get("job")
        if not job or not job.get("cron_expression"):
            continue

        jobs[filename] = job

    return jobs


def _run_job(config_name: str, job_runner: str, extra_args: str) -> None:
    command = [radautopy_executable(), config_name, job_runner, *shlex.split(extra_args)]
    logger.info(f"running {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"{config_name} exited {result.returncode}: {result.stderr}")
    else:
        logger.info(f"{config_name} completed")


class JobSync:
    def __init__(self, scheduler: BlockingScheduler) -> None:
        self.scheduler = scheduler
        self.known: dict[str, dict] = {}

    def sync(self) -> None:
        current = _load_jobs()

        for config_name in self.known.keys() - current.keys():
            self.scheduler.remove_job(config_name)
            logger.info(f"removed schedule for {config_name}")

        for config_name, job in current.items():
            if self.known.get(config_name) == job:
                continue
            try:
                trigger = CronTrigger.from_crontab(job["cron_expression"])
            except ValueError:
                logger.exception(f"invalid cron_expression for {config_name}")
                continue

            self.scheduler.add_job(
                _run_job,
                trigger=trigger,
                id=config_name,
                args=[config_name, job["job_runner"], job.get("extra_args", "")],
                replace_existing=True,
            )
            logger.info(f"scheduled {config_name}: {job['cron_expression']}")

        self.known = current


def main() -> None:
    scheduler = BlockingScheduler()
    job_sync = JobSync(scheduler)
    job_sync.sync()
    scheduler.add_job(job_sync.sync, "interval", seconds=RESCAN_SECONDS, id="__rescan__")

    logger.info("radautopy-scheduler starting")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("radautopy-scheduler stopping")


if __name__ == "__main__":
    main()
