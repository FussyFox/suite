#!/usr/bin/env sh

set -ex

docker pull lambdalint/lambda-function-builder
docker run -ti -v "$(pwd):/var/task" lambdalint/lambda-function-builder pip-3.6 install -r requirements.txt -t .
