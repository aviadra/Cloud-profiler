###BASE
FROM ubuntu:20.04 AS base
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /home/appuser/
WORKDIR /home/appuser/
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io \
    python3-pip \
        && rm -rf /var/lib/apt/lists/*
RUN /usr/bin/python3 -m pip install --upgrade pip
COPY ./requirements.txt /home/appuser/requirements.txt
RUN pip3 install -r requirements.txt
COPY . /home/appuser/
RUN useradd appuser && chown -R appuser:appuser /home/appuser/

FROM base as hardened

RUN apt update \
    && apt install \
      python3-minimal \
      python3-distutils \
      -y  --no-install-recommends \
    && apt full-upgrade -y \
    && rm -rf /var/lib/apt/lists/*

RUN apt purge -y --allow-remove-essential \
    python3-pip \
    bash \
    && apt autoremove -y

RUN dpkg -P --force-remove-essential --force-depends \
    libgcrypt20 \
    libsystemd0 \
    pcre3 \
    shadow \
    coreutils \
    glibc \
    gnupg2 \
    libtasn1 \
    libsqlite3-0 \
    dash \
    containerd \
    libtasn1-6 \
    libpcre2-8-0 \
    libpcre3 \
    tar || true

#### Debug
FROM base AS debug
RUN pip3 install ptvsd==4.3.2
CMD ["python3", "-m", "ptvsd", "--host", "0.0.0.0", "--port", "5678", "--wait", "--multiprocess", "./update-cloud-hosts.py"]

###Prod
FROM hardened AS prod
RUN echo "" > /bin/sh
USER appuser
ENTRYPOINT ["python3", "./service.py"]