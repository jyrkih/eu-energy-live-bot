FROM python:3.10
RUN apt-get update
RUN apt-get -y install cron

COPY crontab /etc/cron.d/bot-crontab
RUN chmod 0744 /etc/cron.d/bot-crontab && crontab /etc/cron.d/bot-crontab

COPY config.py /app/
COPY eu-electricity-tomorrow.py /app/
COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt
COPY docker-entrypoint.sh /app/entrypoint.sh
WORKDIR /app
CMD ["./entrypoint.sh"]