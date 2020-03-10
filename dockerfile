FROM python:3.7

WORKDIR /usr/src/myapp

COPY requirements.txt ./

RUN pip install virtualenv \
    && virtualenv venv \
    && venv/bin/pip install -i https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir -r requirements.txt
COPY . .

FROM python:3.7-slim

LABEL maintainer="jyxnt1@gmail.com"


ENV TTL 10
ENV PUSHGATEWAY_URL http://test
ENV PUSH_WEBHOOK_URL http://test

WORKDIR /usr/src/myapp

COPY --from=0 /usr/src/myapp .
CMD ["venv/bin/python","run.py"]
