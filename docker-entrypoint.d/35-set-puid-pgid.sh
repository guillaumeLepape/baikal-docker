#!/bin/sh

# Lets the nginx and php-fpm user match the owner of the mounted volumes, both
# processes resolve the "nginx" user/group by name when they start.

set -e
ME=$(basename $0)

for name in PUID PGID
do
  eval "value=\${$name:-}"
  case "$value" in
    *[!0-9]*)
      echo "$ME: error: $name must be a number, got '$value'" >&2
      exit 1
      ;;
    0)
      echo "$ME: error: $name must not be 0, php-fpm refuses to run as root" >&2
      exit 1
      ;;
  esac
done

uid=${PUID:-$(id -u nginx)}
gid=${PGID:-$(id -g nginx)}

if [ -n "${PGID:-}" ]
then
  echo "$ME: info: Setting nginx group ID to $PGID"
  sed -i "s/^nginx:x:[0-9]*:/nginx:x:$PGID:/" /etc/group
fi

if [ -n "${PUID:-}" ] || [ -n "${PGID:-}" ]
then
  [ -z "${PUID:-}" ] || echo "$ME: info: Setting nginx user ID to $PUID"
  # nginx workers take their group from the passwd entry, not from /etc/group
  sed -i "s/^nginx:x:[0-9]*:[0-9]*:/nginx:x:$uid:$gid:/" /etc/passwd
fi
