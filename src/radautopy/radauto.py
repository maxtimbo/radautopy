import os
import sys
from datetime import datetime, timezone

import click
from pathlib import Path
from importlib.metadata import version

from .utils.config import EMAIL_MODES, LOG_DIR, store
from .utils.config.config import ConfigJSON
from .utils.errors import ConfigError

from .utils.remote import build_remote, check_runner
from .utils.mail import RadMail
from .utils.log_setup import RadLogger

from .runners.standard import perform_standard
from .runners.news import perform_news
from .runners.split_single import perform_split_single
from .runners.ttwn import perform_ttwn

LOG_FILE = Path(LOG_DIR, "radautopy.log")

logger = RadLogger(LOG_FILE).get_logger()


def resolve_email_mode(job: dict, email_override: str | None, disable_email: bool) -> str:
    if email_override:
        return email_override
    if disable_email:
        return "never"
    mode = job.get("email_mode", "always")
    if mode not in EMAIL_MODES:
        logger.warning(f"unknown email_mode '{mode}', using 'always'")
        return "always"
    return mode


def finish(mailer: RadMail | None, email_mode: str, ok: bool) -> None:
    if mailer is None or email_mode == "never" or (email_mode == "failure" and ok):
        return
    if mailer.table_data:
        mailer.concat_table()
    if not mailer.message:
        return
    mailer.send_mail(alt_subject=None if ok else f"FAILED: {mailer.subject}")


def record_run(ctx: click.Context, ok: bool, message: str = "") -> None:
    try:
        trigger = os.environ.get("RADAUTOPY_TRIGGER", "cli")
        store.record_run(ctx.obj["config_file"], ctx.obj["started_at"], ok, trigger, message)
    except Exception:
        logger.exception("could not record run result")


def fail(ctx: click.Context, message: str) -> None:
    logger.exception(message)
    record_run(ctx, ok=False, message=message)
    click.echo(f"error: {message}", err=True)
    mailer = ctx.obj.get("mailer")
    if mailer is not None:
        mailer.p(message)
    finish(mailer, ctx.obj.get("email_mode", "always"), ok=False)
    sys.exit(1)


def run_guarded(ctx: click.Context, runner_name: str, runner, *args) -> None:
    obj = ctx.obj
    try:
        check_runner(obj["config"].job.get("job_type"), runner_name)
        if not getattr(obj["config"], "filemap", None):
            raise ConfigError("filemap is empty; add at least one track")
        ok = runner(obj["config"], obj["mailer"], obj["email_mode"], obj["remote"], *args)
    except Exception as e:
        fail(ctx, f"{obj['config_file']} failed during {runner_name}: {e}")
        return
    finish(obj["mailer"], obj["email_mode"], ok)
    record_run(ctx, ok, "" if ok else "finished with errors; see radautopy.log")
    if not ok:
        logger.error(f"{obj['config_file']} finished with errors")
        click.echo(f"error: {obj['config_file']} finished with errors; see radautopy.log", err=True)
        sys.exit(1)
    logger.info(f"{obj['config_file']} finished successfully")


@click.group()
@click.version_option(version = version("radautopy"), prog_name = "radautopy")
@click.option('-v', '--verbose', is_flag=True, help='enable verbose mode')
@click.option('--disable_email', is_flag=True, help='never send email (same as --email never)', default=False)
@click.option('--email', 'email_override', type=click.Choice(EMAIL_MODES), help="override the job's email setting")
@click.argument('config_file')
@click.pass_context
def cli(ctx: click.Context, config_file: str, verbose: bool, disable_email: bool, email_override: str | None) -> None:
    if verbose:
        RadLogger(LOG_FILE, verbose=True)

    ctx.ensure_object(dict)
    ctx.obj['config_file'] = config_file
    ctx.obj['started_at'] = datetime.now(timezone.utc)
    try:
        config = ConfigJSON(config_file)
        ctx.obj['config'] = config
        ctx.obj['email_mode'] = resolve_email_mode(config.job, email_override, disable_email)
        ctx.obj['mailer'] = RadMail(**config.email)
        ctx.obj['remote'] = build_remote(config)
    except Exception as e:
        fail(ctx, f"{config_file} could not start: {e}")

@cli.command()
@click.option('-t', '--tries', type=click.IntRange(min=1), default=1, help='define number of tries')
@click.option('-s', '--sleep_timer', type=click.IntRange(min=0), default=1200, help='define number of seconds between tries')
@click.pass_context
def news(ctx: click.Context, tries: int, sleep_timer: int) -> None:
    run_guarded(ctx, "news", perform_news, tries, sleep_timer)

@cli.command()
@click.pass_context
def standard(ctx: click.Context) -> None:
    run_guarded(ctx, "standard", perform_standard)

@cli.command(name='split_single')
@click.option('-t', '--threshold', type=int, default = -60, help='define db threshold for silence split')
@click.option('-d', '--duration', type=int, default = 15, help='silence duration in seconds')
@click.pass_context
def split_single(ctx: click.Context, threshold: int, duration: int) -> None:
    run_guarded(ctx, "split_single", perform_split_single, threshold, duration)

@cli.command()
@click.pass_context
def ttwn(ctx: click.Context) -> None:
    run_guarded(ctx, "ttwn", perform_ttwn)
