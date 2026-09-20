#!/bin/sh

# Ensure the mounted volumes are writable by the nginx user
chown -R nginx:nginx /var/www/baikal/config /var/www/baikal/Specific
