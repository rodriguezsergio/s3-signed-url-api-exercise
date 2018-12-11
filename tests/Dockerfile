FROM python:3.7

RUN pip install \
        requests \
        redis

COPY test.py /opt/datastax_tests/

WORKDIR /opt/datastax_tests
CMD ["/usr/local/bin/python", "/opt/datastax_tests/test.py"]