#!/usr/bin/env bash

set -e

BUILD_VERSION=0

BAIKAL_VERSION=$(grep -m1 '^ARG BAIKAL_VERSION=' Dockerfile | cut -d= -f2)

docker buildx build --build-arg BAIKAL_VERSION=$BAIKAL_VERSION -t guillaumelepape/baikal:${BAIKAL_VERSION}.${BUILD_VERSION} -t guillaumelepape/baikal:latest .
