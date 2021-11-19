###BASE
FROM python:3.11.0a2-bullseye AS base
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

#Compile PyCryptodome wheel
FROM base AS wheeler
RUN apt update && apt install -y build-essential
RUN pip3 wheel PyCryptodome pyVmomi

FROM base AS main
RUN mkdir -p /home/appuser/
WORKDIR /home/appuser/
RUN apt update && apt install -y \
    docker.io
RUN /usr/local/bin/python3 -m pip install --no-cache-dir --upgrade pip
COPY ./requirements.txt /home/appuser/requirements.txt
RUN pip3 install -r requirements.txt --no-cache-dir --prefer-binary
COPY --from=wheeler /*.whl .
RUN pip3 install *.whl && rm -f *.whl
COPY ./iTerm2-static-profiles/ /home/appuser/iTerm2-static-profiles/
# COPY ChangeLog.md /home/appuser/
COPY ./config.yaml /home/appuser/
COPY ./service.py /home/appuser/
COPY ./update-cloud-hosts.py /home/appuser/
RUN adduser --system appuser && \
    chown -R appuser /home/appuser/
RUN chmod -R o+wr /home/appuser/

###Prod
FROM main AS prod
RUN apt update && apt full-upgrade -y && rm -rf /var/lib/apt/lists/*
USER appuser
ENTRYPOINT ["python3", "./service.py"]