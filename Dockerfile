###BASE
FROM python:3.8.2-slim-buster as base
ADD ./requirements.txt /opt/CloudProfiler/requirements.txt
WORKDIR /opt/CloudProfiler
RUN pip install -r requirements.txt
ADD . /opt/CloudProfiler

#### Debug
FROM base as debug
WORKDIR /opt/CloudProfiler
RUN pip3 install ptvsd
CMD python3 -m ptvsd --host 0.0.0.0 --port 5678 --wait --multiprocess ./update-cloud-hosts.py

###Prod
FROM base as prod
ENTRYPOINT ["python", "./service.py"]