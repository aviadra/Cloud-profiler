###BASE
FROM python:3.8.3-slim-buster AS base
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /home/appuser/
WORKDIR /home/appuser/
COPY ./requirements.txt /home/appuser/requirements.txt
RUN pip3 install -r requirements.txt
COPY . /home/appuser/
RUN useradd appuser && chown -R appuser /home/appuser/

USER appuser

#### Debug
FROM base AS debug
RUN pip3 install ptvsd==4.3.2
CMD ["python3", "-m", "ptvsd", "--host", "0.0.0.0", "--port", "5678", "--wait", "--multiprocess", "./update-cloud-hosts.py"]

###Prod
FROM base AS prod
ENTRYPOINT ["python", "./service.py"]