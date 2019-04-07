#!/usr/bin/bash
#
## RUN TESTS (Linux only)
#
# This will run all tests in this project, including the engine integration tests with the Docker engine backend.
# The tests are run on Python versions 3.5 - 3.7.
# See tox.ini for details :)
#
# For these tests to run, you need to have Docker installed. The tests will use a Docker image found in
#   test_assets/riptide-docker-tox
# to run the tests. The tests will be given access to your Docker daemon.
#
# FOR MAC AND WINDOWS TESTS:
#   Run the commands in the tox.ini on their own (after installing everything).
#   Testing multiple Python versions not supported on these platforms.
#
# If you have problems, try to delete the .tox directory.
#

# 0. Build the integration test image...
docker build -t riptide_integration_test riptide/tests/docker_image

# 1. Build the runner image...
docker build -t riptide_docker_tox test_assets/riptide-docker-tox

# 2. Run the image...
docker run \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e USER=$(id -u) \
    -e DOCKER_GROUP=$(cut -d: -f3 < <(getent group docker)) \
    -v $SSH_AUTH_SOCK:/ssh-agent -e SSH_AUTH_SOCK=/ssh-agent \
    -v $HOME/.ssh:/home/riptide/.ssh:ro \
    -v "/tmp:/tmp" \
    -v "$(pwd):$(pwd)" \
    --network host \
    --workdir $(pwd) \
    riptide_docker_tox \
    "tox"