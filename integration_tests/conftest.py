import os
import socket
import subprocess
import time
import uuid

import httpx2
import pytest

from baikal import create_user, install, login_admin

BAIKAL_IMAGE = os.environ.get("BAIKAL_IMAGE", "baikal:ci")
ADMIN_PASSWORD = "IntegrationTestAdmin123!"
USER_PASSWORD = "IntegrationTestUser123!"
USERNAME = "davtest"


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _wait_for_http(url, timeout=30):
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            httpx2.get(url, timeout=2)
            return
        except httpx2.TransportError as exc:
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"{url} never became reachable: {last_error}")


@pytest.fixture(scope="session")
def baikal_server():
    container_name = f"baikal-itest-{uuid.uuid4().hex[:8]}"
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"

    subprocess.run(
        ["docker", "run", "-d", "--name", container_name, "-p", f"{port}:80", BAIKAL_IMAGE],
        check=True,
        capture_output=True,
    )
    try:
        _wait_for_http(base_url)
        session = install(base_url, ADMIN_PASSWORD)
        login_admin(session, base_url, ADMIN_PASSWORD)
        create_user(session, base_url, USERNAME, USER_PASSWORD)

        yield {
            "base_url": base_url,
            "username": USERNAME,
            "password": USER_PASSWORD,
        }
    finally:
        if os.environ.get("BAIKAL_KEEP_CONTAINER"):
            print(f"leaving container {container_name} running for debugging")
        else:
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
