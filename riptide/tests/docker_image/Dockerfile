# Tag this as riptide_integration_test
# Simple flexible docker http server image for basic intergation tests

FROM node:10
RUN yarn global add http-server
RUN mkdir -p /default_workdir && \
    echo "hello riptide" > /default_workdir/index.html && \
    chmod 777 /default_workdir -R
WORKDIR /default_workdir
# TODO Tests for engine-docker's handling of command / entrypoint
CMD ["http-server", "--port", "8080"]