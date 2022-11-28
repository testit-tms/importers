FROM python:3.11.0-alpine

WORKDIR /app
COPY . .

RUN \
    apk update && \
    apk add py3-pip && \
    pip install . && \
    rm -rf rm -rf /var/cache/apk/*

ENTRYPOINT testit-consumer
