"""Automates Baikal's first-run web install wizard over HTTP.

Baikal has no config-seeding mechanism, so a fresh container must be
walked through /admin/install/ before any CalDAV/CardDAV request will
work. This replicates exactly what a human clicking through the wizard
would submit.
"""

import re

import httpx2

CSRF_RE = re.compile(r'CSRF_TOKEN"\s+value="([^"]*)"')


def _csrf(html):
    match = CSRF_RE.search(html)
    if not match:
        raise RuntimeError("could not find CSRF token in Baikal response")
    return match.group(1)


def install(base_url, admin_password):
    """Runs the install wizard: standard config, then sqlite database.

    Baikal's Formal\\Form only persists a submission when the hidden
    "refreshed" field is "0" - any other value is treated as a
    live re-render of the form (e.g. after changing the DB backend
    dropdown) and is intentionally not saved.
    """
    session = httpx2.Client(follow_redirects=True)

    resp = session.get(f"{base_url}/admin/install/")
    resp.raise_for_status()
    token = _csrf(resp.text)

    resp = session.post(
        f"{base_url}/admin/install/",
        files={
            "Baikal_Model_Config_Standard::submitted": (None, "1"),
            "refreshed": (None, "0"),
            "CSRF_TOKEN": (None, token),
            "data[timezone]": (None, "UTC"),
            "witness[timezone]": (None, "1"),
            "data[card_enabled]": (None, "1"),
            "witness[card_enabled]": (None, "1"),
            "data[cal_enabled]": (None, "1"),
            "witness[cal_enabled]": (None, "1"),
            "data[invite_from]": (None, "noreply@example.com"),
            "witness[invite_from]": (None, "1"),
            "data[dav_auth_type]": (None, "Basic"),
            "witness[dav_auth_type]": (None, "1"),
            "data[admin_passwordhash]": (None, admin_password),
            "witness[admin_passwordhash]": (None, "1"),
            "data[admin_passwordhash_confirm]": (None, admin_password),
            "witness[admin_passwordhash_confirm]": (None, "1"),
        },
    )
    resp.raise_for_status()
    if "Exception" in resp.text:
        raise RuntimeError(f"standard config step failed: {resp.text[:500]}")

    resp = session.get(f"{base_url}/admin/install/?/database")
    resp.raise_for_status()
    token = _csrf(resp.text)

    resp = session.post(
        f"{base_url}/admin/install/?/database",
        files={
            "Baikal_Model_Config_Database::submitted": (None, "1"),
            "refreshed": (None, "0"),
            "CSRF_TOKEN": (None, token),
            "data[backend]": (None, "sqlite"),
            "witness[backend]": (None, "1"),
            "data[sqlite_file]": (None, "/var/www/baikal/Specific/db/db.sqlite"),
            "witness[sqlite_file]": (None, "1"),
        },
    )
    resp.raise_for_status()
    if "Exception" in resp.text:
        raise RuntimeError(f"database config step failed: {resp.text[:500]}")

    return session


def login_admin(session, base_url, admin_password):
    resp = session.post(
        f"{base_url}/admin/",
        files={
            "auth": (None, "1"),
            "login": (None, "admin"),
            "password": (None, admin_password),
        },
    )
    resp.raise_for_status()

    resp = session.get(f"{base_url}/admin/")
    resp.raise_for_status()
    if "/admin/?/logout/" not in resp.text:
        raise RuntimeError("admin login failed")
    return resp.text


def create_user(session, base_url, username, password):
    resp = session.get(f"{base_url}/admin/?/users/new/1/")
    resp.raise_for_status()
    token = _csrf(resp.text)

    resp = session.post(
        f"{base_url}/admin/?/users/new/1/",
        files={
            "Baikal_Model_User::submitted": (None, "1"),
            "refreshed": (None, "0"),
            "CSRF_TOKEN": (None, token),
            "data[username]": (None, username),
            "witness[username]": (None, "1"),
            "data[displayname]": (None, username),
            "witness[displayname]": (None, "1"),
            "data[email]": (None, f"{username}@example.com"),
            "witness[email]": (None, "1"),
            "data[password]": (None, password),
            "witness[password]": (None, "1"),
            "data[passwordconfirm]": (None, password),
            "witness[passwordconfirm]": (None, "1"),
        },
    )
    resp.raise_for_status()

    resp = session.get(f"{base_url}/admin/?/users/")
    resp.raise_for_status()
    if username not in resp.text:
        raise RuntimeError(f"user creation for {username!r} failed")
