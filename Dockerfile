FROM python:3.8.1-slim-buster
ADD ./requirements.txt /opt/CloudProfiler/requirements.txt
WORKDIR /opt/CloudProfiler
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "./service.py"]
ADD . /opt/CloudProfiler