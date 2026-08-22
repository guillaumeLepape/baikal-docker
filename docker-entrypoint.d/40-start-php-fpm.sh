#!/bin/sh
# Runs automatically via the nginx image's own /docker-entrypoint.sh before nginx starts.
set -e

echo "$0: starting php-fpm"
php-fpm83 -D
