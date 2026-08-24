# baikal-docker

Docker image for [Baikal](https://sabre.io/baikal/) (CalDAV/CardDAV server), built on `nginx` + `php-fpm`.

Automatically rebuilt and published to Docker Hub whenever a new upstream Baikal version is released.

[![Docker Pulls](https://img.shields.io/docker/pulls/guillaumelepape/baikal)](https://hub.docker.com/r/guillaumelepape/baikal)
[![Docker Image Size](https://img.shields.io/docker/image-size/guillaumelepape/baikal/latest)](https://hub.docker.com/r/guillaumelepape/baikal)
[![Docker Image Version](https://img.shields.io/docker/v/guillaumelepape/baikal?sort=semver)](https://hub.docker.com/r/guillaumelepape/baikal)
[![Latest Image Published](https://img.shields.io/docker/last-updated/guillaumelepape/baikal)](https://hub.docker.com/r/guillaumelepape/baikal/tags)

Available on Docker Hub: [guillaumelepape/baikal](https://hub.docker.com/r/guillaumelepape/baikal)

Source on GitHub: [guillaumeLepape/baikal-docker](https://github.com/guillaumeLepape/baikal-docker)

## Volumes

| Container path                | Purpose                                                              | Required |
| ------------------------------ | --------------------------------------------------------------------- | -------- |
| `/var/www/baikal/config`       | Baikal configuration (generated on first run via the web setup UI)    | Yes      |
| `/var/www/baikal/Specific`     | Baikal data: users, addressbooks, calendars, SQLite DB (if used)      | Yes      |
| `/etc/msmtprc`                 | msmtp config, used as the `sendmail` backend for PHP's `mail()` calls | No       |

### `/etc/msmtprc`

Bind-mount a file here to let Baikal send email (e.g. password-reset links) through an external SMTP relay. If the file isn't mounted, PHP's `mail()` calls will silently fail (`sendmail` is symlinked to `msmtp`, which requires this config to know where to relay).

Set this file's permissions on the host (e.g. `chmod 600`) before mounting it — the container does not modify them.

Example `msmtprc`:

```
defaults
auth           on
tls            on
tls_trust_file /etc/ssl/certs/ca-certificates.crt

account        default
host           smtp.example.com
port           587
from           baikal@example.com
user           baikal@example.com
password       your-smtp-password
```

Keep this file's host-side permissions restrictive (e.g. `chmod 600`) since it contains SMTP credentials.

## docker-compose example

```yaml
services:
  baikal:
    image: docker.io/guillaumelepape/baikal:latest
    container_name: baikal
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./data/config:/var/www/baikal/config
      - ./data/specific:/var/www/baikal/Specific
      - ./msmtprc:/etc/msmtprc:ro
```

On first run, visit `http://localhost:8080/admin/` to complete the Baikal setup wizard.

## Tags & releases

Images are tagged `<baikal-version>.<build-number>`, e.g. `0.12.1.0` — the first three parts match the upstream [Baikal release](https://github.com/sabre-io/Baikal/releases). `latest` always points at the most recent tag.

[versions.env](versions.env) is the single source of truth for these values. Editing and merging it to `main` triggers a release: [.github/workflows/release.yml](.github/workflows/release.yml) tags the commit `BAIKAL_VERSION.BUILD_VERSION`, builds and pushes a multi-arch (amd64/arm64) image to Docker Hub, updates the Docker Hub description, and creates a GitHub Release.

## Dependencies

Upstream Baikal releases and GitHub Actions versions are kept current via [Renovate](https://docs.renovatebot.com/), which bumps `BAIKAL_VERSION` in [versions.env](versions.env) directly.
