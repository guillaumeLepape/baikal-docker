#!/usr/bin/env bash

set -e

BAIKAL_VERSION=0.12.1
BUILD_VERSION=0

docker buildx build --build-arg BAIKAL_VERSION=$BAIKAL_VERSION -t guillaumelepape/baikal:${BAIKAL_VERSION}.${BUILD_VERSION} -t guillaumelepape/baikal:latest .
