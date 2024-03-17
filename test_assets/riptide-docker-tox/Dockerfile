# BASED ON https://github.com/level12/python-test-multi/blob/master/Dockerfile
# - This Dockerfile also adds a Docker Client, tox and a custom entrypoint
# To be tagged as: riptide_docker_tox

FROM ubuntu:20.04

RUN apt-get clean && apt-get update && apt-get install -y gnupg2 locales && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# map to the source code of the app
VOLUME /src

RUN export DEBIAN_FRONTEND=noninteractive \
    && ln -fs /usr/share/zoneinfo/Europe/Berlin /etc/localtime \
    && echo "deb http://ppa.launchpad.net/deadsnakes/ppa/ubuntu focal main" >> /etc/apt/sources.list.d/python.list \
    && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776 \
    && apt-get update -q \
    && apt-get install -y curl git mercurial \
        python3.8 python3.8-dev libpython3.8-dev libpython3.8-stdlib python3.8-distutils \
        python3.9 python3.9-dev libpython3.9-dev libpython3.9-stdlib python3.9-distutils \
        python3.10 python3.10-dev libpython3.10-dev libpython3.10-stdlib python3.10-distutils \
        python3.11 python3.11-dev libpython3.11-dev libpython3.11-stdlib python3.11-distutils \
        python3.12 python3.12-dev libpython3.12-dev libpython3.12-stdlib python3.12-distutils \
    && curl -fSL "https://bootstrap.pypa.io/get-pip.py" -o get-pip.py \
    && python3.8 get-pip.py \
    && python3.9 get-pip.py \
    && python3.10 get-pip.py \
    && python3.11 get-pip.py \
    && python3.12 get-pip.py \
    && rm get-pip.py \
    && rm -rf /var/lib/apt/lists/*

# install tox
RUN pip install tox

# Add Docker client
RUN curl -sSL https://get.docker.com/ | sh

# additional requirements by Riptide
RUN apt-get update && apt-get install -y \
    build-essential \
    libcap-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
ADD entrypoint.sh /usr/bin/entrypoint.sh
ENTRYPOINT ["/usr/bin/entrypoint.sh"]
