import hmac
import os
import ssl
import threading
import time
from typing import Callable

from ldap3 import BASE, NONE, Connection, Server, Tls
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars

from ..utils.config import auth_store

ADMIN_USERNAME = "admin"
LDAP_DEFAULTS = {
    "enabled": False,
    "url": "",
    "start_tls": False,
    "ca_file": "",
    "bind_dn": "",
    "bind_password": "",
    "user_base": "",
    "user_filter": "(uid={username})",
    "admin_group": "",
    "viewer_group": "",
    "timeout": 5,
}
MAX_DELAY_SECONDS = 5.0
FAILURE_WINDOW_SECONDS = 900

_failures: dict[tuple[str, str], tuple[int, float]] = {}
_failures_lock = threading.Lock()


class LDAPLoginError(Exception):
    pass


def admin_password() -> str:
    return os.environ.get("RADAUTOPY_ADMIN_PASSWORD", "")


def ldap_settings() -> dict:
    return {**LDAP_DEFAULTS, **auth_store.get_setting("ldap")}


def failure_delay(ip: str, username: str) -> float:
    now = time.monotonic()
    with _failures_lock:
        for key in [k for k, (_, t) in _failures.items() if now - t > FAILURE_WINDOW_SECONDS]:
            del _failures[key]
        count = _failures.get((ip, username), (0, 0))[0]
    return 0.0 if count == 0 else min(0.25 * 2 ** (count - 1), MAX_DELAY_SECONDS)


def record_attempt(ip: str, username: str, ok: bool) -> None:
    with _failures_lock:
        if ok:
            _failures.pop((ip, username), None)
        else:
            count = _failures.get((ip, username), (0, 0))[0]
            _failures[(ip, username)] = (count + 1, time.monotonic())


def authenticate(username: str, password: str) -> tuple[str, str] | None:
    if not username or not password:
        return None
    if username == ADMIN_USERNAME:
        if hmac.compare_digest(password.encode(), admin_password().encode()):
            return "admin", "admin"
        return None
    user = auth_store.get_user(username)
    if user is not None:
        return (user["role"], "local") if auth_store.verify_password(password, user["password_hash"]) else None
    settings = ldap_settings()
    if not settings["enabled"]:
        return None
    try:
        return ldap_authenticate(settings, username, password), "ldap"
    except LDAPLoginError:
        return None


def ldap_authenticate(settings: dict, username: str, password: str, log: Callable[[str], None] = lambda _: None) -> str:
    if not password:
        raise LDAPLoginError("empty password")
    timeout = int(settings.get("timeout") or 5)
    tls = Tls(validate=ssl.CERT_REQUIRED, ca_certs_file=settings.get("ca_file") or None)
    server = Server(settings["url"], get_info=NONE, tls=tls, connect_timeout=timeout)

    def connect(user: str | None, secret: str | None) -> Connection:
        conn = Connection(server, user=user, password=secret, receive_timeout=timeout, raise_exceptions=True)
        conn.open()
        if settings.get("start_tls"):
            conn.start_tls()
        conn.bind()
        return conn

    try:
        log(f"connecting to {settings['url']}{' with StartTLS' if settings.get('start_tls') else ''}")
        service = connect(settings.get("bind_dn") or None, settings.get("bind_password") or None)
        log(f"service bind ok ({settings.get('bind_dn') or 'anonymous'})")

        search_filter = settings["user_filter"].replace("{username}", escape_filter_chars(username))
        service.search(settings["user_base"], search_filter, attributes=["memberOf"])
        entries = [e for e in service.response if e.get("type") == "searchResEntry"]
        if len(entries) != 1:
            raise LDAPLoginError(f"{search_filter} matched {len(entries)} entries under {settings['user_base']}, expected 1")
        user_dn = entries[0]["dn"]
        member_of = {g.lower() for g in entries[0].get("attributes", {}).get("memberOf", []) or []}
        log(f"found user {user_dn}")

        connect(user_dn, password).unbind()
        log("user bind ok")

        def in_group(group_dn: str) -> bool:
            if group_dn.lower() in member_of:
                return True
            group_filter = (
                f"(|(member={escape_filter_chars(user_dn)})(uniqueMember={escape_filter_chars(user_dn)})"
                f"(memberUid={escape_filter_chars(username)}))"
            )
            service.search(group_dn, group_filter, search_scope=BASE, attributes=[])
            return any(e.get("type") == "searchResEntry" for e in service.response)

        if settings.get("admin_group") and in_group(settings["admin_group"]):
            log(f"member of admin group {settings['admin_group']}")
            role = "admin"
        elif not settings.get("viewer_group"):
            log("no viewer group configured; any directory user is a viewer")
            role = "viewer"
        elif in_group(settings["viewer_group"]):
            log(f"member of viewer group {settings['viewer_group']}")
            role = "viewer"
        else:
            raise LDAPLoginError("user is not in the admin or viewer group")
        service.unbind()
    except LDAPException as e:
        raise LDAPLoginError(f"{type(e).__name__}: {e}") from e
    log(f"role: {role}")
    return role
