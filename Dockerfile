FROM python:3.8
RUN apt-get update

RUN apt-get -y install cron python3-gdal gdal-bin libgdal-dev

COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt

COPY crontab /etc/cron.d/bot-crontab
RUN chmod 0744 /etc/cron.d/bot-crontab && crontab /etc/cron.d/bot-crontab

COPY config.py /app/
COPY eu-electricity-tomorrow.py /app/
COPY run.sh /app/
RUN chmod 755 /app/run.sh
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
WORKDIR /app
CMD ["./docker-entrypoint.sh"]
