#!/bin/sh

# User correction - copied from Riptide Docker entrypoint :)

# ADD GROUP
groupmod -g $DOCKER_GROUP docker
GROUP_NAME=docker

# ADD USER
if ! getent passwd $USER > /dev/null; then
    USERNAME="riptide"
    mkdir /home/riptide -p > /dev/null 2>&1
    chown $USER /home/riptide -R > /dev/null 2>&1
    useradd -ms /bin/sh --home-dir /home/riptide -u $USER -g $DOCKER_GROUP riptide 2> /dev/null
else
    # User already exists
    USERNAME=$(getent passwd "$USER" | cut -d: -f1)
    HOME_DIR=$(eval echo "~$USERNAME")
    usermod -a -G $DOCKER_GROUP $USERNAME
    # Symlink the other user directory to /home/riptide
    mkdir -p /home
    ln -s $HOME_DIR /home/riptide
    chown $USER /home/riptide -R > /dev/null 2>&1
fi
export HOME=/home/riptide
su $USERNAME -m -c "$@"