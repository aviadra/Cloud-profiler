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
COPY ./requirements.txt /home/appuser/requirements.txt
RUN pip3 install -r requirements.txt
COPY . /home/appuser/
RUN useradd appuser && chown -R appuser:appuser /home/appuser/

RUN apt update \
    && apt install python3-minimal -y  --no-install-recommends \
    && apt full-upgrade -y \
    && rm -rf /var/lib/apt/lists/*

RUN apt purge -y --allow-remove-essential \
    python3-pip \
    containerd \
    bash \
    && apt autoremove -y

RUN dpkg -r --force-remove-essential --force-depends \
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
    tar || true

RUN find  /bin/ -name  sh -delete

#### Debug
FROM base AS debug
RUN pip3 install ptvsd==4.3.2
CMD ["python3", "-m", "ptvsd", "--host", "0.0.0.0", "--port", "5678", "--wait", "--multiprocess", "./update-cloud-hosts.py"]

###Prod
FROM base AS prod
USER appuser
ENTRYPOINT ["python3", "./service.py"]