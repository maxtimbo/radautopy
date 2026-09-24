import io
import json
import logging
import os
import shlex
import subprocess
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import uvicorn
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from ..utils.config import (
    LOG_DIR,
    EMAIL_CONFIG,
    DEFAULT_DIRS,
    JOB_TYPE_SKELETONS,
    JOB_RUNNERS,
    EMAIL_MODES,
    build_dict,
    store,
)
from ..utils.config.config import ConfigJSON
from ..utils.config.config_modify import build_quick_filemap
from ..utils.config.replace_fillers import ReplaceFillers
from ..utils.cron import describe, next_runs, trigger_from_crontab
from ..utils.errors import ConfigError, RadautopyError
from ..utils.mail import RadMail, normalize_recipients
from ..utils.remote import build_remote, check_runner
from ..utils.utilities import check_writable, make_dirs, radautopy_executable

RADAUTOPY_LOG = LOG_DIR / "radautopy.log"
KNOWN_LOGS = ["radautopy.log", "radautopy-scheduler.log"]

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="radautopy control layer")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")


@app.exception_handler(RadautopyError)
async def radautopy_error_handler(request: Request, exc: RadautopyError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"{request.method} {request.url.path} failed")
    return JSONResponse(status_code=500, content={"detail": f"server error: {type(exc).__name__}: {exc}"})


def _job_name(name: str) -> str:
    if "/" in name or ".." in name or name == "email.json":
        raise HTTPException(status_code=400, detail="invalid job name")
    if not name.endswith(".json"):
        name = f"{name}.json"
    return name


def _read_config(name: str) -> dict:
    try:
        return store.get(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{name} not found")


def _job_warnings(config: dict) -> list[str]:
    job = config.get("job")
    if not isinstance(job, dict):
        return ["config has no 'job' section"]
    warnings = []
    try:
        check_runner(job.get("job_type"), job.get("job_runner"))
    except ConfigError as e:
        warnings.append(str(e))
    if job.get("email_mode", "always") not in EMAIL_MODES:
        warnings.append(f"email_mode must be one of {', '.join(EMAIL_MODES)}")
    if job.get("cron_expression"):
        try:
            trigger_from_crontab(job["cron_expression"])
        except ValueError as e:
            warnings.append(f"cron expression is invalid, so the job will not be scheduled: {e}")
    try:
        shlex.split(job.get("extra_args") or "")
    except ValueError as e:
        warnings.append(f"extra_args is invalid: {e}")
    if not config.get("filemap"):
        warnings.append("filemap is empty; the job will fail until at least one track is added")
    return warnings


def _dir_warnings(config: dict) -> list[str]:
    warnings = []
    for key, path in (config.get("dirs") or {}).items():
        if not path:
            warnings.append(f"{key} is empty")
            continue
        try:
            check_writable(Path(path))
        except ConfigError as e:
            warnings.append(f"{key}: {e}")
    return warnings


def _recipient_warnings(data: dict) -> list[str]:
    email = data.get("email")
    if not isinstance(email, dict) or "recipient" not in email:
        return []
    email["recipient"] = normalize_recipients(email["recipient"])
    if not email["recipient"]:
        return ["no email recipients set"]
    bad = [r for r in email["recipient"] if "@" not in r]
    return [f"invalid recipient address(es): {', '.join(bad)}"] if bad else []


def _write_config(name: str, data: dict) -> list[str]:
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="config must be a JSON object")
    warnings = _recipient_warnings(data)
    store.save(name, data)
    if name == "email.json":
        return warnings
    return warnings + _job_warnings(data) + _dir_warnings(data)


def _replace_type_markers(section: dict) -> dict:
    return {k: ("" if v is str else v) for k, v in section.items()}


def _list_job_names() -> list[str]:
    return [n for n in store.list_names() if n != "email.json"]


@app.get("/api/jobs")
def list_jobs() -> list[dict]:
    jobs = []
    for name in _list_job_names():
        try:
            config = store.get(name)
        except FileNotFoundError:
            continue
        job = config.get("job", {})
        jobs.append({
            "filename": name,
            "job_name": job.get("job_name", ""),
            "description": job.get("description", ""),
            "job_type": job.get("job_type", ""),
            "job_runner": job.get("job_runner", ""),
            "cron_expression": job.get("cron_expression", ""),
            "enabled": job.get("enabled", True),
            "cron_description": _cron_description(job.get("cron_expression", "")),
            "warnings": _job_warnings(config),
        })
    return jobs


def _cron_description(expression: str) -> str:
    if not expression:
        return "not scheduled"
    try:
        next_runs(expression, count=1)
        return describe(expression)
    except Exception:
        return "invalid cron expression"


@app.get("/api/cron")
def cron_info(expression: str) -> dict:
    try:
        runs = next_runs(expression)
        description = describe(expression)
    except Exception as e:
        return {"valid": False, "error": str(e)}
    return {
        "valid": True,
        "description": description,
        "next_runs": [r.strftime("%a %Y-%m-%d %H:%M %Z") for r in runs],
    }


@app.post("/api/jobs")
def create_job(payload: dict = Body(...)) -> dict:
    filename = payload.get("filename")
    job_type = payload.get("job_type") or payload.get("job", {}).get("job_type")
    if not filename:
        raise HTTPException(status_code=400, detail="filename is required")
    if job_type not in JOB_TYPE_SKELETONS:
        raise HTTPException(status_code=400, detail=f"job_type must be one of {list(JOB_TYPE_SKELETONS)}")

    name = _job_name(filename)
    if store.exists(name):
        raise HTTPException(status_code=409, detail=f"{name} already exists")

    if "job" in payload:
        config = {k: v for k, v in payload.items() if k != "filename"}
    else:
        config = deepcopy(build_dict(JOB_TYPE_SKELETONS[job_type]))
        config["job"] = _replace_type_markers(config["job"])
        config["job"]["job_type"] = job_type
        type_key = next(iter(JOB_TYPE_SKELETONS[job_type]))
        config[type_key] = _replace_type_markers(config[type_key])
        config["filemap"] = []

    warnings = _write_config(name, config)
    return {"filename": name, "config": config, "warnings": warnings}


@app.post("/api/filemap/quick")
def quick_filemap(payload: dict = Body(...)) -> dict:
    try:
        hours = int(payload["hours"])
        segments = int(payload["segments"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="hours and segments must be integers")
    if hours < 1 or segments < 1:
        raise HTTPException(status_code=400, detail="hours and segments must be at least 1")

    filemap = build_quick_filemap(
        hours,
        segments,
        payload.get("input_pattern", ""),
        payload.get("output_pattern", ""),
        payload.get("artist_pattern", ""),
        payload.get("title_pattern", ""),
    )
    return {"filemap": filemap}


@app.get("/api/jobs/{name}")
def get_job(name: str) -> dict:
    return _read_config(_job_name(name))


@app.put("/api/jobs/{name}")
def put_job(name: str, payload: dict = Body(...)) -> dict:
    name = _job_name(name)
    warnings = _write_config(name, payload)
    return {"filename": name, "config": payload, "warnings": warnings}


@app.put("/api/jobs/{name}/enabled")
def set_job_enabled(name: str, payload: dict = Body(...)) -> dict:
    name = _job_name(name)
    enabled = payload.get("enabled")
    if not isinstance(enabled, bool):
        raise HTTPException(status_code=400, detail="enabled must be true or false")
    config = _read_config(name)
    config.setdefault("job", {})["enabled"] = enabled
    store.save(name, config)
    return {"filename": name, "enabled": enabled}


@app.delete("/api/jobs/{name}")
def delete_job(name: str) -> dict:
    name = _job_name(name)
    if not store.delete(name):
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return {"filename": name, "deleted": True}


@app.post("/api/jobs/{name}/validate")
def validate_job(name: str) -> dict:
    name = _job_name(name)
    if not store.exists(name):
        raise HTTPException(status_code=404, detail=f"{name} not found")

    warnings = _job_warnings(_read_config(name))
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            config = ConfigJSON(name)
            remote = build_remote(config)
            remote.validate()
    except Exception as e:
        return {"output": buf.getvalue(), "error": str(e), "warnings": warnings}

    return {"output": buf.getvalue(), "warnings": warnings}


@app.post("/api/jobs/{name}/run")
def run_job(name: str) -> dict:
    name = _job_name(name)
    config = _read_config(name)
    job = config.get("job", {})
    job_runner = job.get("job_runner")
    check_runner(job.get("job_type"), job_runner)

    try:
        extra_args = shlex.split(job.get("extra_args") or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"extra_args is invalid: {e}")
    command = [radautopy_executable(), name, job_runner, *extra_args]
    make_dirs(LOG_DIR)
    with open(RADAUTOPY_LOG, "a") as log_file:
        log_file.write(f"\n--- web-triggered run {datetime.now(timezone.utc).isoformat()}: {' '.join(command)} ---\n")
        log_file.flush()
        process = subprocess.Popen(command, stdout=log_file, stderr=subprocess.STDOUT)
    return {"status": "started", "pid": process.pid, "command": command}


@app.get("/api/email")
def get_email() -> dict:
    if not store.exists("email.json"):
        skeleton = deepcopy(EMAIL_CONFIG)
        skeleton["email"] = _replace_type_markers(skeleton["email"])
        return {"exists": False, "config": skeleton}
    return {"exists": True, "config": store.get("email.json")}


@app.put("/api/email")
def put_email(payload: dict = Body(...)) -> dict:
    if not isinstance(payload.get("email"), dict):
        raise HTTPException(status_code=400, detail="email config must have an 'email' section")
    warnings = _write_config("email.json", payload)
    return {"config": payload, "warnings": warnings}


@app.post("/api/email/validate")
def validate_email() -> dict:
    if not store.exists("email.json"):
        raise HTTPException(status_code=404, detail="email.json not found")

    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            config = store.get("email.json")
            mailer = RadMail(**config["email"])
            mailer.validate()
    except Exception as e:
        return {"output": buf.getvalue(), "error": str(e)}

    return {"output": buf.getvalue()}


@app.get("/api/log", response_class=PlainTextResponse)
def tail_log(name: str = "radautopy.log", lines: int = 200) -> str:
    if name not in KNOWN_LOGS:
        raise HTTPException(status_code=400, detail=f"name must be one of {KNOWN_LOGS}")
    path = LOG_DIR / name
    if not path.exists():
        return ""
    with open(path) as f:
        return "".join(f.readlines()[-lines:])


@app.get("/")
def jobs_page(request: Request):
    return templates.TemplateResponse(request, "jobs.html", {"jobs": list_jobs()})


@app.get("/logs")
def logs_page(request: Request):
    return templates.TemplateResponse(request, "logs.html", {"log_names": KNOWN_LOGS})


def _job_form_context(config: dict) -> dict:
    job_type = config.get("job", {}).get("job_type", "")
    type_key_map = {jt: next(iter(skel)) for jt, skel in JOB_TYPE_SKELETONS.items()}
    all_type_fields = {}
    for jt, skel in JOB_TYPE_SKELETONS.items():
        key = type_key_map[jt]
        if jt == job_type:
            all_type_fields[jt] = config.get(key, {})
        else:
            all_type_fields[jt] = _replace_type_markers(deepcopy(skel[key]))
    filler_variables = [[f, func(f, f)] for f, func in ReplaceFillers("").filler_functions.items()]
    filler_variables += [["{hour}", "1"], ["{segment}", "1"], ["{count}", "1"]]
    return {
        "config": config,
        "config_json": json.dumps(config),
        "job_runners": JOB_RUNNERS,
        "email_modes": EMAIL_MODES,
        "job_types": list(JOB_TYPE_SKELETONS),
        "current_job_type": job_type,
        "type_key_map": type_key_map,
        "all_type_fields": all_type_fields,
        "filler_variables": filler_variables,
        "email_fields": list(EMAIL_CONFIG["email"]),
        "email_overrides": config.get("email", {}),
    }


@app.get("/jobs/new")
def new_job_page(request: Request):
    blank = {
        "job": _replace_type_markers(deepcopy(build_dict({})["job"])),
        "dirs": deepcopy(DEFAULT_DIRS["dirs"]),
        "filemap": [],
    }
    blank["job"]["job_type"] = list(JOB_TYPE_SKELETONS)[0]
    context = _job_form_context(blank)
    context.update({"filename": "", "is_new": True})
    return templates.TemplateResponse(request, "job_config.html", context)


@app.get("/jobs/{name}/edit")
def edit_job_page(request: Request, name: str):
    name = _job_name(name)
    config = _read_config(name)
    context = _job_form_context(config)
    context.update({"filename": name, "is_new": False, "warnings": _job_warnings(config)})
    return templates.TemplateResponse(request, "job_config.html", context)


@app.get("/email/edit")
def email_edit_page(request: Request):
    result = get_email()
    return templates.TemplateResponse(request, "email_edit.html", {
        "config": result["config"],
        "exists": result["exists"],
    })


@app.get("/rclone")
def rclone_page(request: Request):
    return templates.TemplateResponse(request, "rclone.html", {})


@app.get("/rclone/login")
def rclone_login(request: Request):
    # rclone-web only keeps the API url if login succeeds, so the link must carry credentials
    host = request.url.hostname
    gui_port = os.environ.get("RCLONE_GUI_PORT", "5522")
    api_port = os.environ.get("RCLONE_API_PORT", "5533")
    query = urlencode({
        "url": f"{request.url.scheme}://{host}:{api_port}/",
        "user": os.environ.get("RCLONE_GUI_USER", ""),
        "pass": os.environ.get("RCLONE_GUI_PASS", ""),
    })
    return RedirectResponse(f"{request.url.scheme}://{host}:{gui_port}/login?{query}")


def main() -> None:
    host = os.environ.get("RADAUTOPY_WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("RADAUTOPY_WEB_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
