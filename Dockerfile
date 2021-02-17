###BASE
FROM python:3.9.1-alpine3.13 AS base
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /home/appuser/
WORKDIR /home/appuser/
RUN apk update && apk add --no-cache \
    docker-cli \
    gcc \
    libc-dev

RUN /usr/local/bin/python3 -m pip install --no-cache-dir --upgrade pip
COPY ./requirements.txt /home/appuser/requirements.txt
RUN pip3 install -r requirements.txt --no-cache-dir --prefer-binary
COPY . /home/appuser/
RUN addgroup -S appuser && adduser -S appuser -G appuser && \
    chown -R appuser:appuser /home/appuser/

FROM base as hardened

RUN apk del \
    gcc \
    libc-dev

#### Debug
FROM base AS debug
RUN pip3 install ptvsd==4.3.2 --no-cache-dir 
CMD ["python3", "-m", "ptvsd", "--host", "0.0.0.0", "--port", "5678", "--wait", "--multiprocess", "./update-cloud-hosts.py"]

###Prod
FROM hardened AS prod
RUN apk -U upgrade && rm -f /var/cache/apk/*
RUN echo "" > /bin/sh
USER appuser
ENTRYPOINT ["python3", "./service.py"]