# Tag this as riptide_integration_test
# Simple flexible docker http server image for basic intergation tests

FROM node:12
RUN yarn global add http-server
RUN mkdir -p /default_workdir && \
    echo "hello riptide" > /default_workdir/index.html && \
    chmod 777 /default_workdir -R
# A random folder with some files in it for tests
RUN mkdir -p /a_folder && \
    touch /a_folder/file1 && \
    touch /a_folder/file2 && \
    touch /a_folder/file3
WORKDIR /default_workdir
COPY start.sh /start.sh
RUN useradd -ms /bin/sh --home-dir /home/demo -u 12345 demo
USER 12345
# TODO Tests for engine-docker's handling of command / entrypoint
CMD ["/start.sh"]