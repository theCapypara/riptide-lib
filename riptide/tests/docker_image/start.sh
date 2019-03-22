#!/bin/sh
# User / group checks
id -u > /default_workdir/rootcheck
# Hostname Tests
cp /etc/hostname /default_workdir/hostname
# Logging Tests
>&2 echo "1, 2, 3 error"
echo "1, 2, 3 test" | tee /default_workdir/logging_test
# Start
http-server --port 8080
