import os
import subprocess
import time
import uuid
from pathlib import Path

import pytest
import requests
from testcontainers.core.container import DockerContainer

from baikal_install import create_user, install, login_admin

ADMIN_PASSWORD = "IntegrationTestAdmin123!"
USER_PASSWORD = "IntegrationTestUser123!"
USERNAME = "davtest"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _baikal_version():
    version = os.environ.get("BAIKAL_VERSION")
    if version:
        return version

    versions = REPOSITORY_ROOT / "versions.env"
    for line in versions.read_text().splitlines():
        key, separator, value = line.partition("=")
        if separator and key == "BAIKAL_VERSION":
            return value
    raise RuntimeError(f"BAIKAL_VERSION not found in {versions}")


def _wait_for_http(url: str, timeout: int = 30):
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            requests.get(url, timeout=2)
            return
        except requests.exceptions.ConnectionError as exc:
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"{url} never became reachable: {last_error}")


@pytest.fixture(scope="session")
def baikal_server():
    image_tag = f"baikal-itest:{uuid.uuid4().hex[:8]}"

    subprocess.run(
        [
            "docker",
            "buildx",
            "build",
            "--build-arg",
            f"BAIKAL_VERSION={_baikal_version()}",
            "--tag",
            image_tag,
            str(REPOSITORY_ROOT),
        ],
        check=True,
    )

    container = DockerContainer(image_tag).with_exposed_ports(80)
    started = False
    try:
        container.start()
        started = True
        host = container.get_container_host_ip()
        port = container.get_exposed_port(80)
        base_url = f"http://{host}:{port}"

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
        if started:
            container.stop()
        subprocess.run(
            ["docker", "image", "rm", "--force", image_tag],
            check=False,
            capture_output=True,
        )
