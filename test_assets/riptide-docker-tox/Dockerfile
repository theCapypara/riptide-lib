# BASED ON https://github.com/level12/python-test-multi/blob/master/Dockerfile
# - This Dockerfile also adds a Docke Client, tox and a custom entrypoint
# To be tagged as: riptide_docker_tox

FROM ubuntu:16.04
MAINTAINER devteam@level12.io

RUN apt-get clean && apt-get update && apt-get install -y locales && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# map to the source code of the app
VOLUME /src

RUN echo "deb http://ppa.launchpad.net/deadsnakes/ppa/ubuntu xenial main" >> /etc/apt/sources.list.d/python.list \
    && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776 \
    && apt-get update -q \
    && apt-get install -y curl git mercurial \
        python3.5 python3.5-dev libpython3.5-dev \
        python3.6 python3.6-dev libpython3.6-dev \
        python3.7 python3.7-dev libpython3.7-dev \
    && curl -fSL "https://bootstrap.pypa.io/get-pip.py" -o get-pip.py \
    && python3.5 get-pip.py \
    && python3.6 get-pip.py \
    && python3.7 get-pip.py \
    && rm get-pip.py \
    && rm -rf /var/lib/apt/lists/*

# need these libraries for lxml, PyQuery, and dbus for Keyring
# sasl, ldap, ssl for LDAP
# freetds for pymssql
RUN apt-get update -q && apt-get install -y \
    libfreetype6 \
    libjpeg-turbo8 \
    libpq5 \
    libxml2 \
    libxslt1.1 \
    libffi6 \
    libcairo2 \
    libpango1.0 \
    libtiff5 \
    libgdk-pixbuf2.0-0 \
    libdbus-glib-1-dev \
    libsasl2-dev \
    python-dev \
    libldap2-dev \
    libssl-dev \
    freetds-dev \
    && rm -rf /var/lib/apt/lists/*

# install postgres client for migration testing
RUN apt-get update && apt-get install -y wget \
    && echo "deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main" >> /etc/apt/sources.list.d/pgdg.list \
    && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    && apt-get update \
    && apt-get install -y postgresql-client-9.6 \
    && rm -rf /var/lib/apt/lists/*

# install additional packages for build setup and troubleshooting
RUN apt-get update && apt-get install -y \
    iputils-ping \
    netcat \
    fio \
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
