FROM python:3.8.1
ADD . /opt/CloudProfiler
WORKDIR /opt/CloudProfiler
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "./update-cloud-hosts.py"]