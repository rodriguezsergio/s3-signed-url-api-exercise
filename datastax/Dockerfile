FROM python:3.7

RUN pip install \
        boto3 \
        sanic \
        aioredis && \
    mkdir -p /opt/datastax_app/logs

COPY datastax.py /opt/datastax_app/
COPY datastax.conf /etc/logrotate.d/

WORKDIR /opt/datastax_app
CMD ["/usr/local/bin/python", "/opt/datastax_app/datastax.py"]