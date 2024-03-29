###BASE
FROM python:3.10-alpine3.16 AS base
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

#Compile PyCryptodome wheel
FROM base AS wheeler
RUN apk -U add --no-cache \
    gcc \
    libc-dev
RUN pip3 wheel PyCryptodome pyVmomi

FROM base AS main
RUN mkdir -p /home/appuser/
WORKDIR /home/appuser/
RUN apk -U add --no-cache \
    docker-cli
RUN /usr/local/bin/python3 -m pip install --no-cache-dir --upgrade pip
COPY ./requirements.txt /home/appuser/requirements.txt
RUN pip3 install -r requirements.txt --no-cache-dir --prefer-binary && rm requirements.txt
COPY --from=wheeler /*.whl .
RUN pip3 install *.whl && rm -f *.whl
COPY ./iTerm2-static-profiles/ /home/appuser/iTerm2-static-profiles/
COPY ./config.yaml /home/appuser/
COPY ./service.py /home/appuser/
COPY ./update-cloud-hosts.py /home/appuser/
RUN addgroup -S appuser && adduser -S appuser -G appuser && \
    chown -R appuser:appuser /home/appuser/
RUN chmod -R o+wr /home/appuser/

###Prod
FROM main AS prod
RUN apk -U upgrade && rm -f /var/cache/apk/*
USER appuser
ENTRYPOINT ["python3", "-OO", "./service.py"]