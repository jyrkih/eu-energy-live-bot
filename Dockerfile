FROM python:3.10

COPY config.py /app/
COPY eu-electricity-tomorrow.py /app/
COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /app
CMD ["python3", "eu-electricity-tomorrow.py"]