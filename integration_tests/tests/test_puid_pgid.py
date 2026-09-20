import os
import subprocess

import pytest

HOST_UID = os.getuid()
HOST_GID = os.getgid()

# 101 is the image's default nginx user, using it would not prove anything
requires_non_default_ids = pytest.mark.skipif(
    HOST_UID == 101 or HOST_GID == 101,
    reason="host user or group is the image default (101)",
)


@requires_non_default_ids
def test_puid_pgid_apply_to_mounted_volumes(baikal_container, tmp_path):
    config = tmp_path / "config"
    specific = tmp_path / "specific"
    config.mkdir()
    specific.mkdir()

    with baikal_container(
        env={"PUID": str(HOST_UID), "PGID": str(HOST_GID)},
        volumes={
            str(config): "/var/www/baikal/config",
            str(specific): "/var/www/baikal/Specific",
        },
    ) as server:
        container = server["container"]

        assert container.exec(["id", "-u", "nginx"]).output.decode().strip() == str(HOST_UID)
        assert container.exec(["id", "-g", "nginx"]).output.decode().strip() == str(HOST_GID)

        # Written by php-fpm while running the install wizard and creating the user
        for path in (config / "baikal.yaml", specific / "db" / "db.sqlite"):
            stat = path.stat()
            assert (stat.st_uid, stat.st_gid) == (HOST_UID, HOST_GID), path


@pytest.mark.parametrize(
    "env",
    [{"PUID": "abc"}, {"PGID": "1x"}, {"PUID": "0"}],
    ids=["non-numeric-puid", "non-numeric-pgid", "root-puid"],
)
def test_invalid_ids_abort_startup(baikal_image, env):
    flags = [arg for name, value in env.items() for arg in ("-e", f"{name}={value}")]

    result = subprocess.run(
        ["docker", "run", "--rm", *flags, baikal_image],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode != 0
    assert "35-set-puid-pgid.sh: error" in result.stderr
