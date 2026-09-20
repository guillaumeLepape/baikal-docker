import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

import httpx2
import pytest
from dotenv import dotenv_values
from testcontainers.core.container import DockerContainer

from baikal import create_user, install, login_admin

BAIKAL_IMAGE = "baikal:test"
ADMIN_PASSWORD = "IntegrationTestAdmin123!"
USER_PASSWORD = "IntegrationTestUser123!"
USERNAME = "davtest"


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
def baikal_image():
    root_path = Path(__file__).parents[1]

    config = dotenv_values(root_path / "versions.env")

    subprocess.run(
        [
            "docker",
            "buildx",
            "build",
            "--tag",
            BAIKAL_IMAGE,
            "--build-arg",
            f"BAIKAL_VERSION={config['BAIKAL_VERSION']}",
            str(root_path),
        ],
        check=True,
        capture_output=True,
    )

    return BAIKAL_IMAGE


@pytest.fixture(scope="session")
def baikal_container(baikal_image):
    """Returns a context manager starting an installed Baikal container.

    `env` sets container environment variables and `volumes` maps host paths to
    container paths.
    """

    @contextmanager
    def start(env=None, volumes=None):
        container = DockerContainer(baikal_image, ports=[80])
        for name, value in (env or {}).items():
            container.with_env(name, value)
        for host_path, container_path in (volumes or {}).items():
            container.with_volume_mapping(host_path, container_path, "rw")

        with container:
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
                "container": container,
            }

    return start


@pytest.fixture(scope="session")
def baikal_server(baikal_container):
    with baikal_container() as server:
        yield server
