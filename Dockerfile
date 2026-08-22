# ===========================
# 1️⃣ Build Stage
# ===========================
FROM alpine AS builder

# renovate: datasource=github-releases depName=sabre-io/Baikal
ARG BAIKAL_VERSION=0.12.1

ADD https://github.com/sabre-io/Baikal/releases/download/$BAIKAL_VERSION/baikal-$BAIKAL_VERSION.zip .
RUN apk add unzip && unzip -q baikal-$BAIKAL_VERSION.zip

# ===========================
# 2️⃣ Runtime Stage
# ===========================
FROM nginx:1.31.4-alpine3.24

# Install dependencies: PHP & SQLite3
RUN apk add --no-cache      \
    php83                  \
    php83-fpm              \
    php83-curl             \
    php83-mbstring         \
    php83-mysqli           \
    php83-pdo_mysql        \
    php83-pgsql            \
    php83-pdo_pgsql        \
    php83-sqlite3          \
    php83-pdo_sqlite       \
    php83-dom              \
    php83-xml              \
    php83-simplexml        \
    php83-xmlreader        \
    php83-xmlwriter        \
    php83-session          \
    sqlite                 \
    msmtp                  \
    ca-certificates        &&\
  ln -sf /usr/bin/msmtp /usr/sbin/sendmail &&\
  sed -i \
    -e 's/^user = .*/user = nginx/' \
    -e 's/^group = .*/group = nginx/' \
    -e 's/^listen = .*/listen = \/var\/run\/php-fpm.sock/' \
    -e 's/^;\?listen\.owner = .*/listen.owner = nginx/' \
    -e 's/^;\?listen\.group = .*/listen.group = nginx/' \
    -e 's/^;\?listen\.mode = .*/listen.mode = 0660/' \
    /etc/php83/php-fpm.d/www.conf

COPY --from=builder --chown=nginx:nginx baikal /var/www/baikal
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --chmod=755 docker-entrypoint.d/ /docker-entrypoint.d/

VOLUME /var/www/baikal/config
VOLUME /var/www/baikal/Specific
